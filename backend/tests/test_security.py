"""Unit tests for security primitives (no DB)."""

from __future__ import annotations

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def test_password_hash_roundtrip():
    h = hash_password("StrongPass123")
    assert h != "StrongPass123"
    assert verify_password("StrongPass123", h)
    assert not verify_password("WrongPass123", h)


def test_access_token_roundtrip():
    token = create_access_token("user-123")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_decode_rejects_non_access_token():
    # A refresh-typed JWT must not validate as an access token.
    bad = jwt.encode({"sub": "x", "type": "refresh"}, settings.SECRET_KEY, algorithm="HS256")
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(bad)


def test_refresh_token_hash_is_deterministic_and_opaque():
    raw = generate_refresh_token()
    assert hash_refresh_token(raw) == hash_refresh_token(raw)
    assert raw not in hash_refresh_token(raw)
