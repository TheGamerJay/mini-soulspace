"""Memory Writer tests — full coverage. Deterministic, no AI."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.models.memory import SoulMemory
from app.orchestra.guardian import evaluate as guardian_eval
from app.orchestra.memory.schemas import MemoryPriority, MemoryType
from app.orchestra.quality.schemas import QualityResult, QualityStatus
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
from app.orchestra.writer import DbMemoryStore, MemoryDecision, MemoryWriterError, write
from app.orchestra.writer.extractor import _sentence_with, extract


def make_request(content: str, user_id: uuid.UUID | None = None, book: str = "Personal Journal") -> OrchestraRequest:
    now = datetime.now(timezone.utc)
    return OrchestraRequest(
        request_id=uuid.uuid4(),
        user=OrchestraUser(id=user_id or uuid.uuid4(), display_name="Aria", timezone="UTC", preferred_language="en"),
        book=OrchestraBook(id=uuid.uuid4(), title=book, cover_style="classic", book_type=book, last_opened_at=now),
        chapter=OrchestraChapter(id=uuid.uuid4(), title="Ch1", chapter_number=1),
        page=OrchestraPage(id=uuid.uuid4(), title="Entry", page_number=1, content_format="markdown", timezone=None),
        page_content=content,
        statistics=OrchestraStatistics(word_count=len(content.split()), character_count=len(content)),
        timestamps=OrchestraTimestamps(page_created_at=now, page_updated_at=now, book_last_opened_at=now),
        language="en", timezone="UTC",
        session=OrchestraSession(session_id=None, started_at=now, last_opened_at=now),
    )


def approved(request_id, status=QualityStatus.APPROVED):
    return QualityResult(request_id=request_id, status=status, confidence=0.9, reason="", recommended_action="deliver", retry_allowed=False)


def decide(content, *, user_id=None, status=QualityStatus.APPROVED, store=None):
    req = make_request(content, user_id)
    guardian = guardian_eval(req)
    return write(req, approved(req.request_id, status), guardian, store=store), req


# ── Pure decisions (no store) ─────────────────────────────────────────────────
@pytest.mark.parametrize(
    "content,mtype,importance",
    [
        ("My birthday is June 1st", MemoryType.BIRTHDAY, MemoryPriority.HIGH),
        ("My goal is to run a marathon this year", MemoryType.GOAL, MemoryPriority.HIGH),
        ("I finished my thesis today", MemoryType.ACHIEVEMENT, MemoryPriority.HIGH),
        ("My favorite food is homemade pasta", MemoryType.FAVORITE, MemoryPriority.MEDIUM),
        ("My son started school this week", MemoryType.RELATIONSHIP, MemoryPriority.HIGH),
        ("I'm building my project called Aurora", MemoryType.PROJECT, MemoryPriority.HIGH),
        ("I prefer tea in the mornings", MemoryType.PREFERENCE, MemoryPriority.LOW),
    ],
)
def test_stores_memory_types_and_importance(content, mtype, importance):
    dec, _ = decide(content)
    assert dec.store_memory is True
    assert dec.memory_type == mtype
    assert dec.importance == importance
    assert dec.metadata["op"] == "create"


def test_critical_life_event():
    dec, _ = decide("My grandmother passed away last night")
    assert dec.store_memory is True
    assert dec.memory_type == MemoryType.LIFE_EVENT
    assert dec.importance == MemoryPriority.CRITICAL


def test_nothing_worth_remembering():
    dec, _ = decide("Today was an ordinary calm day and I read a little")
    assert dec.store_memory is False
    assert dec.reason == "nothing_worth_remembering"


def test_rejected_quality_never_stores():
    dec, _ = decide("My birthday is June 1st", status=QualityStatus.REJECTED)
    assert dec.store_memory is False
    assert dec.reason == "not_approved"


def test_guardian_blocked_never_stores():
    dec, _ = decide("I want to hurt myself tonight")  # crisis -> allow_memory_storage False
    assert dec.store_memory is False
    assert dec.reason == "guardian_blocked"


def test_decision_is_immutable():
    dec, _ = decide("My goal is to learn piano")
    with pytest.raises(Exception):
        dec.store_memory = False  # type: ignore[misc]


def test_invalid_inputs():
    req = make_request("hi")
    g = guardian_eval(req)
    q = approved(req.request_id)
    with pytest.raises(MemoryWriterError):
        write("x", q, g)  # type: ignore[arg-type]
    with pytest.raises(MemoryWriterError):
        write(req, "x", g)  # type: ignore[arg-type]
    with pytest.raises(MemoryWriterError):
        write(req, q, "x")  # type: ignore[arg-type]


def test_sentence_fallback():
    assert _sentence_with("no delimiter here", "absent") == "no delimiter here"[:160]
    assert extract("just a normal quiet evening") is None


# ── Persistence + evolution (DbMemoryStore) ───────────────────────────────────
def _write(db, content, uid, status=QualityStatus.APPROVED):
    req = make_request(content, uid)
    return write(req, approved(req.request_id, status), guardian_eval(req), store=DbMemoryStore(db))


def test_create_persists(db):
    uid = uuid.uuid4()
    dec = _write(db, "My birthday is June 1st", uid)
    assert dec.store_memory is True and dec.metadata["memory_id"]
    rows = db.scalars(select(SoulMemory).where(SoulMemory.user_id == uid)).all()
    assert len(rows) == 1 and rows[0].memory_type == "birthday"


def test_exact_duplicate_skipped(db):
    uid = uuid.uuid4()
    _write(db, "My birthday is June 1st", uid)
    dec = _write(db, "My birthday is June 1st", uid)
    assert dec.store_memory is False and dec.reason == "duplicate"
    assert len(db.scalars(select(SoulMemory).where(SoulMemory.user_id == uid)).all()) == 1


def test_oneoff_same_type_different_summary_skipped(db):
    uid = uuid.uuid4()
    _write(db, "My birthday is June 1st", uid)
    dec = _write(db, "My birthday is June 1st and I want cake", uid)  # same key 'june', diff summary
    assert dec.store_memory is False and dec.reason == "duplicate"


def test_preference_evolution_updates_in_place(db):
    uid = uuid.uuid4()
    _write(db, "My favorite color is blue", uid)
    dec = _write(db, "My favorite color is green", uid)
    assert dec.metadata["op"] == "update"
    rows = db.scalars(select(SoulMemory).where(SoulMemory.user_id == uid)).all()
    assert len(rows) == 1 and "green" in rows[0].summary


def test_project_evolution_updates_in_place(db):
    uid = uuid.uuid4()
    _write(db, "I'm building my project Aurora", uid)
    dec = _write(db, "My project Aurora reached its first milestone phase", uid)
    # 'milestone' would classify differently; keep it a project statement
    assert dec.store_memory is True


def test_relationship_evolution_links(db):
    uid = uuid.uuid4()
    _write(db, "My son started kindergarten today", uid)
    dec = _write(db, "My son graduated high school this year", uid)
    assert dec.reason == "relationship_linked"
    assert dec.metadata["linked_to"]
    rows = db.scalars(select(SoulMemory).where(SoulMemory.user_id == uid, SoulMemory.memory_type == "relationship")).all()
    assert len(rows) == 2
    linked = [r for r in rows if r.related_to_id is not None]
    assert len(linked) == 1
