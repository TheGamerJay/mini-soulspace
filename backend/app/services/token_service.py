"""Refresh-session lifecycle: issue, rotate, revoke, reuse-detection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.models.auth import RefreshSession
from app.models.user import User

logger = get_logger(__name__)


class TokenError(Exception):
    """Raised when a refresh token is missing, invalid, expired or reused."""


@dataclass
class IssuedTokens:
    access_token: str
    refresh_token: str  # raw token (only returned here, then set as a cookie)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(dt: datetime) -> datetime:
    """Coerce a possibly-naive datetime (e.g. from SQLite) to UTC-aware."""

    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def issue_tokens(
    db: Session,
    user: User,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> IssuedTokens:
    """Create a new refresh session and matching access token for ``user``."""

    raw_refresh = generate_refresh_token()
    session = RefreshSession(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=_now() + timedelta(days=settings.REFRESH_TOKEN_TTL_DAYS),
        user_agent=(user_agent or "")[:400] or None,
        ip_address=ip_address,
    )
    db.add(session)
    db.flush()

    access = create_access_token(str(user.id))
    return IssuedTokens(access_token=access, refresh_token=raw_refresh)


def _revoke_all_for_user(db: Session, user_id) -> None:
    db.execute(
        update(RefreshSession)
        .where(RefreshSession.user_id == user_id, RefreshSession.revoked_at.is_(None))
        .values(revoked_at=_now())
    )


def rotate_tokens(
    db: Session,
    raw_refresh: str,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[User, IssuedTokens]:
    """Validate a refresh token and rotate it. Raises ``TokenError`` on failure."""

    token_hash = hash_refresh_token(raw_refresh)
    session = db.execute(
        select(RefreshSession).where(RefreshSession.token_hash == token_hash)
    ).scalar_one_or_none()

    if session is None:
        raise TokenError("Unknown refresh token")

    # Reuse of an already-revoked token => likely theft. Revoke the whole family.
    if session.revoked_at is not None:
        logger.warning("Refresh token reuse detected for user %s; revoking sessions", session.user_id)
        _revoke_all_for_user(db, session.user_id)
        raise TokenError("Refresh token already used")

    if _as_aware(session.expires_at) <= _now():
        raise TokenError("Refresh token expired")

    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise TokenError("User unavailable")

    new_tokens = issue_tokens(db, user, user_agent=user_agent, ip_address=ip_address)
    # Link rotation chain and revoke the old session.
    new_session = db.execute(
        select(RefreshSession).where(
            RefreshSession.token_hash == hash_refresh_token(new_tokens.refresh_token)
        )
    ).scalar_one()
    session.revoked_at = _now()
    session.replaced_by = new_session.id
    db.flush()
    return user, new_tokens


def revoke_token(db: Session, raw_refresh: str) -> None:
    """Revoke a single refresh session (logout). No-op if not found."""

    if not raw_refresh:
        return
    session = db.execute(
        select(RefreshSession).where(
            RefreshSession.token_hash == hash_refresh_token(raw_refresh)
        )
    ).scalar_one_or_none()
    if session is not None and session.revoked_at is None:
        session.revoked_at = _now()
        db.flush()
