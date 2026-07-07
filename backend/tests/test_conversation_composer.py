"""Conversation Composer tests — full coverage. Assemble only, no AI."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.orchestra.composer import (
    FRONTEND_EVENT_NAMES,
    MEMORY_NOTIFICATION_TEMPLATES,
    ComposerError,
    ConversationPackage,
    DeliveryStatus,
    compose,
)
from app.orchestra.intelligence.schemas import (
    MemoryIntelligenceResult,
    MemorySource,
    NextAction,
    VerificationStatus,
)
from app.orchestra.memory.schemas import MemoryPriority, MemoryType
from app.orchestra.mini.schemas import CandidateResponse, TokenCounts
from app.orchestra.quality.schemas import QualityResult, QualityStatus, Severity, Violation
from app.orchestra.schemas import (
    OrchestraBook,
    OrchestraChapter,
    OrchestraPage,
    OrchestraRequest,
    OrchestraSession,
    OrchestraStatistics,
    OrchestraTimestamps,
    OrchestraUser,
)
from app.orchestra.writer.schemas import MemoryDecision


def make_request() -> OrchestraRequest:
    now = datetime.now(timezone.utc)
    return OrchestraRequest(
        request_id=uuid.uuid4(),
        user=OrchestraUser(id=uuid.uuid4(), display_name="Aria", timezone="UTC", preferred_language="en"),
        book=OrchestraBook(id=uuid.uuid4(), title="Journal", cover_style="classic", book_type="classic", last_opened_at=now),
        chapter=OrchestraChapter(id=uuid.uuid4(), title="Ch1", chapter_number=1),
        page=OrchestraPage(id=uuid.uuid4(), title="Day", page_number=1, content_format="markdown", timezone=None),
        page_content="Today was steady",
        statistics=OrchestraStatistics(word_count=3, character_count=16),
        timestamps=OrchestraTimestamps(page_created_at=now, page_updated_at=now, book_last_opened_at=now),
        language="en", timezone="UTC",
        session=OrchestraSession(session_id=None, started_at=now, last_opened_at=now),
    )


def make_candidate(request_id, text="A calm, thoughtful reflection.") -> CandidateResponse:
    return CandidateResponse(
        request_id=request_id, service_name="mini_core", service_display_name="Mini Core",
        model_used="qwen3:14b", response_text=text, generation_time_ms=120,
        token_counts=TokenCounts(prompt=5, completion=9, total=14), finish_reason="stop",
        confidence=0.85, metadata={},
    )


def make_quality(request_id, status=QualityStatus.APPROVED, violations=()):
    return QualityResult(
        request_id=request_id, status=status, confidence=0.9, reason="",
        violations=tuple(violations), recommended_action="deliver",
        retry_allowed=status == QualityStatus.NEEDS_RETRY,
    )


def make_decision(request_id, op="create"):
    return MemoryDecision(
        request_id=request_id, store_memory=True, importance=MemoryPriority.HIGH,
        memory_type=MemoryType.GOAL, title="Goal: marathon", summary="My goal is a marathon",
        reason="new_memory", confidence=0.8, metadata={"op": op},
    )


def make_intelligence(memory_id=None):
    return MemoryIntelligenceResult(
        memory_id=memory_id or uuid.uuid4(), confidence=0.99, confidence_reason="explicit",
        memory_source=MemorySource.SOULDIARY, evidence={"page_id": "p"},
        verification_status=VerificationStatus.UNVERIFIED, next_action=NextAction.NONE,
    )


# ── Approved delivery ─────────────────────────────────────────────────────────
def test_approved_delivers_text_exactly():
    req = make_request()
    text = "Exactly as approved — word for word."
    pkg = compose(req, make_quality(req.request_id), make_candidate(req.request_id, text))
    assert isinstance(pkg, ConversationPackage)
    assert pkg.status == DeliveryStatus.DELIVERED
    assert pkg.text == text  # never rewritten
    assert pkg.request_id == req.request_id
    assert pkg.frontend_events[0].name == "ConversationDelivered"
    assert pkg.metadata["service"] == "mini_core"


def test_placeholders_empty_by_default():
    req = make_request()
    pkg = compose(req, make_quality(req.request_id), make_candidate(req.request_id))
    assert pkg.attachments == ()
    assert pkg.actions == ()
    assert pkg.notifications == ()
    assert pkg.citations == ()
    assert pkg.sources == ()
    assert pkg.memory_updates == ()


def test_memory_create_packaged_with_event():
    req = make_request()
    pkg = compose(
        req, make_quality(req.request_id), make_candidate(req.request_id),
        memory_decision=make_decision(req.request_id, op="create"),
        memory_intelligence=make_intelligence(),
    )
    assert len(pkg.memory_updates) == 1
    mu = pkg.memory_updates[0]
    assert mu.op == "create" and mu.memory_type == "goal" and mu.importance == "high"
    assert mu.confidence == 0.99 and mu.verification_status == "unverified"
    names = [e.name for e in pkg.frontend_events]
    assert names == ["ConversationDelivered", "MemoryStored"]


def test_memory_update_event_without_intelligence():
    req = make_request()
    pkg = compose(
        req, make_quality(req.request_id), make_candidate(req.request_id),
        memory_decision=make_decision(req.request_id, op="update"),
    )
    assert pkg.memory_updates[0].op == "update"
    assert pkg.memory_updates[0].confidence == 0.8  # falls back to decision confidence
    assert pkg.memory_updates[0].verification_status is None
    assert [e.name for e in pkg.frontend_events] == ["ConversationDelivered", "MemoryUpdated"]


def test_no_store_decision_packages_nothing():
    req = make_request()
    decision = MemoryDecision(request_id=req.request_id, store_memory=False, reason="nothing_worth_remembering", confidence=0.6)
    pkg = compose(req, make_quality(req.request_id), make_candidate(req.request_id), memory_decision=decision)
    assert pkg.memory_updates == ()
    assert [e.name for e in pkg.frontend_events] == ["ConversationDelivered"]


# ── Failure packages (never bypass Quality) ───────────────────────────────────
@pytest.mark.parametrize("status", [QualityStatus.REJECTED, QualityStatus.NEEDS_RETRY])
def test_not_approved_never_delivered(status):
    req = make_request()
    violations = (Violation(code="identity_claim", severity=Severity.CRITICAL, message="", source_rule="r", fixable=False),)
    pkg = compose(req, make_quality(req.request_id, status, violations), make_candidate(req.request_id, "unsafe text"))
    assert pkg.status == DeliveryStatus.NOT_DELIVERED
    assert pkg.text == ""  # unsafe response never reaches the frontend
    assert pkg.metadata["failure_reason"] == status.value
    assert pkg.metadata["violation_codes"] == ["identity_claim"]
    assert pkg.frontend_events[0].name == "ConversationNotDelivered"


def test_failure_package_without_candidate():
    req = make_request()
    pkg = compose(req, make_quality(req.request_id, QualityStatus.REJECTED))
    assert pkg.status == DeliveryStatus.NOT_DELIVERED


# ── Contract-level ────────────────────────────────────────────────────────────
def test_package_immutable_and_versioned():
    req = make_request()
    pkg = compose(req, make_quality(req.request_id), make_candidate(req.request_id))
    assert pkg.schema_version == "1.0"
    with pytest.raises(Exception):
        pkg.text = "hacked"  # type: ignore[misc]


def test_event_names_and_notification_templates_prepared():
    assert "ConversationDelivered" in FRONTEND_EVENT_NAMES
    assert "BirthdayDetected" in FRONTEND_EVENT_NAMES
    assert MEMORY_NOTIFICATION_TEMPLATES["create"] == "I'll remember that."
    assert MEMORY_NOTIFICATION_TEMPLATES["birthday"] == "Your birthday has been saved."


# ── Failure cases (structured errors) ─────────────────────────────────────────
def test_invalid_request_raises():
    req = make_request()
    with pytest.raises(ComposerError) as e:
        compose("x", make_quality(req.request_id))  # type: ignore[arg-type]
    assert e.value.errors[0]["code"] == "invalid_input"


def test_invalid_quality_raises():
    req = make_request()
    with pytest.raises(ComposerError):
        compose(req, "x")  # type: ignore[arg-type]


def test_approved_without_candidate_raises():
    req = make_request()
    with pytest.raises(ComposerError) as e:
        compose(req, make_quality(req.request_id))
    assert e.value.errors[0]["code"] == "missing_candidate"
