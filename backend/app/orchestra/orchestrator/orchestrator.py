"""Specialist Orchestrator — coordinates the specialists the Router selected.

Single responsibility: decide HOW the selected specialists work together —
safely, sequentially, deterministically. It never replaces the Orchestra or the
Router, never performs specialist work, and never generates user-facing
responses (Rule 24).

Execution is strictly sequential in this phase; ``allow_parallel_execution``
exists only as future architecture. Specialists never talk to each other: the
Orchestrator passes dependency outputs in, records results into a write-once
workspace, and is the only component that merges outputs.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Callable

from app.orchestra.orchestrator.errors import OrchestratorError
from app.orchestra.orchestrator.schemas import (
    AuditEntry,
    Conflict,
    OrchestrationResult,
    OrchestrationStatus,
    OrchestratorConfig,
    SpecialistExecutionPlan,
    SpecialistResult,
    SpecialistTask,
    SpecialistWorkspace,
    TaskStatus,
)
from app.orchestra.router.schemas import RoutingPlan

DEFAULT_ORCHESTRATOR_CONFIG_PATH = Path(__file__).with_name("specialist_orchestrator.json")

#: An executor performs ONE assigned task: (task, dependency_outputs) -> output dict.
Executor = Callable[[SpecialistTask, dict[str, dict[str, Any]]], dict[str, Any]]

# Output keys that are bookkeeping, not comparable findings.
_NON_FINDING_KEYS = {"confidence", "candidate"}


def load_orchestrator_config(
    path: Path | str = DEFAULT_ORCHESTRATOR_CONFIG_PATH,
) -> OrchestratorConfig:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise OrchestratorError(
            [{"field": "config", "code": "missing_config", "message": "specialist_orchestrator.json could not be loaded."}]
        )
    raw["dependencies"] = {k: tuple(v) for k, v in raw.get("dependencies", {}).items()}
    return OrchestratorConfig(**raw)


def build_execution_plan(
    routing_plan: RoutingPlan, config: OrchestratorConfig | None = None
) -> SpecialistExecutionPlan:
    """Turn the Router's WHO into an ordered, dependency-aware task list."""

    if not isinstance(routing_plan, RoutingPlan):
        raise OrchestratorError(
            [{"field": "routing_plan", "code": "invalid_input", "message": "Expected a RoutingPlan."}]
        )
    config = config or load_orchestrator_config()

    order = routing_plan.execution_order[: config.max_specialists_per_request]
    truncated = routing_plan.execution_order[config.max_specialists_per_request:]

    tasks = []
    for i, name in enumerate(order):
        # A dependency only binds when that specialist runs earlier in THIS plan.
        declared = config.dependencies.get(name, ())
        depends_on = tuple(d for d in declared if d in order[:i])
        role = "primary" if name == routing_plan.primary_specialist else "supporting"
        assignment = (
            "produce the reflection/reasoning for this request"
            if role == "primary"
            else "provide evidence, extracted data, analysis, or context"
        )
        tasks.append(
            SpecialistTask(
                specialist=name,
                order=i,
                role=role,
                assignment=assignment,
                depends_on=depends_on,
                timeout_s=config.default_timeout_seconds,
                retries=config.default_retries,
            )
        )

    return SpecialistExecutionPlan(
        request_id=routing_plan.request_id,
        routing_plan_id=routing_plan.plan_id,
        tasks=tuple(tasks),
        primary_specialist=routing_plan.primary_specialist,
        supporting_specialists=tuple(t.specialist for t in tasks if t.role == "supporting"),
        truncated=truncated,
        allow_parallel=False,
    )


class _Audit:
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    def log(self, specialist: str, event: str, detail: str = "") -> None:
        self.entries.append(
            AuditEntry(seq=len(self.entries), specialist=specialist, event=event, detail=detail)
        )


def _run_task(
    task: SpecialistTask,
    executor: Executor,
    inputs: dict[str, dict[str, Any]],
    audit: _Audit,
) -> SpecialistResult:
    """Run one task with retries and a soft timeout. Never raises."""

    attempts = 0
    last_error = ""
    while attempts <= task.retries:
        attempts += 1
        audit.log(task.specialist, "attempt", f"attempt {attempts}")
        start = time.perf_counter()
        try:
            output = executor(task, inputs)
        except Exception as exc:  # noqa: BLE001 — one specialist never crashes the Orchestra
            last_error = f"{type(exc).__name__}: {exc}"
            if attempts <= task.retries:
                audit.log(task.specialist, "retried", last_error)
            continue
        duration_ms = int((time.perf_counter() - start) * 1000)
        if duration_ms > task.timeout_s * 1000:
            last_error = f"soft timeout after {duration_ms}ms"
            audit.log(task.specialist, "timeout", last_error)
            return SpecialistResult(
                task_id=task.task_id, specialist=task.specialist, status=TaskStatus.TIMEOUT,
                attempts=attempts, duration_ms=duration_ms, error=last_error, confidence=0.0,
            )
        confidence = float(output.get("confidence", 0.8))
        audit.log(task.specialist, "completed", f"{duration_ms}ms")
        return SpecialistResult(
            task_id=task.task_id, specialist=task.specialist, status=TaskStatus.COMPLETED,
            output=output, confidence=confidence, attempts=attempts, duration_ms=duration_ms,
        )

    audit.log(task.specialist, "failed", last_error)
    return SpecialistResult(
        task_id=task.task_id, specialist=task.specialist, status=TaskStatus.FAILED,
        attempts=attempts, error=last_error, confidence=0.0,
    )


def _detect_conflicts(results: tuple[SpecialistResult, ...], audit: _Audit) -> tuple[Conflict, ...]:
    """Contradiction = two completed specialists reporting different values for
    the same finding key. Never resolved by guessing."""

    conflicts: list[Conflict] = []
    completed = [r for r in results if r.status == TaskStatus.COMPLETED]
    for i, a in enumerate(completed):
        for b in completed[i + 1:]:
            shared = (set(a.output) & set(b.output)) - _NON_FINDING_KEYS
            for key in sorted(shared):
                if a.output[key] != b.output[key]:
                    conflicts.append(
                        Conflict(
                            key=key,
                            specialists=(a.specialist, b.specialist),
                            values=(str(a.output[key]), str(b.output[key])),
                        )
                    )
                    audit.log(a.specialist, "conflict_detected", f"{key}: vs {b.specialist}")
    return tuple(conflicts)


def orchestrate(
    routing_plan: RoutingPlan,
    executors: dict[str, Executor],
    *,
    trace_id: uuid.UUID,
    config: OrchestratorConfig | None = None,
) -> OrchestrationResult:
    """Coordinate the selected specialists. Sequential, deterministic, safe."""

    if not isinstance(routing_plan, RoutingPlan):
        raise OrchestratorError(
            [{"field": "routing_plan", "code": "invalid_input", "message": "Expected a RoutingPlan."}]
        )
    config = config or load_orchestrator_config()
    audit = _Audit()

    # Guardian authority always wins: no specialists selected -> do nothing.
    if routing_plan.primary_specialist is None:
        audit.log("-", "blocked", "guardian authority — no specialists selected")
        return OrchestrationResult(
            trace_id=trace_id, routing_plan_id=routing_plan.plan_id, execution_order=(),
            primary_specialist=None, supporting_specialists=(), completed_tasks=(),
            failed_tasks=(), skipped_tasks=(), conflicts=(), merged_result={},
            confidence=1.0, status=OrchestrationStatus.BLOCKED,
            audit_trail=tuple(audit.entries), metadata={"reason": "guardian_blocked"},
        )

    plan = build_execution_plan(routing_plan, config)
    workspace = SpecialistWorkspace()
    skipped: list[str] = list(plan.truncated)
    for name in plan.truncated:
        audit.log(name, "skipped", "beyond max_specialists_per_request")

    stop_remaining = False
    for task in plan.tasks:
        if stop_remaining:
            audit.log(task.specialist, "skipped", "primary failed (fail fast)")
            skipped.append(task.specialist)
            continue

        # Dependencies: never guess a missing dependency's output.
        missing = [
            d for d in task.depends_on
            if (r := workspace.get(d)) is None or r.status != TaskStatus.COMPLETED
        ]
        if missing:
            audit.log(task.specialist, "skipped", f"dependency not satisfied: {missing}")
            skipped.append(task.specialist)
            continue

        executor = executors.get(task.specialist)
        if executor is None:
            audit.log(task.specialist, "failed", "no executor available")
            workspace.record(
                SpecialistResult(
                    task_id=task.task_id, specialist=task.specialist, status=TaskStatus.FAILED,
                    error="no executor available", confidence=0.0,
                )
            )
        else:
            audit.log(task.specialist, "task_started", task.role)
            inputs = {d: workspace.get(d).output for d in task.depends_on}  # type: ignore[union-attr]
            result = _run_task(task, executor, inputs, audit)
            if (
                result.status == TaskStatus.COMPLETED
                and result.confidence < config.low_confidence_threshold
            ):
                result = result.model_copy(update={"status": TaskStatus.DEGRADED})
                audit.log(task.specialist, "degraded", f"confidence {result.confidence}")
            workspace.record(result)

        primary_result = workspace.get(plan.primary_specialist or "")
        if (
            config.fail_fast_on_primary_failure
            and task.specialist == plan.primary_specialist
            and primary_result is not None
            and primary_result.status in (TaskStatus.FAILED, TaskStatus.TIMEOUT)
        ):
            stop_remaining = True

    results = workspace.results
    conflicts = _detect_conflicts(results, audit)

    completed = tuple(r.specialist for r in results if r.status in (TaskStatus.COMPLETED, TaskStatus.DEGRADED))
    failed = tuple(r.specialist for r in results if r.status in (TaskStatus.FAILED, TaskStatus.TIMEOUT))
    primary = plan.primary_specialist
    primary_ok = primary in completed

    # Fallback: if the primary failed and the Router named an available fallback
    # with an executor, the fallback becomes the primary voice.
    fallback = routing_plan.fallback_specialist
    if not primary_ok and fallback and fallback not in completed and fallback in executors:
        audit.log(fallback, "task_started", "fallback for failed primary")
        fb_task = SpecialistTask(
            specialist=fallback, order=len(plan.tasks), role="primary",
            assignment="fallback: produce the reflection/reasoning for this request",
            timeout_s=config.default_timeout_seconds, retries=config.default_retries,
        )
        fb_result = _run_task(fb_task, executors[fallback], {}, audit)
        workspace.record(fb_result)
        results = workspace.results
        if fb_result.status == TaskStatus.COMPLETED:
            primary = fallback
            primary_ok = True
            completed = completed + (fallback,)
        else:
            failed = failed + (fallback,)

    # Merge — ONLY the Orchestrator merges specialist outputs.
    merged: dict[str, Any] = {}
    if primary_ok:
        primary_result = workspace.get(primary)  # type: ignore[arg-type]
        merged = {
            "primary": primary_result.output,  # type: ignore[union-attr]
            "evidence": {
                r.specialist: r.output
                for r in results
                if r.specialist != primary and r.status in (TaskStatus.COMPLETED, TaskStatus.DEGRADED)
            },
        }
        audit.log(primary or "-", "merged", f"evidence from {len(merged['evidence'])} specialist(s)")

    degraded = bool(failed or skipped or conflicts or any(r.status == TaskStatus.DEGRADED for r in results))
    if not primary_ok:
        status = OrchestrationStatus.FAILED
    elif degraded:
        # Never hide serious uncertainty: degrade gracefully when allowed,
        # otherwise fail rather than pretend the result is whole.
        status = OrchestrationStatus.DEGRADED if config.allow_degraded_results else OrchestrationStatus.FAILED
    else:
        status = OrchestrationStatus.COMPLETED

    completed_confidences = [
        r.confidence for r in results if r.status in (TaskStatus.COMPLETED, TaskStatus.DEGRADED)
    ]
    confidence = min(completed_confidences) if completed_confidences else 0.0
    confidence = max(0.1, confidence - 0.1 * len(conflicts)) if completed_confidences else 0.0

    return OrchestrationResult(
        trace_id=trace_id,
        routing_plan_id=routing_plan.plan_id,
        execution_order=tuple(t.specialist for t in plan.tasks),
        primary_specialist=primary,
        supporting_specialists=plan.supporting_specialists,
        completed_tasks=completed,
        failed_tasks=failed,
        skipped_tasks=tuple(skipped),
        conflicts=conflicts,
        merged_result=merged,
        confidence=round(confidence, 3),
        status=status,
        audit_trail=tuple(audit.entries),
        metadata={"parallel_ready": False, "task_count": len(plan.tasks)},
    )
