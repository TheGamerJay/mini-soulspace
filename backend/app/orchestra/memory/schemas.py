"""RetrievedMemory + RetrievalResult — immutable, versioned outputs of node 3.

Structured only — never raw DB rows, never user-facing prose. Additive changes
must stay backwards compatible (optional fields; bump the minor version).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"


class MemoryType(str, enum.Enum):
    GOAL = "goal"
    ACHIEVEMENT = "achievement"
    PROJECT = "project"
    BIRTHDAY = "birthday"
    RELATIONSHIP = "relationship"
    PREFERENCE = "preference"
    LIFE_EVENT = "life_event"
    DIARY_ENTRY = "diary_entry"
    WRITING_HISTORY = "writing_history"
    MILESTONE = "milestone"
    # Extended in Phase 3.8 (Memory Writer). Additive — the Retriever accepts them.
    ANNIVERSARY = "anniversary"
    SKILL = "skill"
    HABIT = "habit"
    ROUTINE = "routine"
    FAVORITE = "favorite"
    REMINDER_PREFERENCE = "reminder_preference"
    CREATIVE_PROJECT = "creative_project"
    LEARNING_PROGRESS = "learning_progress"
    HEALTH_PREFERENCE = "health_preference"
    TRAVEL = "travel"
    PET = "pet"
    QUOTE = "quote"
    CUSTOM = "custom"


class MemoryPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class RetrievedMemory(_Frozen):
    id: uuid.UUID
    memory_type: MemoryType
    priority: MemoryPriority
    title: str
    summary: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    why_selected: str
    related_ids: tuple[uuid.UUID, ...] = Field(default_factory=tuple)
    created_at: datetime | None = None


class RetrievalResult(_Frozen):
    schema_version: str = SCHEMA_VERSION
    result_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: uuid.UUID

    retrieved: tuple[RetrievedMemory, ...] = Field(default_factory=tuple)
    count: int = 0
    blocked: bool = False
    reason: str = ""
