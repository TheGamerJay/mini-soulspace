"""Mini Engine schemas.

``CandidateResponse`` is the immutable downstream output. ``RuntimeResponse`` is
internal — raw runtime payloads are never exposed downstream.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class MiniService(_Frozen):
    """One entry from the Mini Service Registry."""

    key: str
    display_name: str
    purpose: str
    runtime: str
    model: str


class TokenCounts(_Frozen):
    prompt: int = 0
    completion: int = 0
    total: int = 0


class RuntimeResponse(_Frozen):
    """Internal, sanitized view of a local-runtime result. Never sent downstream."""

    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    finish_reason: str = "stop"
    duration_ms: int = 0


class CandidateResponse(_Frozen):
    """Immutable output of the Mini Engine — the candidate reflection text."""

    schema_version: str = SCHEMA_VERSION
    response_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: uuid.UUID

    service_name: str
    service_display_name: str
    model_used: str

    response_text: str
    generation_time_ms: int
    token_counts: TokenCounts
    finish_reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
