"""MemoryDecision — immutable, versioned output of node 9 (Memory Writer).

Structured only. Reuses the Retriever's ``MemoryType`` / ``MemoryPriority`` — one
source of truth (Constitution: no duplication). Additive changes must stay
backwards compatible (optional fields; bump the minor version).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.orchestra.memory.schemas import MemoryPriority, MemoryType

SCHEMA_VERSION = "1.0"


class MemoryDecision(BaseModel):
    """Whether (and what) to remember from a completed, approved exchange."""

    model_config = ConfigDict(frozen=True)

    schema_version: str = SCHEMA_VERSION
    decision_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: uuid.UUID

    store_memory: bool
    importance: MemoryPriority | None = None
    memory_type: MemoryType | None = None
    title: str | None = None
    summary: str | None = None
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
