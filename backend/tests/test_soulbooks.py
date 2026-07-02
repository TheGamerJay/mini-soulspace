"""SoulBook Engine tests: CRUD, archive/restore, pages, autosave, search, sort, ownership."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import valid_registration


def _register(client: TestClient, email: str = "a@example.com") -> None:
    r = client.post("/api/auth/register", json=valid_registration(email=email, display_name="Aria Moon"))
    assert r.status_code == 201, r.text


def _new_book(client: TestClient, title: str = "Personal Journal") -> dict:
    r = client.post("/api/soulbooks", json={"title": title})
    assert r.status_code == 201, r.text
    return r.json()


def _new_chapter(client: TestClient, book_id: str, title: str = "Chapter One") -> dict:
    r = client.post(f"/api/soulbooks/{book_id}/chapters", json={"title": title})
    assert r.status_code == 201, r.text
    return r.json()


def _new_page(client: TestClient, book_id: str, chapter_id: str, title: str = "Day One") -> dict:
    r = client.post(
        f"/api/soulbooks/{book_id}/chapters/{chapter_id}/pages", json={"title": title}
    )
    assert r.status_code == 201, r.text
    return r.json()


# ── SoulBooks ────────────────────────────────────────────────────────────────
def test_create_and_list_book(client):
    _register(client)
    book = _new_book(client, "Dream Journal")
    assert book["title"] == "Dream Journal"
    assert book["chapter_count"] == 0
    listing = client.get("/api/soulbooks").json()
    assert len(listing) == 1


def test_rename_book(client):
    _register(client)
    book = _new_book(client)
    r = client.patch(f"/api/soulbooks/{book['id']}", json={"title": "Gratitude Journal"})
    assert r.status_code == 200
    assert r.json()["title"] == "Gratitude Journal"


def test_archive_restore_book(client):
    _register(client)
    book = _new_book(client)
    assert client.post(f"/api/soulbooks/{book['id']}/archive").json()["is_archived"] is True
    assert len(client.get("/api/soulbooks").json()) == 0  # archived hidden by default
    assert len(client.get("/api/soulbooks?include_archived=true").json()) == 1
    assert client.post(f"/api/soulbooks/{book['id']}/restore").json()["is_archived"] is False
    assert len(client.get("/api/soulbooks").json()) == 1


def test_soft_delete_book(client):
    _register(client)
    book = _new_book(client)
    assert client.delete(f"/api/soulbooks/{book['id']}").status_code == 204
    assert client.get(f"/api/soulbooks/{book['id']}").status_code == 404
    assert len(client.get("/api/soulbooks").json()) == 0


# ── Chapters ─────────────────────────────────────────────────────────────────
def test_create_and_number_chapters(client):
    _register(client)
    book = _new_book(client)
    c1 = _new_chapter(client, book["id"], "First")
    c2 = _new_chapter(client, book["id"], "Second")
    assert c1["chapter_number"] == 1
    assert c2["chapter_number"] == 2


def test_rename_chapter(client):
    _register(client)
    book = _new_book(client)
    chapter = _new_chapter(client, book["id"])
    r = client.patch(
        f"/api/soulbooks/{book['id']}/chapters/{chapter['id']}", json={"title": "Renamed"}
    )
    assert r.status_code == 200 and r.json()["title"] == "Renamed"


# ── Pages ────────────────────────────────────────────────────────────────────
def test_create_page_starts_with_dear_diary(client):
    _register(client)
    book = _new_book(client)
    chapter = _new_chapter(client, book["id"])
    page = _new_page(client, book["id"], chapter["id"])
    assert page["content"].startswith("Dear Diary...")
    assert page["page_number"] == 1
    assert page["content_format"] == "markdown"


def test_save_page_updates_counts(client):
    _register(client)
    book = _new_book(client)
    chapter = _new_chapter(client, book["id"])
    page = _new_page(client, book["id"], chapter["id"])
    r = client.patch(
        f"/api/soulbooks/{book['id']}/chapters/{chapter['id']}/pages/{page['id']}",
        json={"content": "Today was a good day"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["word_count"] == 5
    assert body["character_count"] == len("Today was a good day")


def test_autosave_page(client):
    _register(client)
    book = _new_book(client)
    chapter = _new_chapter(client, book["id"])
    page = _new_page(client, book["id"], chapter["id"])
    r = client.patch(
        f"/api/soulbooks/{book['id']}/chapters/{chapter['id']}/pages/{page['id']}/autosave",
        json={"content": "one two three"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "saved"
    assert body["word_count"] == 3


# ── Search & sort ────────────────────────────────────────────────────────────
def test_search_books_and_pages(client):
    _register(client)
    book = _new_book(client, "Travel Journal")
    chapter = _new_chapter(client, book["id"])
    page = _new_page(client, book["id"], chapter["id"])
    client.patch(
        f"/api/soulbooks/{book['id']}/chapters/{chapter['id']}/pages/{page['id']}",
        json={"content": "wandering through Kyoto temples"},
    )
    by_title = client.get("/api/soulbooks/search?q=travel").json()
    assert len(by_title["books"]) == 1
    by_content = client.get("/api/soulbooks/search?q=kyoto").json()
    assert len(by_content["pages"]) == 1


def test_sorting_alphabetical(client):
    _register(client)
    _new_book(client, "Zeta")
    _new_book(client, "Alpha")
    titles = [b["title"] for b in client.get("/api/soulbooks?sort=alphabetical").json()]
    assert titles == ["Alpha", "Zeta"]


def test_sorting_options_all_ok(client):
    _register(client)
    _new_book(client, "One")
    for sort in ["recently_opened", "recently_updated", "alphabetical", "newest", "oldest"]:
        assert client.get(f"/api/soulbooks?sort={sort}").status_code == 200


# ── Ownership protection ─────────────────────────────────────────────────────
def test_cannot_access_another_users_book(client):
    _register(client, email="owner@example.com")
    book = _new_book(client, "Private")
    chapter = _new_chapter(client, book["id"])

    # Switch identity to a second user.
    client.cookies.clear()
    _register(client, email="intruder@example.com")

    assert client.get(f"/api/soulbooks/{book['id']}").status_code == 404
    assert client.get(f"/api/soulbooks/{book['id']}/chapters").status_code == 404
    assert client.get(f"/api/soulbooks/{book['id']}/chapters/{chapter['id']}").status_code == 404
    assert len(client.get("/api/soulbooks").json()) == 0  # intruder sees nothing


def test_endpoints_require_auth(client):
    assert client.get("/api/soulbooks").status_code == 401
