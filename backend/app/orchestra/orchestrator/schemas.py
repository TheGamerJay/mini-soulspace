"""Specialist Orchestrator schemas — plans, tasks, results, workspace, audit.

The Router chooses the team; the Orchestrator controls the work (Rule 24).
Specialists perform only their assigned task, never talk to each other, never
modify shared state, never write final responses. Only the Orchestrator passes
data between specialists and merges outputs.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.orchestra.orchestrator.errors import OrchestratorError

SCHEMA_VERSION = "1.0"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class OrchestratorConfig(_Frozen):
    """Loaded from specialist_orchestrator.json — nothing hardcoded."""

    default_timeout_seconds: float = 30.0
    default_retries: int = 1
    allow_parallel_execution: bool = False  # future architecture only
    max_specialists_per_request: int = 3
    fail_fast_on_primary_failure: bool = True
    allow_degraded_results: bool = True
    low_confidence_threshold: float = 0.4
    dependencies: dict[str, tuple[str, ...]] = Field(default_factory=dict)


class TaskStatus(str, enum.Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    DEGRADED = "degraded"


class SpecialistTask(_Frozen):
    """One assignment: a specialist performs exactly this, nothing more."""

    task_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    specialist: str
    order: int
    role: str  # "primary" | "supporting"
    assignment: str
    depends_on: tuple[str, ...] = Field(default_factory=tuple)
    timeout_s: float
    retries: int


class SpecialistExecutionPlan(_Frozen):
    schema_version: str = SCHEMA_VERSION
    plan_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: uuid.UUID
    routing_plan_id: uuid.UUID

    tasks: tuple[SpecialistTask, ...]
    primary_specialist: str | None
    supporting_specialists: tuple[str, ...] = Field(default_factory=tuple)
    truncated: tuple[str, ...] = Field(default_factory=tuple)  # beyond the max cap
    allow_parallel: bool = False  # future fan-out — architecture only


class SpecialistResult(_Frozen):
    """A specialist's structured output — evidence, extraction, analysis, or
    context. Never a final user-facing response."""

    task_id: uuid.UUID
    specialist: str
    status: TaskStatus
    output: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    attempts: int = 0
    duration_ms: int = 0
    error: str = ""


class Conflict(_Frozen):
    """A detected contradiction — never resolved by guessing; the Quality
    Checker receives it."""

    key: str
    specialists: tuple[str, ...]
    values: tuple[str, ...]


class AuditEntry(_Frozen):
    seq: int
    specialist: str
    event: str  # task_started | attempt | completed | failed | timeout | retried | skipped | conflict_detected | merged | blocked
    detail: str = ""


class OrchestrationStatus(str, enum.Enum):
    COMPLETED = "completed"
    DEGRADED = "degraded"
    FAILED = "failed"
    BLOCKED = "blocked"


class OrchestrationResult(_Frozen):
    schema_version: str = SCHEMA_VERSION
    result_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    trace_id: uuid.UUID
    routing_plan_id: uuid.UUID
    execution_order: tuple[str, ...]
    primary_specialist: str | None
    supporting_specialists: tuple[str, ...]
    completed_tasks: tuple[str, ...]
    failed_tasks: tuple[str, ...]
    skipped_tasks: tuple[str, ...]
    conflicts: tuple[Conflict, ...]
    merged_result: dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    status: OrchestrationStatus
    audit_trail: tuple[AuditEntry, ...]
    metadata: dict[str, Any] = Field(default_factory=dict)


class SpecialistWorkspace:
    """Temporary shared workspace — write-once per specialist.

    Specialists cannot overwrite another specialist's result (no races, no
    shared-state mutation). Only the Orchestrator reads it to merge outputs.
    """

    def __init__(self) -> None:
        self._results: dict[str, SpecialistResult] = {}

    def record(self, result: SpecialistResult) -> None:
        if result.specialist in self._results:
            raise OrchestratorError(
                [{
                    "field": "workspace",
                    "code": "workspace_conflict",
                    "message": f"'{result.specialist}' already recorded a result; overwriting is forbidden.",
                }]
            )
        self._results[result.specialist] = result

    def get(self, specialist: str) -> SpecialistResult | None:
        return self._results.get(specialist)

    @property
    def results(self) -> tuple[SpecialistResult, ...]:
        return tuple(self._results.values())
