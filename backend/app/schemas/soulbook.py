"""SoulBook Engine schemas."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SortOption(str, enum.Enum):
    RECENTLY_OPENED = "recently_opened"
    RECENTLY_UPDATED = "recently_updated"
    ALPHABETICAL = "alphabetical"
    NEWEST = "newest"
    OLDEST = "oldest"


class ContentFormatEnum(str, enum.Enum):
    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"


# ── SoulBook ─────────────────────────────────────────────────────────────────
class SoulBookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    cover_style: str | None = Field(default=None, max_length=40)


class SoulBookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    cover_style: str | None = Field(default=None, max_length=40)


class SoulBookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    cover_style: str
    is_archived: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    last_opened_at: datetime | None
    chapter_count: int = 0


# ── Chapter ──────────────────────────────────────────────────────────────────
class SoulChapterCreate(BaseModel):
    title: str = Field(min_length=1, max_length=150)


class SoulChapterUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    chapter_number: int | None = Field(default=None, ge=1)


class SoulChapterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    book_id: uuid.UUID
    title: str
    chapter_number: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    last_opened_at: datetime | None
    page_count: int = 0


# ── Page ─────────────────────────────────────────────────────────────────────
class SoulPageCreate(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    content: str | None = None
    content_format: ContentFormatEnum = ContentFormatEnum.MARKDOWN
    timezone: str | None = Field(default=None, max_length=64)


class SoulPageUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    content: str | None = None
    content_format: ContentFormatEnum | None = None
    page_number: int | None = Field(default=None, ge=1)


class SoulPageAutosave(BaseModel):
    """Lightweight autosave payload (content and/or title)."""

    title: str | None = Field(default=None, max_length=150)
    content: str | None = None


class SoulPageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    book_id: uuid.UUID
    chapter_id: uuid.UUID
    title: str
    content: str
    page_number: int
    content_format: str
    timezone: str | None
    word_count: int
    character_count: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class SoulPageSaveResult(BaseModel):
    """Returned by autosave — enough for the client to update its status line."""

    id: uuid.UUID
    updated_at: datetime
    word_count: int
    character_count: int
    status: str = "saved"


class SearchResults(BaseModel):
    books: list[SoulBookRead]
    pages: list[SoulPageRead]
