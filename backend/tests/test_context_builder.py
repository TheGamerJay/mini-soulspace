"""Context Builder tests — full coverage. No AI, assembles only."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.orchestra.context import (
    ContextBudget,
    ContextBuilderError,
    ContextLayer,
    ContextPackage,
    build,
)
from app.orchestra.guardian import evaluate as guardian_eval
from app.orchestra.memory.schemas import (
    MemoryPriority,
    MemoryType,
    RetrievalResult,
    RetrievedMemory,
)
from app.orchestra.planner.schemas import (
    PlannerResult,
    PlanTone,
    QuestionType,
    ReflectionDepth,
    ReflectionPlan,
    ReflectionType,
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


def make_request(content: str = "Today was a calm day", book_title: str = "Journal") -> OrchestraRequest:
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


def make_mem(mtype=MemoryType.DIARY_ENTRY, priority=MemoryPriority.MEDIUM, summary="s") -> RetrievedMemory:
    return RetrievedMemory(
        id=uuid.uuid4(), memory_type=mtype, priority=priority, title="mem",
        summary=summary, relevance_score=0.5, confidence=0.5, why_selected="matched: x",
    )


def make_retrieval(request_id, mems=(), blocked=False) -> RetrievalResult:
    return RetrievalResult(request_id=request_id, retrieved=tuple(mems), count=len(mems), blocked=blocked, reason="r")


def make_planner(request_id, *, reference=False, memories=(), confidence=0.7) -> PlannerResult:
    plan = ReflectionPlan(
        reflection_type=ReflectionType.REFLECTION, tone=PlanTone.THOUGHTFUL, depth=ReflectionDepth.MEDIUM,
        emotional_style="thoughtful", ask_question=False, question_type=QuestionType.NONE, question_count=0,
        reference_memories=reference, memories_to_use=tuple(memories), max_memories=len(memories),
        celebrate=False, encourage=False, listen_only=False,
    )
    return PlannerResult(request_id=request_id, plan=plan, confidence=confidence, reason="test")


def types_in_order(pkg: ContextPackage):
    return [b.type for b in pkg.blocks]


# ── Layers / ordering ─────────────────────────────────────────────────────────
def test_basic_layers_and_order():
    req = make_request()
    g = guardian_eval(req)
    pkg = build(req, g, make_retrieval(req.request_id), make_planner(req.request_id))
    assert isinstance(pkg, ContextPackage)
    assert types_in_order(pkg) == [
        ContextLayer.IDENTITY, ContextLayer.GUARDIAN, ContextLayer.CURRENT_PAGE, ContextLayer.REFLECTION,
    ]
    assert pkg.statistics.block_count == 4
    assert pkg.statistics.memory_count == 0


def test_planner_excluded_memory_note():
    req = make_request()
    g = guardian_eval(req)
    pkg = build(req, g, make_retrieval(req.request_id, [make_mem()]), make_planner(req.request_id, reference=False))
    assert any(n.reason == "planner_excluded" for n in pkg.excluded)


def test_memories_included_when_approved():
    req = make_request()
    g = guardian_eval(req)
    m1, m2 = make_mem(), make_mem()
    planner = make_planner(req.request_id, reference=True, memories=[m1.id, m2.id])
    pkg = build(req, g, make_retrieval(req.request_id, [m1, m2]), planner)
    assert ContextLayer.MEMORY in types_in_order(pkg)
    assert pkg.statistics.memory_count == 2
    # memory sits between page and reflection
    assert types_in_order(pkg) == [
        ContextLayer.IDENTITY, ContextLayer.GUARDIAN, ContextLayer.CURRENT_PAGE,
        ContextLayer.MEMORY, ContextLayer.REFLECTION,
    ]


# ── Gates ─────────────────────────────────────────────────────────────────────
def test_guardian_blocks_memory():
    req = make_request()
    blocked_guardian = guardian_eval(make_request("I want to die by suicide"))
    m = make_mem()
    planner = make_planner(req.request_id, reference=True, memories=[m.id])
    pkg = build(req, blocked_guardian, make_retrieval(req.request_id, [m]), planner)
    assert pkg.statistics.memory_count == 0
    assert any(n.reason == "blocked_by_guardian" for n in pkg.excluded)


def test_retrieval_blocked_note():
    req = make_request()
    g = guardian_eval(req)
    m = make_mem()
    planner = make_planner(req.request_id, reference=True, memories=[m.id])
    pkg = build(req, g, make_retrieval(req.request_id, [m], blocked=True), planner)
    assert any(n.reason == "retrieval_blocked" for n in pkg.excluded)


def test_not_in_retrieval_note():
    req = make_request()
    g = guardian_eval(req)
    stray = uuid.uuid4()
    planner = make_planner(req.request_id, reference=True, memories=[stray])
    pkg = build(req, g, make_retrieval(req.request_id), planner)
    assert any(n.reason == "not_in_retrieval" for n in pkg.excluded)


def test_duplicate_memory_deduped():
    req = make_request()
    g = guardian_eval(req)
    m = make_mem()
    planner = make_planner(req.request_id, reference=True, memories=[m.id, m.id])
    pkg = build(req, g, make_retrieval(req.request_id, [m]), planner)
    assert pkg.statistics.memory_count == 1
    assert any(n.reason == "duplicate" for n in pkg.excluded)


# ── Budget caps ───────────────────────────────────────────────────────────────
def test_max_memories_cap():
    req = make_request()
    g = guardian_eval(req)
    m1, m2 = make_mem(), make_mem()
    planner = make_planner(req.request_id, reference=True, memories=[m1.id, m2.id])
    pkg = build(req, g, make_retrieval(req.request_id, [m1, m2]), planner, budget=ContextBudget(max_memories=1))
    assert pkg.statistics.memory_count == 1
    assert any(n.reason == "max_memories" for n in pkg.excluded)


def test_max_goals_cap():
    req = make_request()
    g = guardian_eval(req)
    m1, m2 = make_mem(MemoryType.GOAL), make_mem(MemoryType.GOAL)
    planner = make_planner(req.request_id, reference=True, memories=[m1.id, m2.id])
    pkg = build(req, g, make_retrieval(req.request_id, [m1, m2]), planner, budget=ContextBudget(max_goals=1))
    assert any(n.reason == "max_goals" for n in pkg.excluded)


def test_max_projects_cap():
    req = make_request()
    g = guardian_eval(req)
    m1, m2 = make_mem(MemoryType.PROJECT), make_mem(MemoryType.PROJECT)
    planner = make_planner(req.request_id, reference=True, memories=[m1.id, m2.id])
    pkg = build(req, g, make_retrieval(req.request_id, [m1, m2]), planner, budget=ContextBudget(max_projects=1))
    assert any(n.reason == "max_projects" for n in pkg.excluded)


def test_budget_drops_memory_block_only():
    req = make_request("short entry")
    g = guardian_eval(req)
    big = [make_mem(summary="x" * 400), make_mem(summary="y" * 400)]
    planner = make_planner(req.request_id, reference=True, memories=[big[0].id, big[1].id])
    pkg = build(req, g, make_retrieval(req.request_id, big), planner, budget=ContextBudget(max_total_chars=1500))
    assert ContextLayer.MEMORY not in types_in_order(pkg)
    assert any(n.reason == "budget_char_limit" for n in pkg.excluded)
    assert not any(n.reason == "budget_char_limit_truncated" for n in pkg.excluded)


def test_budget_truncates_page():
    long_content = "word " * 400
    req = make_request(long_content)
    g = guardian_eval(req)
    m = make_mem(summary="z" * 200)
    planner = make_planner(req.request_id, reference=True, memories=[m.id])
    pkg = build(req, g, make_retrieval(req.request_id, [m]), planner, budget=ContextBudget(max_total_chars=300))
    page = next(b for b in pkg.blocks if b.type == ContextLayer.CURRENT_PAGE)
    assert page.content.get("truncated") is True
    assert any(n.reason == "budget_char_limit_truncated" for n in pkg.excluded)


def test_large_entry_within_budget_not_trimmed():
    req = make_request("A reasonably sized reflection. " * 20)
    g = guardian_eval(req)
    pkg = build(req, g, make_retrieval(req.request_id), make_planner(req.request_id))
    page = next(b for b in pkg.blocks if b.type == ContextLayer.CURRENT_PAGE)
    assert page.content.get("truncated") is None
    assert not any("budget" in n.reason for n in pkg.excluded)


# ── Contract-level ────────────────────────────────────────────────────────────
def test_confidence_is_average():
    req = make_request()
    g = guardian_eval(req)
    planner = make_planner(req.request_id, confidence=0.5)
    pkg = build(req, g, make_retrieval(req.request_id), planner)
    assert pkg.confidence == round((g.confidence + 0.5) / 2, 2)
    assert pkg.schema_version == "1.0"


def test_statistics_and_reasons():
    req = make_request()
    g = guardian_eval(req)
    pkg = build(req, g, make_retrieval(req.request_id), make_planner(req.request_id))
    assert pkg.statistics.total_chars == sum(b.char_count for b in pkg.blocks)
    assert all(b.reason for b in pkg.blocks)
    assert all(b.source for b in pkg.blocks)


def test_package_is_immutable():
    req = make_request()
    g = guardian_eval(req)
    pkg = build(req, g, make_retrieval(req.request_id), make_planner(req.request_id))
    with pytest.raises(Exception):
        pkg.confidence = 0.1  # type: ignore[misc]
    with pytest.raises(Exception):
        pkg.blocks[0].priority = None  # type: ignore[misc]


# ── Failure cases ─────────────────────────────────────────────────────────────
def test_invalid_inputs_raise():
    req = make_request()
    g = guardian_eval(req)
    r = make_retrieval(req.request_id)
    p = make_planner(req.request_id)
    with pytest.raises(ContextBuilderError):
        build("x", g, r, p)  # type: ignore[arg-type]
    with pytest.raises(ContextBuilderError):
        build(req, "x", r, p)  # type: ignore[arg-type]
    with pytest.raises(ContextBuilderError):
        build(req, g, "x", p)  # type: ignore[arg-type]
    with pytest.raises(ContextBuilderError):
        build(req, g, r, "x")  # type: ignore[arg-type]
