"""Security primitives: password hashing, JWT, and token generation.

Kept dependency-light and side-effect free so it is trivially unit-testable.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

# Argon2id (argon2-cffi defaults to the id variant) with sensible cost params.
_password_hasher = PasswordHasher()

# Guard against absurdly long passwords (DoS on the hasher).
MAX_PASSWORD_LENGTH = 128


# --- Password hashing --------------------------------------------------------
def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id."""

    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against an Argon2id hash (constant-time)."""

    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:  # malformed hash, etc.
        return False


def needs_rehash(password_hash: str) -> bool:
    """Whether a stored hash should be upgraded to current parameters."""

    return _password_hasher.check_needs_rehash(password_hash)


# --- JWT access tokens -------------------------------------------------------
def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    """Create a signed, short-lived JWT access token for ``subject`` (user id)."""

    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.ACCESS_TOKEN_TTL_MINUTES)).timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an access token. Raises ``jwt.PyJWTError`` on failure."""

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Not an access token")
    return payload


# --- Opaque refresh tokens ---------------------------------------------------
def generate_refresh_token() -> str:
    """Generate a cryptographically strong opaque refresh token."""

    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token for at-rest storage (SHA-256, never store raw)."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()
