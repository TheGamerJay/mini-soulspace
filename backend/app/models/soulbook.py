"""SoulBook Engine models: books, chapters, pages, bookmarks, recents.

Design goals (Phase 2):
- Normalized: Book 1─* Chapter 1─* Page, all owned by a User.
- Soft delete (`is_deleted`) + archive (`is_archived` on books).
- Ordering (`chapter_number`, `page_number`).
- Recency (`last_opened_at`, `updated_at`) for sorting.
- Future-ready: pages store plain_text/markdown (never HTML) so AI reflections,
  memory, exports and conversations can attach later without schema rewrites.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class ContentFormat(str, enum.Enum):
    """How a page's content is stored (never HTML)."""

    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"


class SoulBook(Base, TimestampMixin):
    __tablename__ = "soul_books"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_style: Mapped[str] = mapped_column(String(40), nullable=False, default="classic")
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    last_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    chapters: Mapped[list[SoulChapter]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )


class SoulChapter(Base, TimestampMixin):
    __tablename__ = "soul_chapters"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("soul_books.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    last_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    book: Mapped[SoulBook] = relationship(back_populates="chapters")
    pages: Mapped[list[SoulPage]] = relationship(
        back_populates="chapter", cascade="all, delete-orphan"
    )


class SoulPage(Base, TimestampMixin):
    __tablename__ = "soul_pages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("soul_books.id", ondelete="CASCADE"), index=True, nullable=False
    )
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("soul_chapters.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    page_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    content_format: Mapped[ContentFormat] = mapped_column(
        String(20), nullable=False, default=ContentFormat.MARKDOWN.value
    )
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    character_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    chapter: Mapped[SoulChapter] = relationship(back_populates="pages")


class SoulBookmark(Base):
    """A saved location (book/chapter/page). Foundation for a future bookmarks UI."""

    __tablename__ = "soul_bookmarks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("soul_books.id", ondelete="CASCADE"), nullable=False
    )
    chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("soul_chapters.id", ondelete="CASCADE"), nullable=True
    )
    page_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("soul_pages.id", ondelete="CASCADE"), nullable=True
    )
    label: Mapped[str | None] = mapped_column(String(150), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class SoulRecentBook(Base):
    """Per-user recently-opened book (upserted on open)."""

    __tablename__ = "soul_recent_books"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("soul_books.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class SoulRecentChapter(Base):
    """Per-user recently-opened chapter (upserted on open)."""

    __tablename__ = "soul_recent_chapters"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("soul_books.id", ondelete="CASCADE"), nullable=False
    )
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("soul_chapters.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
