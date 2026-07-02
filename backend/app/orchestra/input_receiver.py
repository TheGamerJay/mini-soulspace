"""Input Receiver — the first Orchestra node.

Single responsibility: convert raw application state into an immutable
``OrchestraRequest``. It only **collects, validates and packages** facts. It
performs no reflection, memory, safety, prompt, or model work — and never
modifies the source data. It reuses the Phase 2 SoulBook service for
ownership-scoped reads (no duplicated data access).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import User
from app.orchestra.errors import InputValidationError, error
from app.orchestra.schemas import (
    OrchestraBook,
    OrchestraChapter,
    OrchestraPage,
    OrchestraRequest,
    OrchestraSession,
    OrchestraStatistics,
    OrchestraTimestamps,
    OrchestraUser,
)
from app.services import soulbook_service as svc


def _validate_relationships(book, chapter, page) -> list[dict[str, str]]:
    """Defensive relationship integrity checks (facts must line up)."""

    errors: list[dict[str, str]] = []
    if chapter.book_id != book.id:
        errors.append(error("chapter", "corrupted_relationship", "Chapter does not belong to book."))
    if page.book_id != book.id:
        errors.append(error("page", "corrupted_relationship", "Page does not belong to book."))
    if page.chapter_id != chapter.id:
        errors.append(error("page", "corrupted_relationship", "Page does not belong to chapter."))
    return errors


def _validate_facts(page, language: str, resolved_timezone: str) -> list[dict[str, str]]:
    """Presence checks for content, language and timezone."""

    errors: list[dict[str, str]] = []
    if page.content is None:
        errors.append(error("page_content", "missing_content", "Page content is missing."))
    if not language:
        errors.append(error("language", "missing_language", "User language is missing."))
    if not resolved_timezone:
        errors.append(error("timezone", "missing_timezone", "Timezone is missing."))
    return errors


def build_orchestra_request(
    db: Session,
    user: User | None,
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    page_id: uuid.UUID,
    *,
    session_id: str | None = None,
    metadata: dict | None = None,
) -> OrchestraRequest:
    """Collect + validate application state into an immutable OrchestraRequest.

    Raises ``InputValidationError`` (with structured ``errors``) on any failure;
    never returns a partially-built or invalid request.
    """

    if user is None:
        raise InputValidationError(
            [error("user", "missing_user", "Authenticated user is required.")]
        )

    # Ownership-scoped reads. A missing OR foreign record raises NotFoundError,
    # which we translate into a structured validation error (never leaking which).
    try:
        book = svc.get_book(db, user.id, book_id)
    except svc.NotFoundError:
        raise InputValidationError(
            [error("book", "book_not_found", "SoulBook not found for this user.")]
        )
    try:
        chapter = svc.get_chapter(db, user.id, book_id, chapter_id)
    except svc.NotFoundError:
        raise InputValidationError(
            [error("chapter", "chapter_not_found", "Chapter not found for this book.")]
        )
    try:
        page = svc.get_page(db, user.id, book_id, chapter_id, page_id)
    except svc.NotFoundError:
        raise InputValidationError(
            [error("page", "page_not_found", "Page not found for this chapter.")]
        )

    language = user.preferred_language
    resolved_timezone = page.timezone or user.timezone

    errors = _validate_relationships(book, chapter, page) + _validate_facts(
        page, language, resolved_timezone
    )
    if errors:
        raise InputValidationError(errors)

    content = page.content or ""

    return OrchestraRequest(
        user=OrchestraUser(
            id=user.id,
            display_name=user.display_name,
            timezone=user.timezone,
            preferred_language=user.preferred_language,
        ),
        book=OrchestraBook(
            id=book.id,
            title=book.title,
            cover_style=book.cover_style,
            book_type=book.cover_style,
            last_opened_at=book.last_opened_at,
        ),
        chapter=OrchestraChapter(
            id=chapter.id,
            title=chapter.title,
            chapter_number=chapter.chapter_number,
        ),
        page=OrchestraPage(
            id=page.id,
            title=page.title,
            page_number=page.page_number,
            content_format=page.content_format,
            timezone=page.timezone,
        ),
        page_content=content,
        statistics=OrchestraStatistics(
            word_count=svc.count_words(content),
            character_count=svc.count_characters(content),
        ),
        timestamps=OrchestraTimestamps(
            page_created_at=page.created_at,
            page_updated_at=page.updated_at,
            book_last_opened_at=book.last_opened_at,
        ),
        language=language,
        timezone=resolved_timezone,
        session=OrchestraSession(
            session_id=session_id,
            started_at=datetime.now(timezone.utc),
            last_opened_at=book.last_opened_at,
        ),
        metadata={"book_type": book.cover_style, **(metadata or {})},
    )
