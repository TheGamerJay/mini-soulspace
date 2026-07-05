"""ContextBlock + ContextPackage — immutable, versioned outputs of node 5.

Structured only — no prompts, no generated text. The ContextPackage becomes the
sole input to the Prompt Builder. Additive changes must stay backwards compatible
(optional fields; bump the minor version).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"


class ContextLayer(str, enum.Enum):
    IDENTITY = "identity"          # Layer 1 — Soul Companion identity (reserved ref)
    GUARDIAN = "guardian"          # Layer 2 — Guardian decisions/restrictions
    CURRENT_PAGE = "current_page"  # Layer 3 — the journal page + metadata
    MEMORY = "memory"              # Layer 4 — Guardian+Planner-approved memories
    REFLECTION = "reflection"      # Layer 5 — the ReflectionPlan
    RESERVED = "reserved"          # Layer 6 — future specialists (empty for now)


class ContextPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class ContextBlock(_Frozen):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    type: ContextLayer
    priority: ContextPriority
    source: str
    reason: str  # why this block exists (internal only)
    content: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    char_count: int = 0


class ContextBudget(_Frozen):
    max_memories: int = 3
    max_projects: int = 2
    max_goals: int = 2
    max_total_chars: int = 6000
    max_total_tokens: int | None = None  # future ready


class ExcludedNote(_Frozen):
    """Records anything left out (budget/relevance) — never silently discarded."""

    item: str
    reason: str


class ContextStatistics(_Frozen):
    block_count: int
    total_chars: int
    memory_count: int
    excluded_count: int


class ContextPackage(_Frozen):
    schema_version: str = SCHEMA_VERSION
    package_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: uuid.UUID

    blocks: tuple[ContextBlock, ...] = Field(default_factory=tuple)
    statistics: ContextStatistics
    budget: ContextBudget
    excluded: tuple[ExcludedNote, ...] = Field(default_factory=tuple)
    confidence: float = Field(ge=0.0, le=1.0)
