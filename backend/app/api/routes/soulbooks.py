"""SoulBook Engine routes (protected). Thin layer over soulbook_service."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.soulbook import (
    SearchResults,
    SoulBookCreate,
    SoulBookRead,
    SoulBookUpdate,
    SoulChapterCreate,
    SoulChapterRead,
    SoulChapterUpdate,
    SoulPageAutosave,
    SoulPageCreate,
    SoulPageRead,
    SoulPageSaveResult,
    SoulPageUpdate,
    SortOption,
)
from app.services import soulbook_service as svc

router = APIRouter(prefix="/soulbooks", tags=["soulbooks"])

CurrentUser = Depends(get_current_active_user)
Db = Depends(get_db)


# ── SoulBooks ────────────────────────────────────────────────────────────────
@router.get("", response_model=list[SoulBookRead], summary="List SoulBooks")
def list_books(
    sort: SortOption = Query(SortOption.RECENTLY_OPENED),
    include_archived: bool = Query(False),
    user: User = CurrentUser,
    db: Session = Db,
):
    return svc.list_books(db, user.id, sort=sort, include_archived=include_archived)


@router.post("", response_model=SoulBookRead, status_code=status.HTTP_201_CREATED, summary="Create SoulBook")
def create_book(payload: SoulBookCreate, user: User = CurrentUser, db: Session = Db):
    book = svc.create_book(db, user.id, payload)
    db.commit()
    return book


@router.get("/search", response_model=SearchResults, summary="Search SoulBooks & pages")
def search(q: str = Query("", max_length=200), user: User = CurrentUser, db: Session = Db):
    books, pages = svc.search(db, user.id, q)
    return SearchResults(
        books=[SoulBookRead.model_validate(b) for b in books],
        pages=[SoulPageRead.model_validate(p) for p in pages],
    )


@router.get("/{book_id}", response_model=SoulBookRead, summary="Open a SoulBook")
def get_book(book_id: uuid.UUID, user: User = CurrentUser, db: Session = Db):
    book = svc.get_book(db, user.id, book_id, touch=True)
    db.commit()
    return book


@router.patch("/{book_id}", response_model=SoulBookRead, summary="Rename / update SoulBook")
def update_book(book_id: uuid.UUID, payload: SoulBookUpdate, user: User = CurrentUser, db: Session = Db):
    book = svc.update_book(db, user.id, book_id, payload)
    db.commit()
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Soft-delete SoulBook")
def delete_book(book_id: uuid.UUID, user: User = CurrentUser, db: Session = Db):
    svc.soft_delete_book(db, user.id, book_id)
    db.commit()


@router.post("/{book_id}/archive", response_model=SoulBookRead, summary="Archive SoulBook")
def archive_book(book_id: uuid.UUID, user: User = CurrentUser, db: Session = Db):
    book = svc.archive_book(db, user.id, book_id)
    db.commit()
    return book


@router.post("/{book_id}/restore", response_model=SoulBookRead, summary="Restore SoulBook")
def restore_book(book_id: uuid.UUID, user: User = CurrentUser, db: Session = Db):
    book = svc.restore_book(db, user.id, book_id)
    db.commit()
    return book


# ── Chapters ─────────────────────────────────────────────────────────────────
@router.get("/{book_id}/chapters", response_model=list[SoulChapterRead], summary="List chapters")
def list_chapters(book_id: uuid.UUID, user: User = CurrentUser, db: Session = Db):
    return svc.list_chapters(db, user.id, book_id)


@router.post(
    "/{book_id}/chapters",
    response_model=SoulChapterRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create chapter",
)
def create_chapter(
    book_id: uuid.UUID, payload: SoulChapterCreate, user: User = CurrentUser, db: Session = Db
):
    chapter = svc.create_chapter(db, user.id, book_id, payload)
    db.commit()
    return chapter


@router.get("/{book_id}/chapters/{chapter_id}", response_model=SoulChapterRead, summary="Open chapter")
def get_chapter(book_id: uuid.UUID, chapter_id: uuid.UUID, user: User = CurrentUser, db: Session = Db):
    chapter = svc.get_chapter(db, user.id, book_id, chapter_id, touch=True)
    db.commit()
    return chapter


@router.patch("/{book_id}/chapters/{chapter_id}", response_model=SoulChapterRead, summary="Rename chapter")
def update_chapter(
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    payload: SoulChapterUpdate,
    user: User = CurrentUser,
    db: Session = Db,
):
    chapter = svc.update_chapter(db, user.id, book_id, chapter_id, payload)
    db.commit()
    return chapter


@router.delete(
    "/{book_id}/chapters/{chapter_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete chapter",
)
def delete_chapter(book_id: uuid.UUID, chapter_id: uuid.UUID, user: User = CurrentUser, db: Session = Db):
    svc.soft_delete_chapter(db, user.id, book_id, chapter_id)
    db.commit()


# ── Pages ────────────────────────────────────────────────────────────────────
@router.get(
    "/{book_id}/chapters/{chapter_id}/pages",
    response_model=list[SoulPageRead],
    summary="List pages",
)
def list_pages(book_id: uuid.UUID, chapter_id: uuid.UUID, user: User = CurrentUser, db: Session = Db):
    return svc.list_pages(db, user.id, book_id, chapter_id)


@router.post(
    "/{book_id}/chapters/{chapter_id}/pages",
    response_model=SoulPageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create page (starts with 'Dear Diary...')",
)
def create_page(
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    payload: SoulPageCreate,
    user: User = CurrentUser,
    db: Session = Db,
):
    page = svc.create_page(db, user.id, book_id, chapter_id, payload)
    db.commit()
    return page


@router.get(
    "/{book_id}/chapters/{chapter_id}/pages/{page_id}",
    response_model=SoulPageRead,
    summary="Open page",
)
def get_page(
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    page_id: uuid.UUID,
    user: User = CurrentUser,
    db: Session = Db,
):
    return svc.get_page(db, user.id, book_id, chapter_id, page_id)


@router.patch(
    "/{book_id}/chapters/{chapter_id}/pages/{page_id}",
    response_model=SoulPageRead,
    summary="Save page",
)
def update_page(
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    page_id: uuid.UUID,
    payload: SoulPageUpdate,
    user: User = CurrentUser,
    db: Session = Db,
):
    page = svc.update_page(db, user.id, book_id, chapter_id, page_id, payload)
    db.commit()
    return page


@router.patch(
    "/{book_id}/chapters/{chapter_id}/pages/{page_id}/autosave",
    response_model=SoulPageSaveResult,
    summary="Auto-save page",
)
def autosave_page(
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    page_id: uuid.UUID,
    payload: SoulPageAutosave,
    user: User = CurrentUser,
    db: Session = Db,
):
    page = svc.autosave_page(
        db, user.id, book_id, chapter_id, page_id, title=payload.title, content=payload.content
    )
    db.commit()
    return SoulPageSaveResult(
        id=page.id,
        updated_at=page.updated_at,
        word_count=page.word_count,
        character_count=page.character_count,
    )


@router.delete(
    "/{book_id}/chapters/{chapter_id}/pages/{page_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete page",
)
def delete_page(
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    page_id: uuid.UUID,
    user: User = CurrentUser,
    db: Session = Db,
):
    svc.soft_delete_page(db, user.id, book_id, chapter_id, page_id)
    db.commit()
