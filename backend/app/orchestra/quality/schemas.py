"""QualityResult + Violation — immutable, versioned output of node 8.

Structured only — the Quality Checker never sends text to the user. Additive
changes must stay backwards compatible (optional fields; bump the minor version).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"


class QualityStatus(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_RETRY = "needs_retry"


class Severity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class Violation(_Frozen):
    code: str
    severity: Severity
    message: str
    source_rule: str
    fixable: bool


class QualityResult(_Frozen):
    schema_version: str = SCHEMA_VERSION
    result_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: uuid.UUID

    status: QualityStatus
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    violations: tuple[Violation, ...] = Field(default_factory=tuple)
    recommended_action: str
    retry_allowed: bool
    retry_reason: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
