"""Immutable, versioned OrchestraRequest — the output of the Input Receiver node.

This object represents **facts only** (no AI-specific fields). Once created it is
read-only: no Orchestra node may modify it; downstream nodes produce their own
outputs instead. New fields must be added in a backwards-compatible way (add
optional fields; bump ``SCHEMA_VERSION`` minor).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

#: Semantic version of the OrchestraRequest schema. Additive changes bump minor.
SCHEMA_VERSION = "1.0"


class _Frozen(BaseModel):
    """Base for immutable value objects."""

    model_config = ConfigDict(frozen=True)


class OrchestraUser(_Frozen):
    id: uuid.UUID
    display_name: str
    timezone: str
    preferred_language: str


class OrchestraBook(_Frozen):
    id: uuid.UUID
    title: str
    cover_style: str
    book_type: str
    last_opened_at: datetime | None


class OrchestraChapter(_Frozen):
    id: uuid.UUID
    title: str
    chapter_number: int


class OrchestraPage(_Frozen):
    id: uuid.UUID
    title: str
    page_number: int
    content_format: str
    timezone: str | None
    cursor_position: int | None = None  # future ready


class OrchestraStatistics(_Frozen):
    word_count: int
    character_count: int


class OrchestraTimestamps(_Frozen):
    page_created_at: datetime
    page_updated_at: datetime
    book_last_opened_at: datetime | None


class OrchestraSession(_Frozen):
    session_id: str | None = None
    started_at: datetime
    last_opened_at: datetime | None = None


class OrchestraRequest(_Frozen):
    """The structured package every downstream Orchestra node receives."""

    schema_version: str = SCHEMA_VERSION
    request_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: OrchestraUser
    book: OrchestraBook
    chapter: OrchestraChapter
    page: OrchestraPage
    page_content: str
    statistics: OrchestraStatistics
    timestamps: OrchestraTimestamps
    language: str
    timezone: str
    session: OrchestraSession
    metadata: dict = Field(default_factory=dict)
    future_reserved: dict = Field(default_factory=dict)
