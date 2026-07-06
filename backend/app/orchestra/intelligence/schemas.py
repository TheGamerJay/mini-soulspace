"""Memory Intelligence schemas — immutable, versioned.

``MemoryIntelligenceResult`` explains one memory-quality operation (assessment,
decay, correction). Every stored memory must be explainable: confidence,
evidence, source, provenance (Constitution Rule 19).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"


class MemorySource(str, enum.Enum):
    SIGNUP_FORM = "signup_form"
    SOULDIARY = "souldiary"
    CONVERSATION = "conversation"
    VOICE_CONVERSATION = "voice_conversation"
    IMAGE_ANALYSIS = "image_analysis"
    DOCUMENT_ANALYSIS = "document_analysis"
    CALENDAR = "calendar"
    MANUAL_USER_ENTRY = "manual_user_entry"
    IMPORTED_DATA = "imported_data"
    SYSTEM_GENERATED = "system_generated"


class VerificationStatus(str, enum.Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    NEEDS_VERIFICATION = "needs_verification"
    OUTDATED = "outdated"


class NextAction(str, enum.Enum):
    NONE = "none"
    MONITOR = "monitor"
    SCHEDULE_VERIFICATION = "schedule_verification"
    UPDATED = "updated"
    CORRECTED = "corrected"


class IntelligenceConfig(BaseModel):
    """Configurable thresholds — nothing hardcoded. ``type_overrides`` prepares
    per-memory-type thresholds for the future."""

    model_config = ConfigDict(frozen=True)

    auto_store_threshold: float = 0.90
    needs_verification_threshold: float = 0.70
    low_confidence_threshold: float = 0.50
    minimum_confidence: float = 0.00
    confidence_decay_enabled: bool = True
    verification_enabled: bool = True
    decay_per_day: float = 0.0005
    correction_pattern_threshold: int = 2
    correction_confidence_penalty: float = 0.05
    type_overrides: dict[str, dict[str, float]] = Field(default_factory=dict)


class MemoryIntelligenceResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: str = SCHEMA_VERSION
    result_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    memory_id: uuid.UUID

    confidence: float = Field(ge=0.0, le=1.0)
    confidence_reason: str
    memory_source: MemorySource
    evidence: dict[str, Any]
    verification_status: VerificationStatus
    last_verified_at: datetime | None = None
    last_updated_at: datetime | None = None
    previous_version: int | None = None
    next_action: NextAction
    metadata: dict[str, Any] = Field(default_factory=dict)


#: Future analytics event names — architecture only, NOT implemented (Phase 4+).
ANALYTICS_EVENTS: tuple[str, ...] = (
    "MemoryCreated",
    "MemoryUpdated",
    "UserCorrectionApplied",
    "DuplicateMemoryPrevented",
    "ConfidenceAdjusted",
    "VerificationScheduled",
    "VerificationSucceeded",
)
