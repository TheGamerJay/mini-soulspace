"""Specialist Orchestrator — the Router chooses the team; this coordinates the
work (Rule 24). Sequential, deterministic, write-once workspace, no user-facing
output. See docs/SPECIALIST_ORCHESTRATOR.md.
"""

from app.orchestra.orchestrator.errors import OrchestratorError
from app.orchestra.orchestrator.orchestrator import (
    DEFAULT_ORCHESTRATOR_CONFIG_PATH,
    build_execution_plan,
    load_orchestrator_config,
    orchestrate,
)
from app.orchestra.orchestrator.schemas import (
    SCHEMA_VERSION,
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

__all__ = [
    "orchestrate",
    "build_execution_plan",
    "load_orchestrator_config",
    "DEFAULT_ORCHESTRATOR_CONFIG_PATH",
    "OrchestratorError",
    "OrchestratorConfig",
    "SpecialistExecutionPlan",
    "SpecialistTask",
    "SpecialistResult",
    "SpecialistWorkspace",
    "OrchestrationResult",
    "OrchestrationStatus",
    "TaskStatus",
    "Conflict",
    "AuditEntry",
    "SCHEMA_VERSION",
]
