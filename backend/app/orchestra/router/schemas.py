"""Specialist Router schemas — capability cards + immutable RoutingPlan.

The Router decides WHO can help; the Orchestra decides HOW the conversation
flows (Constitution Rule 23). Structured only — the Router never generates
language or performs reasoning.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"


class Availability(str, enum.Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    HIDDEN = "hidden"
    UNAVAILABLE = "unavailable"
    EXPERIMENTAL = "experimental"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class SpecialistCard(_Frozen):
    """A specialist's self-description — everything the Router may know."""

    name: str
    display_name: str
    description: str
    purpose: str
    capabilities: tuple[str, ...]
    supported_inputs: tuple[str, ...]
    supported_outputs: tuple[str, ...]
    priority: int
    availability: Availability
    version: str
    health_status: str
    execution_mode: str  # local | remote | none
    estimated_cost: str  # low | medium | high
    estimated_speed: str  # fast | medium | slow
    service: str  # Mini Service key the Mini Engine resolves

    @property
    def participates(self) -> bool:
        """Whether the Router may select this specialist for execution."""

        return (
            self.availability in (Availability.ENABLED, Availability.EXPERIMENTAL)
            and self.health_status == "healthy"
            and self.execution_mode != "none"
        )


class Complexity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RoutingPlan(_Frozen):
    """Immutable output of the Specialist Router (node between Prompt Builder
    and the Mini Services)."""

    schema_version: str = SCHEMA_VERSION
    plan_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: uuid.UUID

    primary_specialist: str | None
    primary_service: str | None
    secondary_specialists: tuple[str, ...] = Field(default_factory=tuple)
    fallback_specialist: str | None = None
    execution_order: tuple[str, ...] = Field(default_factory=tuple)
    unavailable_specialists: tuple[str, ...] = Field(default_factory=tuple)

    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    estimated_complexity: Complexity = Complexity.LOW
    parallel_ready: bool = False  # future fan-out/fan-in — architecture only
    future_reserved: dict[str, Any] = Field(default_factory=dict)
