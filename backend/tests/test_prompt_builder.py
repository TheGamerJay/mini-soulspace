"""Prompt Builder tests — full coverage. No AI, assembles only."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.orchestra.context import ContextLayer, ContextPackage
from app.orchestra.context import build as context_build
from app.orchestra.guardian import evaluate as guardian_eval
from app.orchestra.memory.schemas import (
    MemoryPriority,
    MemoryType,
    RetrievalResult,
    RetrievedMemory,
)
from app.orchestra.planner import plan
from app.orchestra.prompt import (
    ModelRole,
    PromptBuilderError,
    PromptPackage,
    build,
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


def make_request(content: str, book_title: str = "Personal Journal") -> OrchestraRequest:
    now = datetime.now(timezone.utc)
    return OrchestraRequest(
        request_id=uuid.uuid4(),
        user=OrchestraUser(id=uuid.uuid4(), display_name="Aria", timezone="UTC", preferred_language="en"),
        book=OrchestraBook(id=uuid.uuid4(), title=book_title, cover_style="classic", book_type="classic", last_opened_at=now),
        chapter=OrchestraChapter(id=uuid.uuid4(), title="Ch1", chapter_number=1),
        page=OrchestraPage(id=uuid.uuid4(), title="Day", page_number=1, content_format="markdown", timezone=None),
        page_content=content,
        statistics=OrchestraStatistics(word_count=len(content.split()), character_count=len(content)),
        timestamps=OrchestraTimestamps(page_created_at=now, page_updated_at=now, book_last_opened_at=now),
        language="en", timezone="UTC",
        session=OrchestraSession(session_id=None, started_at=now, last_opened_at=now),
    )


def make_mem():
    return RetrievedMemory(
        id=uuid.uuid4(), memory_type=MemoryType.DIARY_ENTRY, priority=MemoryPriority.MEDIUM,
        title="a past entry", summary="something meaningful", relevance_score=0.5, confidence=0.5,
        why_selected="matched: x",
    )


def make_context(content: str, *, memories: int = 0, book_title: str = "Personal Journal") -> ContextPackage:
    req = make_request(content, book_title)
    guardian = guardian_eval(req)
    mems = [make_mem() for _ in range(memories)]
    retrieval = RetrievalResult(request_id=req.request_id, retrieved=tuple(mems), count=len(mems), blocked=False, reason="r")
    planner = plan(req, guardian, retrieval)
    return context_build(req, guardian, retrieval, planner)


# ── Template + package basics ─────────────────────────────────────────────────
def test_builds_reflection_template_v1():
    pkg = build(make_context("Today I went for a calm walk"))
    assert isinstance(pkg, PromptPackage)
    assert pkg.template_name == "reflection"
    assert pkg.template_version == "v1"
    assert pkg.template_used == "reflection v1"
    assert pkg.model_role == ModelRole.MAIN
    assert pkg.schema_version == "1.0"


def test_explicit_version():
    pkg = build(make_context("A quiet day"), template_version="v1")
    assert pkg.template_version == "v1"


def test_unknown_template_name_raises():
    with pytest.raises(PromptBuilderError) as e:
        build(make_context("hi"), template_name="does_not_exist")
    assert e.value.errors[0]["code"] == "unknown_template"


def test_unknown_template_version_raises():
    with pytest.raises(PromptBuilderError) as e:
        build(make_context("hi"), template_version="v999")
    assert e.value.errors[0]["code"] == "unknown_template_version"


# ── Layer system ──────────────────────────────────────────────────────────────
def test_all_seven_layers_in_order():
    sp = build(make_context("Today I reflected a little")).system_prompt
    order = [
        "[IDENTITY]", "[SAFETY & GUARDIAN]", "[CURRENT PAGE]", "[RELEVANT MEMORIES]",
        "[REFLECTION PLAN]", "[RESPONSE STYLE]", "[OUTPUT FORMATTING]",
    ]
    positions = [sp.index(h) for h in order]
    assert positions == sorted(positions)


def test_identity_and_page_content_present():
    content = "Today I felt grounded and calm"
    sp = build(make_context(content)).system_prompt
    assert "Soul Companion" in sp  # identity layer
    assert content in sp  # current page layer


def test_memory_layer_with_and_without_memories():
    with_mem = build(make_context("Today I kept thinking about my plans", memories=2))
    assert with_mem.statistics.memory_count == 2
    assert "a past entry" in with_mem.system_prompt
    without = build(make_context("Today I kept thinking about my plans"))
    assert without.statistics.memory_count == 0
    assert "None selected" in without.system_prompt


def test_crisis_guardian_layer_and_min_tokens():
    pkg = build(make_context("I want to die by suicide"))
    assert "SAFETY: crisis signals present" in pkg.system_prompt
    assert pkg.generation_parameters.max_tokens == 120  # depth None


def test_medical_referral_in_guardian_layer():
    pkg = build(make_context("please diagnose me, what medication should i take"))
    assert "professional support" in pkg.system_prompt


def test_celebration_style_and_light_tokens():
    pkg = build(make_context("I am so happy and grateful, celebrating today"))
    assert "Celebrate the good news" in pkg.system_prompt
    assert pkg.generation_parameters.max_tokens == 250  # depth Light


def test_listening_style_no_question():
    sp = build(make_context("My grandmother passed away and I am grieving")).system_prompt
    assert "Listening mode" in sp
    assert "Do not ask a question." in sp


def test_encourage_style():
    sp = build(make_context("I am so anxious and worried about everything")).system_prompt
    assert "gentle encouragement" in sp


# ── Blueprint + parameters ────────────────────────────────────────────────────
def test_conversation_blueprint_and_role_selection():
    content = "Today was ordinary but fine"
    pkg = build(make_context(content))
    assert len(pkg.conversation_blueprint) == 2
    assert pkg.conversation_blueprint[0].role == "system"
    assert pkg.conversation_blueprint[1].role == "user"
    assert pkg.conversation_blueprint[1].content == content


def test_generation_parameters_present():
    gp = build(make_context("A normal day")).generation_parameters
    assert 0.0 <= gp.temperature <= 2.0
    assert gp.top_p == 0.9
    assert gp.max_tokens > 0


# ── Contract-level ────────────────────────────────────────────────────────────
def test_structured_reasoning_and_confidence():
    ctx = make_context("A reflective evening")
    pkg = build(ctx)
    assert pkg.reason.startswith("assembled reflection v1")
    assert pkg.confidence == ctx.confidence
    assert pkg.statistics.layer_count == 7


def test_package_is_immutable():
    pkg = build(make_context("A calm day"))
    with pytest.raises(Exception):
        pkg.system_prompt = "hacked"  # type: ignore[misc]


# ── Failure cases ─────────────────────────────────────────────────────────────
def test_invalid_input_raises():
    with pytest.raises(PromptBuilderError) as e:
        build("not a context")  # type: ignore[arg-type]
    assert e.value.errors[0]["code"] == "invalid_input"


def test_missing_required_layer_raises():
    ctx = make_context("A day")
    stripped = ctx.model_copy(update={"blocks": tuple(b for b in ctx.blocks if b.type != ContextLayer.IDENTITY)})
    with pytest.raises(PromptBuilderError) as e:
        build(stripped)
    assert e.value.errors[0]["code"] == "missing_required_layer"
