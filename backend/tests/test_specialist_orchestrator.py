"""Specialist Orchestrator tests — full coverage. Sequential, deterministic."""

from __future__ import annotations

import time
import uuid

import pytest

from app.orchestra.orchestrator import (
    OrchestrationStatus,
    OrchestratorConfig,
    OrchestratorError,
    SpecialistResult,
    SpecialistWorkspace,
    TaskStatus,
    build_execution_plan,
    load_orchestrator_config,
    orchestrate,
)
from app.orchestra.router.schemas import RoutingPlan

TRACE = uuid.uuid4()
CFG = OrchestratorConfig(
    default_timeout_seconds=5.0,
    default_retries=1,
    max_specialists_per_request=3,
    dependencies={"mini_research": ("mini_vision",), "mini_tutor": ("mini_vision",), "mini_memory": ("mini_research",)},
)


def make_routing(order: list[str], *, primary: str | None = None, fallback: str | None = "mini_core") -> RoutingPlan:
    primary = primary if primary is not None else (order[0] if order else None)
    return RoutingPlan(
        request_id=uuid.uuid4(),
        primary_specialist=primary,
        primary_service=primary,
        secondary_specialists=tuple(order[1:]),
        fallback_specialist=fallback,
        execution_order=tuple(order),
        reasoning="test",
        confidence=0.9,
    )


def ok(name: str, output: dict | None = None):
    return lambda task, inputs: {**(output or {"note": f"{name} ok"})}


# ── Execution plan ────────────────────────────────────────────────────────────
def test_plan_roles_dependencies_and_order():
    plan = build_execution_plan(make_routing(["mini_vision", "mini_research", "mini_core"], primary="mini_core"), CFG)
    assert [t.specialist for t in plan.tasks] == ["mini_vision", "mini_research", "mini_core"]
    assert plan.tasks[1].depends_on == ("mini_vision",)  # research needs vision
    assert plan.tasks[2].role == "primary"
    assert plan.supporting_specialists == ("mini_vision", "mini_research")
    assert plan.allow_parallel is False


def test_plan_dependency_only_binds_when_present():
    plan = build_execution_plan(make_routing(["mini_research"]), CFG)
    assert plan.tasks[0].depends_on == ()  # vision not in this plan


def test_plan_truncates_beyond_max():
    cfg = CFG.model_copy(update={"max_specialists_per_request": 2})
    plan = build_execution_plan(make_routing(["a", "b", "c", "d"]), cfg)
    assert len(plan.tasks) == 2
    assert plan.truncated == ("c", "d")


def test_plan_invalid_input():
    with pytest.raises(OrchestratorError):
        build_execution_plan("nope", CFG)  # type: ignore[arg-type]


# ── Sequential execution ──────────────────────────────────────────────────────
def test_single_specialist_completed():
    res = orchestrate(make_routing(["mini_core"]), {"mini_core": ok("core")}, trace_id=TRACE, config=CFG)
    assert res.status == OrchestrationStatus.COMPLETED
    assert res.primary_specialist == "mini_core"
    assert res.completed_tasks == ("mini_core",)
    assert res.merged_result["primary"]["note"] == "core ok"
    assert res.trace_id == TRACE


def test_multi_specialist_sequential_merge():
    executors = {
        "mini_vision": ok("vision", {"ocr_text": "aspirin 100mg"}),
        "mini_research": lambda task, inputs: {"summary": f"researched {inputs['mini_vision']['ocr_text']}"},
        "mini_core": ok("core", {"reflection": "here is what I found"}),
    }
    res = orchestrate(
        make_routing(["mini_vision", "mini_research", "mini_core"], primary="mini_core"),
        executors, trace_id=TRACE, config=CFG,
    )
    assert res.status == OrchestrationStatus.COMPLETED
    assert res.execution_order == ("mini_vision", "mini_research", "mini_core")
    # Only the Orchestrator passed data between specialists:
    assert res.merged_result["evidence"]["mini_research"]["summary"] == "researched aspirin 100mg"
    assert res.merged_result["primary"]["reflection"] == "here is what I found"
    assert res.supporting_specialists == ("mini_vision", "mini_research")


# ── Failure / dependency handling ─────────────────────────────────────────────
def boom(task, inputs):
    raise RuntimeError("specialist exploded")


def test_failed_dependency_skips_dependent():
    executors = {"mini_vision": boom, "mini_research": ok("research"), "mini_core": ok("core")}
    res = orchestrate(
        make_routing(["mini_vision", "mini_research", "mini_core"], primary="mini_core"),
        executors, trace_id=TRACE, config=CFG,
    )
    assert "mini_vision" in res.failed_tasks
    assert "mini_research" in res.skipped_tasks  # never guess a missing dependency
    assert "mini_core" in res.completed_tasks  # safe to continue
    assert res.status == OrchestrationStatus.DEGRADED


def test_retry_success():
    calls = {"n": 0}

    def flaky(task, inputs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("first attempt fails")
        return {"note": "recovered"}

    res = orchestrate(make_routing(["mini_core"]), {"mini_core": flaky}, trace_id=TRACE, config=CFG)
    assert res.status == OrchestrationStatus.COMPLETED
    assert calls["n"] == 2
    assert any(e.event == "retried" for e in res.audit_trail)


def test_retry_failure_no_infinite():
    res = orchestrate(make_routing(["mini_core"], fallback=None), {"mini_core": boom}, trace_id=TRACE, config=CFG)
    assert res.status == OrchestrationStatus.FAILED
    assert res.failed_tasks == ("mini_core",)
    attempts = [e for e in res.audit_trail if e.event == "attempt"]
    assert len(attempts) == CFG.default_retries + 1  # bounded, never infinite


def test_soft_timeout():
    cfg = CFG.model_copy(update={"default_timeout_seconds": 0.005, "default_retries": 0})

    def slow(task, inputs):
        time.sleep(0.02)
        return {"note": "too late"}

    res = orchestrate(make_routing(["mini_core"], fallback=None), {"mini_core": slow}, trace_id=TRACE, config=cfg)
    assert res.status == OrchestrationStatus.FAILED
    assert any(e.event == "timeout" for e in res.audit_trail)


def test_missing_executor_fails_gracefully():
    res = orchestrate(make_routing(["mini_vision"], fallback=None), {}, trace_id=TRACE, config=CFG)
    assert res.status == OrchestrationStatus.FAILED
    assert res.failed_tasks == ("mini_vision",)


def test_fail_fast_skips_remaining_after_primary_failure():
    executors = {"mini_vision": boom, "mini_research": ok("research")}
    res = orchestrate(
        make_routing(["mini_vision", "mini_research"], primary="mini_vision", fallback=None),
        executors, trace_id=TRACE, config=CFG,
    )
    assert "mini_research" in res.skipped_tasks
    assert res.status == OrchestrationStatus.FAILED


def test_fallback_specialist_recovers_primary():
    executors = {"mini_vision": boom, "mini_core": ok("core", {"reflection": "fallback voice"})}
    res = orchestrate(
        make_routing(["mini_vision"], primary="mini_vision", fallback="mini_core"),
        executors, trace_id=TRACE, config=CFG,
    )
    assert res.primary_specialist == "mini_core"
    assert res.status == OrchestrationStatus.DEGRADED  # recovered, but not whole
    assert res.merged_result["primary"]["reflection"] == "fallback voice"


def test_fallback_also_failing_stays_failed():
    executors = {"mini_vision": boom, "mini_core": boom}
    res = orchestrate(
        make_routing(["mini_vision"], primary="mini_vision", fallback="mini_core"),
        executors, trace_id=TRACE, config=CFG,
    )
    assert res.status == OrchestrationStatus.FAILED
    assert "mini_core" in res.failed_tasks


# ── Conflicts + degradation ───────────────────────────────────────────────────
def test_conflict_detected_never_resolved():
    executors = {
        "mini_vision": ok("v", {"medication": "aspirin"}),
        "mini_core": ok("c", {"medication": "ibuprofen", "reflection": "hmm"}),
    }
    res = orchestrate(
        make_routing(["mini_vision", "mini_core"], primary="mini_core"),
        executors, trace_id=TRACE, config=CFG,
    )
    assert len(res.conflicts) == 1
    conflict = res.conflicts[0]
    assert conflict.key == "medication"
    assert set(conflict.values) == {"aspirin", "ibuprofen"}
    assert res.status == OrchestrationStatus.DEGRADED  # sent onward, not guessed
    assert res.confidence < 0.8


def test_low_confidence_output_degrades():
    executors = {"mini_core": ok("c", {"reflection": "unsure", "confidence": 0.2})}
    res = orchestrate(make_routing(["mini_core"]), executors, trace_id=TRACE, config=CFG)
    assert res.status == OrchestrationStatus.DEGRADED
    assert any(e.event == "degraded" for e in res.audit_trail)


def test_degraded_not_allowed_fails():
    cfg = CFG.model_copy(update={"allow_degraded_results": False})
    executors = {"mini_vision": boom, "mini_core": ok("core")}
    res = orchestrate(
        make_routing(["mini_vision", "mini_core"], primary="mini_core"),
        executors, trace_id=TRACE, config=cfg,
    )
    assert res.status == OrchestrationStatus.FAILED  # never hide uncertainty


# ── Guardian authority + workspace protection ─────────────────────────────────
def test_guardian_blocked_does_nothing():
    res = orchestrate(make_routing([], primary=None, fallback=None), {"mini_core": ok("c")}, trace_id=TRACE, config=CFG)
    assert res.status == OrchestrationStatus.BLOCKED
    assert res.execution_order == ()
    assert res.merged_result == {}
    assert res.metadata["reason"] == "guardian_blocked"


def test_workspace_write_once():
    ws = SpecialistWorkspace()
    r = SpecialistResult(task_id=uuid.uuid4(), specialist="mini_core", status=TaskStatus.COMPLETED)
    ws.record(r)
    with pytest.raises(OrchestratorError) as e:
        ws.record(r.model_copy(update={"output": {"hacked": True}}))
    assert e.value.code == "workspace_conflict"
    assert ws.get("mini_core").output == {}  # original untouched — no overwrite
    assert len(ws.results) == 1


def test_truncated_specialists_skipped():
    cfg = CFG.model_copy(update={"max_specialists_per_request": 1})
    executors = {"mini_core": ok("core")}
    res = orchestrate(
        make_routing(["mini_core", "mini_vision", "mini_research"], primary="mini_core"),
        executors, trace_id=TRACE, config=cfg,
    )
    assert set(res.skipped_tasks) == {"mini_vision", "mini_research"}


# ── Audit + contract ──────────────────────────────────────────────────────────
def test_audit_trail_is_ordered_and_complete():
    res = orchestrate(make_routing(["mini_core"]), {"mini_core": ok("core")}, trace_id=TRACE, config=CFG)
    events = [e.event for e in res.audit_trail]
    assert events == ["task_started", "attempt", "completed", "merged"]
    assert [e.seq for e in res.audit_trail] == [0, 1, 2, 3]


def test_result_immutable():
    res = orchestrate(make_routing(["mini_core"]), {"mini_core": ok("core")}, trace_id=TRACE, config=CFG)
    with pytest.raises(Exception):
        res.status = OrchestrationStatus.FAILED  # type: ignore[misc]


def test_config_loads_and_missing_raises():
    cfg = load_orchestrator_config()
    assert cfg.allow_parallel_execution is False
    assert cfg.dependencies["mini_research"] == ("mini_vision",)
    with pytest.raises(OrchestratorError) as e:
        load_orchestrator_config("nope.json")
    assert e.value.code == "missing_config"


def test_orchestrate_invalid_input():
    with pytest.raises(OrchestratorError):
        orchestrate("nope", {}, trace_id=TRACE, config=CFG)  # type: ignore[arg-type]
