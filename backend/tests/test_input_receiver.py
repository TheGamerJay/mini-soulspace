"""Input Receiver node tests — aims for full branch coverage of app.orchestra."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.orchestra.errors import InputValidationError
from app.orchestra.input_receiver import (
    _validate_facts,
    _validate_relationships,
    build_orchestra_request,
)
from app.orchestra.schemas import SCHEMA_VERSION, OrchestraRequest
from app.schemas.auth import RegisterRequest
from app.schemas.soulbook import SoulBookCreate, SoulChapterCreate, SoulPageCreate
from app.services import auth_service
from app.services import soulbook_service as svc
from tests.conftest import valid_registration


def _make_user(db, email="a@example.com"):
    user = auth_service.register_user(db, RegisterRequest(**valid_registration(email=email)))
    db.commit()
    return user


def _make_page(db, user, content=None):
    book = svc.create_book(db, user.id, SoulBookCreate(title="Personal Journal"))
    chapter = svc.create_chapter(db, user.id, book.id, SoulChapterCreate(title="Chapter One"))
    page = svc.create_page(db, user.id, book.id, chapter.id, SoulPageCreate(title="Day 1", content=content))
    db.commit()
    return book, chapter, page


# ── Happy path ────────────────────────────────────────────────────────────────
def test_builds_immutable_versioned_request(db):
    user = _make_user(db)
    book, chapter, page = _make_page(db, user, content="one two three")

    req = build_orchestra_request(
        db, user, book.id, chapter.id, page.id, session_id="s1", metadata={"foo": "bar"}
    )

    assert isinstance(req, OrchestraRequest)
    assert req.schema_version == SCHEMA_VERSION == "1.0"
    assert req.user.id == user.id
    assert req.book.id == book.id
    assert req.chapter.chapter_number == 1
    assert req.page.id == page.id
    assert req.page_content == "one two three"
    assert req.statistics.word_count == 3
    assert req.statistics.character_count == len("one two three")
    assert req.language == user.preferred_language
    assert req.timezone == user.timezone  # page tz is None -> falls back to user tz
    assert req.session.session_id == "s1"
    assert req.metadata["book_type"] == book.cover_style
    assert req.metadata["foo"] == "bar"


def test_request_is_read_only(db):
    user = _make_user(db)
    book, chapter, page = _make_page(db, user)
    req = build_orchestra_request(db, user, book.id, chapter.id, page.id)
    with pytest.raises(Exception):
        req.language = "changed"  # type: ignore[misc]


def test_dear_diary_default_content_and_stats(db):
    user = _make_user(db)
    book, chapter, page = _make_page(db, user)  # default "Dear Diary...\n\n"
    req = build_orchestra_request(db, user, book.id, chapter.id, page.id)
    assert req.page_content.startswith("Dear Diary...")
    assert req.statistics.character_count == len(req.page_content)


# ── Validation failures ───────────────────────────────────────────────────────
def test_missing_user():
    with pytest.raises(InputValidationError) as e:
        build_orchestra_request(None, None, uuid.uuid4(), uuid.uuid4(), uuid.uuid4())  # type: ignore[arg-type]
    assert e.value.errors[0]["code"] == "missing_user"


def test_missing_book(db):
    user = _make_user(db)
    with pytest.raises(InputValidationError) as e:
        build_orchestra_request(db, user, uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
    assert e.value.errors[0]["code"] == "book_not_found"


def test_missing_chapter(db):
    user = _make_user(db)
    book, _chapter, _page = _make_page(db, user)
    with pytest.raises(InputValidationError) as e:
        build_orchestra_request(db, user, book.id, uuid.uuid4(), uuid.uuid4())
    assert e.value.errors[0]["code"] == "chapter_not_found"


def test_missing_page(db):
    user = _make_user(db)
    book, chapter, _page = _make_page(db, user)
    with pytest.raises(InputValidationError) as e:
        build_orchestra_request(db, user, book.id, chapter.id, uuid.uuid4())
    assert e.value.errors[0]["code"] == "page_not_found"


def test_wrong_ownership(db):
    owner = _make_user(db, email="owner@example.com")
    book, chapter, page = _make_page(db, owner)
    intruder = _make_user(db, email="intruder@example.com")
    with pytest.raises(InputValidationError) as e:
        build_orchestra_request(db, intruder, book.id, chapter.id, page.id)
    assert e.value.errors[0]["code"] == "book_not_found"


def test_missing_language(db):
    user = _make_user(db)
    book, chapter, page = _make_page(db, user)
    user.preferred_language = ""
    with pytest.raises(InputValidationError) as e:
        build_orchestra_request(db, user, book.id, chapter.id, page.id)
    assert any(err["code"] == "missing_language" for err in e.value.errors)


def test_missing_timezone(db):
    user = _make_user(db)
    book, chapter, page = _make_page(db, user)
    user.timezone = ""  # page tz is None too -> unresolved
    with pytest.raises(InputValidationError) as e:
        build_orchestra_request(db, user, book.id, chapter.id, page.id)
    assert any(err["code"] == "missing_timezone" for err in e.value.errors)


# ── Pure validators (defensive branches) ──────────────────────────────────────
def test_validate_relationships_detects_corruption():
    book = SimpleNamespace(id=1)
    chapter = SimpleNamespace(id=2, book_id=999)
    page = SimpleNamespace(id=3, book_id=999, chapter_id=999)
    errors = _validate_relationships(book, chapter, page)
    assert len(errors) == 3
    assert all(err["code"] == "corrupted_relationship" for err in errors)


def test_validate_relationships_ok():
    book = SimpleNamespace(id=1)
    chapter = SimpleNamespace(id=2, book_id=1)
    page = SimpleNamespace(id=3, book_id=1, chapter_id=2)
    assert _validate_relationships(book, chapter, page) == []


def test_validate_facts_all_missing():
    page = SimpleNamespace(content=None)
    errors = _validate_facts(page, "", "")
    codes = {err["code"] for err in errors}
    assert codes == {"missing_content", "missing_language", "missing_timezone"}


def test_validate_facts_ok():
    page = SimpleNamespace(content="hello")
    assert _validate_facts(page, "en", "UTC") == []
