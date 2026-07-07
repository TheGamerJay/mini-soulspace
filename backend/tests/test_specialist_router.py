"""Specialist Router tests — full coverage. Deterministic, registry-driven."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest

from app.orchestra.guardian import evaluate as guardian_eval
from app.orchestra.meaning import analyze as meaning_analyze
from app.orchestra.memory.schemas import RetrievalResult
from app.orchestra.planner import plan as planner_plan
from app.orchestra.router import (
    Availability,
    Complexity,
    RouterError,
    RoutingPlan,
    find_by_capability,
    future_specialists,
    load_specialists,
    route,
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


def stages(content: str, book: str = "Personal Journal"):
    req = make_request(content, book)
    meaning = meaning_analyze(req)
    guardian = guardian_eval(req, meaning)
    retrieval = RetrievalResult(request_id=req.request_id, retrieved=(), count=0, blocked=False, reason="")
    planner = planner_plan(req, guardian, retrieval)
    return req, meaning, guardian, planner


def run_route(content: str, book: str = "Personal Journal", registry=None, **kw) -> RoutingPlan:
    req, meaning, guardian, planner = stages(content, book)
    if registry is None:
        registry = load_specialists()
    return route(req, meaning, guardian, planner, registry, **kw)


@pytest.fixture
def enabled_registry(tmp_path):
    """A registry where Vision/Research/Tutor are deployable — proving future
    specialists activate by configuration, never by code changes."""

    raw = json.loads(
        (load_specialists.__globals__["DEFAULT_SPECIALISTS_PATH"]).read_text(encoding="utf-8")
    )
    for name in ("mini_vision", "mini_research", "mini_tutor"):
        raw["specialists"][name]["availability"] = "enabled"
        raw["specialists"][name]["health_status"] = "healthy"
        raw["specialists"][name]["execution_mode"] = "local"
    path = tmp_path / "specialists.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    return load_specialists(path)


# ── Registry ──────────────────────────────────────────────────────────────────
def test_registry_loads_all_capability_cards():
    reg = load_specialists()
    assert set(reg) == {
        "mini_core", "mini_vision", "mini_research", "mini_tutor", "mini_creator",
        "mini_canvas", "mini_analyst", "mini_voice", "mini_memory",
    }
    core = reg["mini_core"]
    assert core.participates is True
    assert core.availability == Availability.ENABLED
    assert core.service == "mini_core"
    vision = reg["mini_vision"]
    assert vision.participates is False  # architecture only
    assert "identity_recognition" not in vision.capabilities  # never supported
    assert "medication_recognition" in vision.capabilities


def test_registry_missing_raises():
    with pytest.raises(RouterError) as e:
        load_specialists("nope.json")
    assert e.value.code == "missing_registry"


def test_capability_discovery_priority_order():
    reg = load_specialists()
    cards = find_by_capability(reg, {"tutoring", "image_understanding"})
    assert [c.name for c in cards] == ["mini_vision", "mini_tutor"]  # priority desc


def test_future_specialists_registered():
    names = future_specialists()
    assert "mini_music" in names and "mini_coding_agent" in names
    assert len(names) == 15


# ── Selection ─────────────────────────────────────────────────────────────────
def test_diary_page_routes_to_mini_core():
    plan = run_route("Today was a calm, ordinary day")
    assert plan.primary_specialist == "mini_core"
    assert plan.primary_service == "mini_core"
    assert plan.secondary_specialists == ()
    assert plan.execution_order == ("mini_core",)
    assert plan.estimated_complexity == Complexity.LOW
    assert plan.parallel_ready is False
    assert plan.confidence == 0.9


def test_unavailable_specialist_falls_back_to_core():
    plan = run_route("Can you help with my homework assignment on fractions")
    assert plan.primary_specialist == "mini_core"  # tutor is architecture-only
    assert "mini_tutor" in plan.unavailable_specialists
    assert plan.fallback_specialist == "mini_core"
    assert "fallback" in plan.reasoning


def test_enabled_specialist_selected(enabled_registry):
    plan = run_route("Can you help with my homework assignment on fractions", registry=enabled_registry)
    assert plan.primary_specialist == "mini_tutor"
    assert plan.primary_service == "mini_tutor"
    assert plan.unavailable_specialists == ()


def test_multi_specialist_sequential_routing(enabled_registry):
    # Medication photo: Vision → Research (requested capability = future attachment).
    plan = run_route(
        "what medication is this, please identify it",
        registry=enabled_registry,
        requested_capabilities=("image_understanding",),
    )
    assert plan.primary_specialist == "mini_vision"
    assert "mini_research" in plan.secondary_specialists
    assert plan.execution_order[0] == "mini_vision"
    assert plan.estimated_complexity in (Complexity.MEDIUM, Complexity.HIGH)


def test_research_routing(enabled_registry):
    plan = run_route("I'm doing research on sleep cycles", book="Research Notes", registry=enabled_registry)
    assert plan.primary_specialist == "mini_research"


def test_requested_capabilities_route_analyst():
    # No analyst deployment yet: requested capability -> unavailable -> fallback.
    plan = run_route("please analyse this table", requested_capabilities=("data_analysis",))
    assert "mini_analyst" in plan.unavailable_specialists
    assert plan.primary_specialist == "mini_core"


# ── Guardian authority ────────────────────────────────────────────────────────
def test_crisis_selects_no_specialists():
    plan = run_route("I want to hurt myself tonight")
    assert plan.primary_specialist is None
    assert plan.primary_service is None
    assert plan.execution_order == ()
    assert "guardian authority" in plan.reasoning
    assert plan.confidence == 1.0


def test_no_available_specialist_raises(tmp_path):
    raw = {"specialists": {}, "future_specialists": []}
    path = tmp_path / "empty.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(RouterError) as e:
        run_route("a calm day", registry=load_specialists(path))
    assert e.value.code == "no_available_specialist"


# ── Contract-level ────────────────────────────────────────────────────────────
def test_plan_is_immutable_and_versioned():
    plan = run_route("a calm day")
    assert plan.schema_version == "1.0"
    with pytest.raises(Exception):
        plan.primary_specialist = "x"  # type: ignore[misc]


def test_invalid_inputs():
    req, meaning, guardian, planner = stages("hello there")
    reg = load_specialists()
    with pytest.raises(RouterError):
        route("x", meaning, guardian, planner, reg)  # type: ignore[arg-type]
    with pytest.raises(RouterError):
        route(req, "x", guardian, planner, reg)  # type: ignore[arg-type]
    with pytest.raises(RouterError):
        route(req, meaning, "x", planner, reg)  # type: ignore[arg-type]
    with pytest.raises(RouterError):
        route(req, meaning, guardian, "x", reg)  # type: ignore[arg-type]
