"""Authentication business logic: registration and credential checks."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.legal.content import LEGAL_VERSION
from app.models.auth import AgreementDocument, UserAgreement
from app.models.preferences import UserPreferences
from app.models.user import User
from app.schemas.auth import RegisterRequest


class RegistrationError(Exception):
    """Raised when an account cannot be created."""


def get_user_by_email(db: Session, email: str) -> User | None:
    """Case-insensitive lookup by normalized email."""

    return db.execute(
        select(User).where(func.lower(User.email) == email.lower())
    ).scalar_one_or_none()


def register_user(db: Session, payload: RegisterRequest, *, ip_address: str | None = None) -> User:
    """Create a user, their preferences, and audit their agreement acceptance.

    The schema already enforced ``agreement_accepted``; we defend again here so
    the service is safe regardless of caller.
    """

    if not payload.agreement_accepted:
        raise RegistrationError("Agreement must be accepted.")

    if get_user_by_email(db, payload.email) is not None:
        # Generic error message to avoid account enumeration.
        raise RegistrationError("An account could not be created with those details.")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        date_of_birth=payload.date_of_birth,
        country=payload.country,
        region=payload.region,
        timezone=payload.timezone,
        preferred_language=payload.preferred_language,
    )
    db.add(user)
    db.flush()  # assign user.id

    db.add(
        UserPreferences(
            user_id=user.id,
            timezone_auto_detected=payload.timezone_auto_detected,
        )
    )

    # Record acceptance of every document the combined checkbox covers.
    accepted_at = datetime.now(timezone.utc)
    for document in AgreementDocument:
        db.add(
            UserAgreement(
                user_id=user.id,
                document=document,
                version=LEGAL_VERSION,
                accepted_at=accepted_at,
                ip_address=ip_address,
            )
        )

    db.flush()
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the user if credentials are valid and the account is active."""

    user = get_user_by_email(db, email)
    if user is None:
        # Still run a hash to reduce timing signal, then fail.
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


def touch_last_login(db: Session, user: User) -> None:
    user.last_login_at = datetime.now(timezone.utc)
    db.flush()


# Pre-computed dummy hash to equalize timing when the email doesn't exist.
_DUMMY_HASH = hash_password("timing-equalizer-not-a-real-password")
