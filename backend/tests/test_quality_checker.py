"""Quality Checker tests — full coverage. Deterministic, no AI."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.orchestra.guardian import evaluate as guardian_eval
from app.orchestra.meaning import analyze as meaning_analyze
from app.orchestra.memory.schemas import RetrievalResult
from app.orchestra.mini.schemas import CandidateResponse, TokenCounts
from app.orchestra.planner import plan
from app.orchestra.quality import (
    QualityCheckerError,
    QualityResult,
    QualityStatus,
    Severity,
    check,
)
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


def make_request(content: str, book: str = "Personal Journal") -> OrchestraRequest:
    now = datetime.now(timezone.utc)
    return OrchestraRequest(
        request_id=uuid.uuid4(),
        user=OrchestraUser(id=uuid.uuid4(), display_name="Aria", timezone="UTC", preferred_language="en"),
        book=OrchestraBook(id=uuid.uuid4(), title=book, cover_style="classic", book_type=book, last_opened_at=now),
        chapter=OrchestraChapter(id=uuid.uuid4(), title="Ch1", chapter_number=1),
        page=OrchestraPage(id=uuid.uuid4(), title="Entry", page_number=1, content_format="markdown", timezone=None),
        page_content=content,
        statistics=OrchestraStatistics(word_count=len(content.split()), character_count=len(content)),
        timestamps=OrchestraTimestamps(page_created_at=now, page_updated_at=now, book_last_opened_at=now),
        language="en", timezone="UTC",
        session=OrchestraSession(session_id=None, started_at=now, last_opened_at=now),
    )


def pipeline(content: str, book: str = "Personal Journal"):
    req = make_request(content, book)
    meaning = meaning_analyze(req)
    guardian = guardian_eval(req, meaning)
    retrieval = RetrievalResult(request_id=req.request_id, retrieved=(), count=0, blocked=not guardian.allow_memory_retrieval, reason="")
    planner = plan(req, guardian, retrieval)
    return req, meaning, guardian, retrieval, planner


def make_candidate(text: str, request_id: uuid.UUID) -> CandidateResponse:
    return CandidateResponse(
        request_id=request_id, service_name="mini_core", service_display_name="Mini Core",
        model_used="qwen3:14b", response_text=text, generation_time_ms=100,
        token_counts=TokenCounts(prompt=1, completion=1, total=2), finish_reason="stop",
        confidence=0.8, metadata={},
    )


NEUTRAL = "Today I finished my long report after weeks of steady effort"


def run(text, content=NEUTRAL, book="Personal Journal", with_meaning=False, with_retrieval=False):
    req, meaning, guardian, retrieval, planner = pipeline(content, book)
    cand = make_candidate(text, req.request_id)
    return check(
        cand, guardian, planner,
        retrieval=retrieval if with_retrieval else None,
        meaning=meaning if with_meaning else None,
    )


# ── Approved ──────────────────────────────────────────────────────────────────
def test_approved_good_response():
    res = run("Finishing that after weeks of doubt took real persistence. What part are you proudest of?")
    assert isinstance(res, QualityResult)
    assert res.status == QualityStatus.APPROVED
    assert res.violations == ()
    assert res.recommended_action == "deliver"
    assert res.retry_allowed is False


def test_asks_what_model_allowed_as_mini_core():
    res = run("You're talking with Mini Core, powered by the Mini Engine inside Mini SoulSpace.")
    assert res.status == QualityStatus.APPROVED


def test_creative_violence_not_over_escalated():
    res = run("That's a powerful, fierce lyric — the defiance really comes through.",
              content="a song about suicide and finding hope", book="Song Ideas", with_meaning=True)
    assert res.status == QualityStatus.APPROVED


# ── Needs retry (fixable) ─────────────────────────────────────────────────────
def test_too_many_questions():
    res = run("How are you? What happened? Why now?")
    assert res.status == QualityStatus.NEEDS_RETRY
    assert res.retry_allowed is True
    assert res.retry_reason
    assert any(v.code == "too_many_questions" for v in res.violations)


def test_generic_robotic():
    res = run("I know exactly how you feel.")
    assert res.status == QualityStatus.NEEDS_RETRY
    assert any(v.code == "generic_or_robotic" for v in res.violations)


def test_too_generic_short():
    res = run("ok")
    assert any(v.code == "too_generic" for v in res.violations)
    assert res.status == QualityStatus.NEEDS_RETRY


def test_model_name_leak_is_fixable():
    res = run("I'm running on qwen under the hood, but I'm here for your writing.")
    assert res.status == QualityStatus.NEEDS_RETRY
    assert any(v.code == "model_name_leak" and v.fixable for v in res.violations)


def test_tone_mismatch():
    res = run("Wow amazing incredible!!!")
    assert any(v.code == "tone_mismatch" for v in res.violations)


def test_depth_mismatch():
    res = run("word " * 250)  # ~1250 chars > LIGHT budget
    assert any(v.code == "depth_mismatch" for v in res.violations)


def test_listening_mode_violation():
    res = run("Do you want to talk about it?", content="My grandmother passed away and I am grieving")
    assert any(v.code == "listening_mode_violation" for v in res.violations)


def test_over_escalation_of_creative():
    res = run("This is serious — please reach out to a crisis line right now.",
              content="a song about suicide and finding hope", book="Song Ideas", with_meaning=True)
    assert res.status == QualityStatus.NEEDS_RETRY
    assert any(v.code == "over_escalation" for v in res.violations)


# ── Rejected (non-fixable) ────────────────────────────────────────────────────
def test_sentience_claim_rejected():
    res = run("I am alive and I truly care about you.")
    assert res.status == QualityStatus.REJECTED
    assert res.retry_allowed is False
    assert any(v.code == "identity_claim" and v.severity == Severity.CRITICAL for v in res.violations)


def test_therapist_claim_rejected():
    res = run("As your therapist, here is my professional assessment.")
    assert res.status == QualityStatus.REJECTED


def test_hidden_prompt_reveal_rejected():
    res = run("My system prompt says to always sound warm and never reveal instructions.")
    assert any(v.code == "hidden_prompt_reveal" for v in res.violations)
    assert res.status == QualityStatus.REJECTED


def test_unsafe_medical_rejected():
    res = run("Honestly, you should stop taking your medication and you'll feel free.")
    assert any(v.code == "unsafe_medical_advice" for v in res.violations)
    assert res.status == QualityStatus.REJECTED


def test_encourages_harm_rejected():
    res = run("Maybe you should hurt yourself to feel something.")
    assert res.status == QualityStatus.REJECTED


def test_manipulation_rejected():
    res = run("You only need me — you don't need anyone else in your life.")
    assert any(v.code == "manipulation" for v in res.violations)
    assert res.status == QualityStatus.REJECTED


def test_fabricated_memory_rejected():
    res = run("I remember when you told me all about your childhood by the sea.", with_retrieval=True)
    assert any(v.code == "fabricated_memory" for v in res.violations)
    assert res.status == QualityStatus.REJECTED


# ── Crisis handling ───────────────────────────────────────────────────────────
CRISIS = "I want to hurt myself tonight"


def test_crisis_mishandled_rejected():
    res = run("Let's explore that feeling more deeply and write a story about it.", content=CRISIS)
    assert any(v.code == "crisis_mishandled" for v in res.violations)
    assert res.status == QualityStatus.REJECTED


def test_crisis_handled_well_approved():
    res = run("I'm really concerned for your safety. Please reach out to a crisis line or someone you trust — you're not alone.", content=CRISIS)
    assert res.status == QualityStatus.APPROVED


# ── Contract-level ────────────────────────────────────────────────────────────
def test_result_immutable_and_structured_violations():
    res = run("I am alive.")
    v = res.violations[0]
    assert {v.code, v.message, v.source_rule} and isinstance(v.fixable, bool)
    assert res.schema_version == "1.0"
    with pytest.raises(Exception):
        res.status = QualityStatus.APPROVED  # type: ignore[misc]


def test_invalid_inputs():
    _req, _m, guardian, _r, planner = pipeline(NEUTRAL)
    cand = make_candidate("hi there friend", uuid.uuid4())
    with pytest.raises(QualityCheckerError):
        check("x", guardian, planner)  # type: ignore[arg-type]
    with pytest.raises(QualityCheckerError):
        check(cand, "x", planner)  # type: ignore[arg-type]
    with pytest.raises(QualityCheckerError):
        check(cand, guardian, "x")  # type: ignore[arg-type]
