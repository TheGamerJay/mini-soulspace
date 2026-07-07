"""SoulBook Engine business logic.

All access is scoped to the owning user: every lookup filters by ``user_id`` and
raises ``NotFoundError`` (surfaced as 404) when a record is missing or owned by
someone else — so users can never reach another user's books, chapters or pages.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.soulbook import (
    ContentFormat,
    SoulBook,
    SoulBookmark,
    SoulChapter,
    SoulPage,
    SoulRecentBook,
    SoulRecentChapter,
)
from app.schemas.soulbook import (
    SoulBookCreate,
    SoulBookUpdate,
    SoulChapterCreate,
    SoulChapterUpdate,
    SoulPageCreate,
    SoulPageUpdate,
    SortOption,
)


class NotFoundError(Exception):
    """Raised when a record does not exist or is not owned by the user."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def count_words(content: str | None) -> int:
    return len((content or "").split())


def count_characters(content: str | None) -> int:
    return len(content or "")


# ── SoulBooks ────────────────────────────────────────────────────────────────
def _book_query(db: Session, user_id: uuid.UUID):
    return select(SoulBook).where(SoulBook.user_id == user_id, SoulBook.is_deleted.is_(False))


def _apply_sort(stmt, sort: SortOption):
    if sort == SortOption.ALPHABETICAL:
        return stmt.order_by(func.lower(SoulBook.title).asc())
    if sort == SortOption.NEWEST:
        return stmt.order_by(SoulBook.created_at.desc())
    if sort == SortOption.OLDEST:
        return stmt.order_by(SoulBook.created_at.asc())
    if sort == SortOption.RECENTLY_UPDATED:
        return stmt.order_by(SoulBook.updated_at.desc())
    # recently_opened (default): nulls last-ish via coalesce to created_at
    return stmt.order_by(func.coalesce(SoulBook.last_opened_at, SoulBook.created_at).desc())


def _with_chapter_count(db: Session, book: SoulBook) -> SoulBook:
    book.chapter_count = db.scalar(  # type: ignore[attr-defined]
        select(func.count(SoulChapter.id)).where(
            SoulChapter.book_id == book.id, SoulChapter.is_deleted.is_(False)
        )
    )
    return book


def list_books(
    db: Session,
    user_id: uuid.UUID,
    *,
    sort: SortOption = SortOption.RECENTLY_OPENED,
    include_archived: bool = False,
) -> list[SoulBook]:
    stmt = _book_query(db, user_id)
    if not include_archived:
        stmt = stmt.where(SoulBook.is_archived.is_(False))
    stmt = _apply_sort(stmt, sort)
    books = list(db.scalars(stmt).all())
    for b in books:
        _with_chapter_count(db, b)
    return books


def get_book(db: Session, user_id: uuid.UUID, book_id: uuid.UUID, *, touch: bool = False) -> SoulBook:
    book = db.scalar(_book_query(db, user_id).where(SoulBook.id == book_id))
    if book is None:
        raise NotFoundError("SoulBook not found")
    if touch:
        book.last_opened_at = _now()
        _upsert_recent_book(db, user_id, book_id)
        db.flush()
    _with_chapter_count(db, book)
    return book


def create_book(db: Session, user_id: uuid.UUID, payload: SoulBookCreate) -> SoulBook:
    book = SoulBook(
        user_id=user_id,
        title=payload.title.strip(),
        description=payload.description,
        cover_style=payload.cover_style or "classic",
        last_opened_at=_now(),
    )
    db.add(book)
    db.flush()
    _with_chapter_count(db, book)
    return book


def update_book(db: Session, user_id: uuid.UUID, book_id: uuid.UUID, payload: SoulBookUpdate) -> SoulBook:
    book = get_book(db, user_id, book_id)
    data = payload.model_dump(exclude_unset=True)
    if "title" in data and data["title"]:
        data["title"] = data["title"].strip()
    for key, value in data.items():
        setattr(book, key, value)
    db.flush()
    _with_chapter_count(db, book)
    return book


def soft_delete_book(db: Session, user_id: uuid.UUID, book_id: uuid.UUID) -> None:
    book = get_book(db, user_id, book_id)
    book.is_deleted = True
    db.flush()


def archive_book(db: Session, user_id: uuid.UUID, book_id: uuid.UUID) -> SoulBook:
    book = get_book(db, user_id, book_id)
    book.is_archived = True
    db.flush()
    _with_chapter_count(db, book)
    return book


def restore_book(db: Session, user_id: uuid.UUID, book_id: uuid.UUID) -> SoulBook:
    book = get_book(db, user_id, book_id)
    book.is_archived = False
    db.flush()
    _with_chapter_count(db, book)
    return book


def _upsert_recent_book(db: Session, user_id: uuid.UUID, book_id: uuid.UUID) -> None:
    recent = db.scalar(select(SoulRecentBook).where(SoulRecentBook.book_id == book_id))
    if recent is None:
        db.add(SoulRecentBook(user_id=user_id, book_id=book_id, opened_at=_now()))
    else:
        recent.opened_at = _now()


# ── Chapters ─────────────────────────────────────────────────────────────────
def _chapter_query(db: Session, user_id: uuid.UUID, book_id: uuid.UUID):
    return select(SoulChapter).where(
        SoulChapter.user_id == user_id,
        SoulChapter.book_id == book_id,
        SoulChapter.is_deleted.is_(False),
    )


def _with_page_count(db: Session, chapter: SoulChapter) -> SoulChapter:
    chapter.page_count = db.scalar(  # type: ignore[attr-defined]
        select(func.count(SoulPage.id)).where(
            SoulPage.chapter_id == chapter.id, SoulPage.is_deleted.is_(False)
        )
    )
    return chapter


def list_chapters(db: Session, user_id: uuid.UUID, book_id: uuid.UUID) -> list[SoulChapter]:
    get_book(db, user_id, book_id)  # ownership check
    chapters = list(
        db.scalars(_chapter_query(db, user_id, book_id).order_by(SoulChapter.chapter_number.asc())).all()
    )
    for c in chapters:
        _with_page_count(db, c)
    return chapters


def get_chapter(
    db: Session, user_id: uuid.UUID, book_id: uuid.UUID, chapter_id: uuid.UUID, *, touch: bool = False
) -> SoulChapter:
    chapter = db.scalar(_chapter_query(db, user_id, book_id).where(SoulChapter.id == chapter_id))
    if chapter is None:
        raise NotFoundError("Chapter not found")
    if touch:
        chapter.last_opened_at = _now()
        _upsert_recent_chapter(db, user_id, book_id, chapter_id)
        db.flush()
    _with_page_count(db, chapter)
    return chapter


def create_chapter(
    db: Session, user_id: uuid.UUID, book_id: uuid.UUID, payload: SoulChapterCreate
) -> SoulChapter:
    get_book(db, user_id, book_id)  # ownership check
    next_number = (
        db.scalar(
            select(func.coalesce(func.max(SoulChapter.chapter_number), 0)).where(
                SoulChapter.book_id == book_id, SoulChapter.is_deleted.is_(False)
            )
        )
        or 0
    ) + 1
    chapter = SoulChapter(
        user_id=user_id,
        book_id=book_id,
        title=payload.title.strip(),
        chapter_number=next_number,
        last_opened_at=_now(),
    )
    db.add(chapter)
    db.flush()
    _with_page_count(db, chapter)
    return chapter


def update_chapter(
    db: Session,
    user_id: uuid.UUID,
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    payload: SoulChapterUpdate,
) -> SoulChapter:
    chapter = get_chapter(db, user_id, book_id, chapter_id)
    data = payload.model_dump(exclude_unset=True)
    if "title" in data and data["title"]:
        data["title"] = data["title"].strip()
    for key, value in data.items():
        setattr(chapter, key, value)
    db.flush()
    _with_page_count(db, chapter)
    return chapter


def soft_delete_chapter(
    db: Session, user_id: uuid.UUID, book_id: uuid.UUID, chapter_id: uuid.UUID
) -> None:
    chapter = get_chapter(db, user_id, book_id, chapter_id)
    chapter.is_deleted = True
    db.flush()


def _upsert_recent_chapter(
    db: Session, user_id: uuid.UUID, book_id: uuid.UUID, chapter_id: uuid.UUID
) -> None:
    recent = db.scalar(select(SoulRecentChapter).where(SoulRecentChapter.chapter_id == chapter_id))
    if recent is None:
        db.add(
            SoulRecentChapter(
                user_id=user_id, book_id=book_id, chapter_id=chapter_id, opened_at=_now()
            )
        )
    else:
        recent.opened_at = _now()


# ── Pages ────────────────────────────────────────────────────────────────────
def _page_query(db: Session, user_id: uuid.UUID, chapter_id: uuid.UUID):
    return select(SoulPage).where(
        SoulPage.user_id == user_id,
        SoulPage.chapter_id == chapter_id,
        SoulPage.is_deleted.is_(False),
    )


def list_pages(
    db: Session, user_id: uuid.UUID, book_id: uuid.UUID, chapter_id: uuid.UUID
) -> list[SoulPage]:
    get_chapter(db, user_id, book_id, chapter_id)  # ownership check
    return list(
        db.scalars(_page_query(db, user_id, chapter_id).order_by(SoulPage.page_number.asc())).all()
    )


def get_page(
    db: Session,
    user_id: uuid.UUID,
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    page_id: uuid.UUID,
) -> SoulPage:
    page = db.scalar(_page_query(db, user_id, chapter_id).where(SoulPage.id == page_id))
    if page is None:
        raise NotFoundError("Page not found")
    if page.book_id != book_id:
        raise NotFoundError("Page not found")
    return page


DEAR_DIARY = "Dear Diary...\n\n"


def create_page(
    db: Session,
    user_id: uuid.UUID,
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    payload: SoulPageCreate,
) -> SoulPage:
    get_chapter(db, user_id, book_id, chapter_id)  # ownership check
    next_number = (
        db.scalar(
            select(func.coalesce(func.max(SoulPage.page_number), 0)).where(
                SoulPage.chapter_id == chapter_id, SoulPage.is_deleted.is_(False)
            )
        )
        or 0
    ) + 1
    content = payload.content if payload.content is not None else DEAR_DIARY
    page = SoulPage(
        user_id=user_id,
        book_id=book_id,
        chapter_id=chapter_id,
        title=payload.title.strip(),
        content=content,
        page_number=next_number,
        content_format=ContentFormat(payload.content_format.value).value,
        timezone=payload.timezone,
        word_count=count_words(content),
        character_count=count_characters(content),
    )
    db.add(page)
    db.flush()
    return page


def update_page(
    db: Session,
    user_id: uuid.UUID,
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    page_id: uuid.UUID,
    payload: SoulPageUpdate,
) -> SoulPage:
    page = get_page(db, user_id, book_id, chapter_id, page_id)
    data = payload.model_dump(exclude_unset=True)
    if "title" in data and data["title"]:
        data["title"] = data["title"].strip()
    if "content_format" in data and data["content_format"] is not None:
        data["content_format"] = ContentFormat(data["content_format"]).value
    if "content" in data:
        page.content = data.pop("content") or ""
        page.word_count = count_words(page.content)
        page.character_count = count_characters(page.content)
    for key, value in data.items():
        setattr(page, key, value)
    db.flush()
    return page


def autosave_page(
    db: Session,
    user_id: uuid.UUID,
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    page_id: uuid.UUID,
    *,
    title: str | None = None,
    content: str | None = None,
) -> SoulPage:
    page = get_page(db, user_id, book_id, chapter_id, page_id)
    if title is not None and title.strip():
        page.title = title.strip()
    if content is not None:
        page.content = content
        page.word_count = count_words(content)
        page.character_count = count_characters(content)
    db.flush()
    return page


def soft_delete_page(
    db: Session,
    user_id: uuid.UUID,
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    page_id: uuid.UUID,
) -> None:
    page = get_page(db, user_id, book_id, chapter_id, page_id)
    page.is_deleted = True
    db.flush()


# ── Ribbon bookmark (the "close book" experience) ────────────────────────────
def set_bookmark(
    db: Session,
    user_id: uuid.UUID,
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    page_id: uuid.UUID,
    *,
    cursor: int | None = None,
) -> SoulBookmark:
    """Upsert the user's single ribbon bookmark (one per user)."""

    get_page(db, user_id, book_id, chapter_id, page_id)  # ownership check
    bookmark = db.scalar(select(SoulBookmark).where(SoulBookmark.user_id == user_id))
    label = str(cursor) if cursor is not None else None
    if bookmark is None:
        bookmark = SoulBookmark(
            user_id=user_id, book_id=book_id, chapter_id=chapter_id, page_id=page_id, label=label
        )
        db.add(bookmark)
    else:
        bookmark.book_id = book_id
        bookmark.chapter_id = chapter_id
        bookmark.page_id = page_id
        bookmark.label = label
    db.flush()
    return bookmark


def get_bookmark(db: Session, user_id: uuid.UUID) -> SoulBookmark | None:
    """Return the user's ribbon bookmark, if its target still exists."""

    bookmark = db.scalar(select(SoulBookmark).where(SoulBookmark.user_id == user_id))
    if bookmark is None or bookmark.chapter_id is None or bookmark.page_id is None:
        return None
    try:
        get_page(db, user_id, bookmark.book_id, bookmark.chapter_id, bookmark.page_id)
    except NotFoundError:
        return None
    return bookmark


# ── Search ───────────────────────────────────────────────────────────────────
def search(db: Session, user_id: uuid.UUID, query: str) -> tuple[list[SoulBook], list[SoulPage]]:
    q = (query or "").strip()
    if not q:
        return [], []
    like = f"%{q.lower()}%"

    books = list(
        db.scalars(
            _book_query(db, user_id)
            .where(
                or_(
                    func.lower(SoulBook.title).like(like),
                    func.lower(func.coalesce(SoulBook.description, "")).like(like),
                )
            )
            .order_by(func.lower(SoulBook.title).asc())
        ).all()
    )
    for b in books:
        _with_chapter_count(db, b)

    pages = list(
        db.scalars(
            select(SoulPage)
            .where(
                SoulPage.user_id == user_id,
                SoulPage.is_deleted.is_(False),
                or_(
                    func.lower(SoulPage.title).like(like),
                    func.lower(SoulPage.content).like(like),
                ),
            )
            .order_by(SoulPage.updated_at.desc())
            .limit(50)
        ).all()
    )
    return books, pages
