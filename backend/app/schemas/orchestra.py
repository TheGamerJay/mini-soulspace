"""API schemas for the Orchestra endpoints (reflect / close / bookmark)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class MemoryUpdateOut(BaseModel):
    op: str
    memory_type: str | None = None
    importance: str | None = None
    title: str | None = None


class NodeMetricOut(BaseModel):
    node: str
    status: str
    ms: int
    reason: str = ""


class ReflectionOut(BaseModel):
    """What the frontend receives after the Orchestra runs (via the Composer)."""

    trace_id: uuid.UUID
    delivered: bool
    status: str
    text: str
    memory_updates: list[MemoryUpdateOut] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
    failure_reason: str | None = None
    total_ms: int
    # Populated only when orchestra.json debug_mode is enabled (developers only).
    metrics: list[NodeMetricOut] | None = None
    slowest_node: str | None = None


class ClosePageRequest(BaseModel):
    """Optional final save + cursor before the book closes."""

    title: str | None = Field(default=None, max_length=150)
    content: str | None = None
    cursor: int | None = Field(default=None, ge=0)


class BookmarkOut(BaseModel):
    book_id: uuid.UUID
    chapter_id: uuid.UUID
    page_id: uuid.UUID
    cursor: int | None = None
    book_title: str
    chapter_title: str
    page_title: str


class ClosePageResponse(BaseModel):
    reflection: ReflectionOut
    bookmark: BookmarkOut
