"""GuardianResult — immutable, versioned output of the Guardian Engine (node 2).

Structured data only — never user-facing prose. Downstream nodes read it and
never modify it. Additive changes must stay backwards compatible (add optional
fields; bump the minor version).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"


class GuardianCategory(str, enum.Enum):
    SAFE = "SAFE"
    LOW_CONCERN = "LOW_CONCERN"
    EMOTIONAL_SUPPORT = "EMOTIONAL_SUPPORT"
    HIGH_EMOTIONAL_DISTRESS = "HIGH_EMOTIONAL_DISTRESS"
    SELF_HARM_RISK = "SELF_HARM_RISK"
    HARM_TO_OTHERS = "HARM_TO_OTHERS"
    MEDICAL_INFORMATION = "MEDICAL_INFORMATION"
    LEGAL_INFORMATION = "LEGAL_INFORMATION"
    ACADEMIC_HELP = "ACADEMIC_HELP"
    PROJECT_ASSISTANCE = "PROJECT_ASSISTANCE"
    IMAGE_ANALYSIS = "IMAGE_ANALYSIS"
    RESEARCH = "RESEARCH"
    EMERGENCY = "EMERGENCY"
    UNKNOWN = "UNKNOWN"


class EmotionalTone(str, enum.Enum):
    NEUTRAL = "Neutral"
    POSITIVE = "Positive"
    REFLECTIVE = "Reflective"
    JOYFUL = "Joyful"
    HOPEFUL = "Hopeful"
    FRUSTRATED = "Frustrated"
    ANGRY = "Angry"
    ANXIOUS = "Anxious"
    SAD = "Sad"
    GRIEVING = "Grieving"
    OVERWHELMED = "Overwhelmed"
    MIXED = "Mixed"
    UNCERTAIN = "Uncertain"


class ReflectionDepth(str, enum.Enum):
    NONE = "None"
    LIGHT = "Light"
    MEDIUM = "Medium"
    DEEP = "Deep"


class RecommendedAction(str, enum.Enum):
    CONTINUE_REFLECTION = "continue_reflection"
    GENTLE_REFLECTION = "gentle_reflection"
    LISTEN_ONLY = "listen_only"
    CELEBRATE = "celebrate"
    ENCOURAGE_SUPPORT = "encourage_support"
    CRISIS_RESPONSE = "crisis_response"
    DECLINE_OVERRIDE = "decline_override"
    CLARIFY = "clarify"
    BLOCK = "block"


class GuardianResult(BaseModel):
    """Immutable protective decision for one OrchestraRequest."""

    model_config = ConfigDict(frozen=True)

    schema_version: str = SCHEMA_VERSION
    result_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: uuid.UUID  # links back to the OrchestraRequest (traceability)

    # Classification
    category: GuardianCategory
    emotional_tone: EmotionalTone

    # Decisions
    allow_reflection: bool
    allow_memory_storage: bool
    allow_memory_retrieval: bool
    allow_questions: bool
    max_questions: int = Field(ge=0, le=2)
    reflection_depth: ReflectionDepth
    allow_identity_override: bool
    allow_roleplay_override: bool
    needs_human_referral: bool
    needs_crisis_template: bool
    recommended_action: RecommendedAction
    confidence: float = Field(ge=0.0, le=1.0)

    # Structured reasoning (internal/debug only — never shown to users)
    reason: str
    signals: tuple[str, ...] = Field(default_factory=tuple)
