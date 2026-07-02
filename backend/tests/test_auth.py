"""Authentication flow tests: registration, agreement gate, login, logout, refresh."""

from __future__ import annotations

from app.core.config import settings
from tests.conftest import valid_registration


def test_register_success_sets_cookies(client):
    res = client.post("/api/auth/register", json=valid_registration())
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["user"]["email"] == "aria@example.com"
    assert body["user"]["region"] == "California"
    assert body["preferences"]["timezone_auto_detected"] is True
    assert settings.ACCESS_COOKIE_NAME in res.cookies
    assert settings.REFRESH_COOKIE_NAME in res.cookies


def test_register_missing_agreement_rejected(client):
    res = client.post(
        "/api/auth/register", json=valid_registration(agreement_accepted=False)
    )
    assert res.status_code == 422


def test_register_password_mismatch_rejected(client):
    res = client.post(
        "/api/auth/register", json=valid_registration(confirm_password="Different123")
    )
    assert res.status_code == 422


def test_register_weak_password_rejected(client):
    res = client.post(
        "/api/auth/register",
        json=valid_registration(password="weak", confirm_password="weak"),
    )
    assert res.status_code == 422


def test_register_underage_rejected(client):
    res = client.post(
        "/api/auth/register", json=valid_registration(date_of_birth="2018-01-01")
    )
    assert res.status_code == 422


def test_min_age_is_configurable(client, monkeypatch):
    # Disable the age gate -> an otherwise-underage DOB is accepted.
    monkeypatch.setattr(settings, "MIN_SIGNUP_AGE", 0)
    res = client.post(
        "/api/auth/register", json=valid_registration(date_of_birth="2018-01-01")
    )
    assert res.status_code == 201, res.text


def test_register_invalid_timezone_rejected(client):
    res = client.post(
        "/api/auth/register", json=valid_registration(timezone="Mars/Olympus")
    )
    assert res.status_code == 422


def test_register_duplicate_email_rejected(client):
    client.post("/api/auth/register", json=valid_registration())
    res = client.post(
        "/api/auth/register", json=valid_registration(display_name="Someone Else")
    )
    assert res.status_code == 409


def test_login_success(client):
    client.post("/api/auth/register", json=valid_registration())
    client.cookies.clear()
    res = client.post(
        "/api/auth/login",
        json={"email": "aria@example.com", "password": "StrongPass123"},
    )
    assert res.status_code == 200
    assert settings.ACCESS_COOKIE_NAME in res.cookies


def test_login_wrong_password(client):
    client.post("/api/auth/register", json=valid_registration())
    client.cookies.clear()
    res = client.post(
        "/api/auth/login",
        json={"email": "aria@example.com", "password": "WrongPass123"},
    )
    assert res.status_code == 401


def test_me_requires_authentication(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_returns_current_user(client):
    client.post("/api/auth/register", json=valid_registration())
    res = client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json()["user"]["email"] == "aria@example.com"


def test_logout_clears_session(client):
    client.post("/api/auth/register", json=valid_registration())
    assert client.get("/api/auth/me").status_code == 200
    res = client.post("/api/auth/logout")
    assert res.status_code == 200
    client.cookies.clear()
    assert client.get("/api/auth/me").status_code == 401


def test_refresh_rotates_tokens(client):
    client.post("/api/auth/register", json=valid_registration())
    res = client.post("/api/auth/refresh")
    assert res.status_code == 200
    assert settings.ACCESS_COOKIE_NAME in res.cookies


def test_protected_profile_requires_auth(client):
    assert client.get("/api/users/me").status_code == 401


def test_profile_update(client):
    client.post("/api/auth/register", json=valid_registration())
    res = client.patch("/api/users/me", json={"region": "New York", "timezone": "America/New_York"})
    assert res.status_code == 200
    assert res.json()["region"] == "New York"
    assert res.json()["timezone"] == "America/New_York"


def test_legal_agreement_endpoint(client):
    res = client.get("/api/legal/agreement")
    assert res.status_code == 200
    body = res.json()
    assert body["version"]
    assert "Acknowledgment" in body["content"]
    assert "agree" in body["checkbox_label"].lower()
