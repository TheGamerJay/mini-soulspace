"""ReflectionPlan + PlannerResult — immutable, versioned outputs of node 4.

Structured decisions only — no user-facing text, no prompts. Reuses the
Guardian's ``ReflectionDepth`` (never duplicated). Additive changes must stay
backwards compatible (optional fields; bump the minor version).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

# Reuse the Guardian's depth enum — one source of truth (Constitution: no dupes).
from app.orchestra.guardian.schemas import ReflectionDepth

SCHEMA_VERSION = "1.0"

__all__ = [
    "SCHEMA_VERSION",
    "ReflectionDepth",
    "ReflectionType",
    "PlanTone",
    "QuestionType",
    "ReflectionPlan",
    "PlannerResult",
]


class ReflectionType(str, enum.Enum):
    LISTENING = "listening"
    VALIDATION = "validation"
    ENCOURAGEMENT = "encouragement"
    CELEBRATION = "celebration"
    REFLECTION = "reflection"
    GOAL_SUPPORT = "goal_support"
    MEMORY_RECALL = "memory_recall"
    GENTLE_CHALLENGE = "gentle_challenge"
    CLARIFICATION = "clarification"
    EDUCATION = "education"
    RESEARCH_SUMMARY = "research_summary"
    PROJECT_SUPPORT = "project_support"
    CREATIVE_INSPIRATION = "creative_inspiration"
    SIMPLE_ACKNOWLEDGEMENT = "simple_acknowledgement"
    NO_REFLECTION = "no_reflection"


class PlanTone(str, enum.Enum):
    CALM = "calm"
    WARM = "warm"
    GENTLE = "gentle"
    HOPEFUL = "hopeful"
    THOUGHTFUL = "thoughtful"
    CELEBRATORY = "celebratory"
    CURIOUS = "curious"
    ENCOURAGING = "encouraging"
    QUIET = "quiet"
    RESPECTFUL = "respectful"


class QuestionType(str, enum.Enum):
    NONE = "none"
    OPEN = "open"
    REFLECTIVE = "reflective"
    CLARIFYING = "clarifying"
    FUTURE_ORIENTED = "future_oriented"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class ReflectionPlan(_Frozen):
    reflection_type: ReflectionType
    tone: PlanTone
    depth: ReflectionDepth
    emotional_style: str

    ask_question: bool
    question_type: QuestionType
    question_count: int = Field(ge=0, le=2)

    reference_memories: bool
    memories_to_use: tuple[uuid.UUID, ...] = Field(default_factory=tuple)
    max_memories: int = Field(ge=0)

    celebrate: bool
    encourage: bool
    listen_only: bool


class PlannerResult(_Frozen):
    schema_version: str = SCHEMA_VERSION
    result_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: uuid.UUID

    plan: ReflectionPlan
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
