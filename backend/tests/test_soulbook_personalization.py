"""Phase 4.1 — SoulBook personalization: covers, favorites, categories, ribbons."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import valid_registration


def _register(client: TestClient, email: str = "keepsake@example.com") -> None:
    r = client.post("/api/auth/register", json=valid_registration(email=email, display_name="Aria Moon"))
    assert r.status_code == 201, r.text


def test_create_with_personalization(client):
    _register(client)
    r = client.post(
        "/api/soulbooks",
        json={
            "title": "Dream Journal",
            "cover_color": "#31589e",
            "icon": "🌙",
            "category": "Dreams",
            "ribbon_color": "#c0392b",
            "cover_material": "cloth",
        },
    )
    assert r.status_code == 201, r.text
    book = r.json()
    assert book["cover_color"] == "#31589e"
    assert book["icon"] == "🌙"
    assert book["category"] == "Dreams"
    assert book["ribbon_color"] == "#c0392b"
    assert book["cover_material"] == "cloth"
    assert book["is_favorite"] is False


def test_defaults_are_a_keepsake(client):
    _register(client, email="defaults@example.com")
    book = client.post("/api/soulbooks", json={"title": "Plain"}).json()
    assert book["cover_color"] == "#6d5bd0"
    assert book["cover_material"] == "leather"
    assert book["icon"] == "📔"
    assert book["ribbon_color"] == "#e0b64c"
    assert book["shelf_position"] is None


def test_customize_and_favorite(client):
    _register(client, email="custom@example.com")
    book = client.post("/api/soulbooks", json={"title": "Journal"}).json()
    r = client.patch(
        f"/api/soulbooks/{book['id']}",
        json={"cover_color": "#2e7d4f", "icon": "🧭", "is_favorite": True, "shelf_position": 2},
    )
    assert r.status_code == 200
    updated = r.json()
    assert updated["cover_color"] == "#2e7d4f"
    assert updated["icon"] == "🧭"
    assert updated["is_favorite"] is True
    assert updated["shelf_position"] == 2


def test_favorites_float_to_the_top(client):
    _register(client, email="favsort@example.com")
    client.post("/api/soulbooks", json={"title": "Alpha"})
    b = client.post("/api/soulbooks", json={"title": "Zzz Favorite"}).json()
    client.patch(f"/api/soulbooks/{b['id']}", json={"is_favorite": True})
    titles = [x["title"] for x in client.get("/api/soulbooks?sort=alphabetical").json()]
    assert titles[0] == "Zzz Favorite"  # favorite pin wins over alphabetical
