"""User profile & preferences operations."""

from __future__ import annotations

from zoneinfo import available_timezones

from sqlalchemy.orm import Session

from app.models.preferences import UserPreferences
from app.models.user import User
from app.schemas.user import UserPreferencesUpdate, UserProfileUpdate

_VALID_TIMEZONES = available_timezones()


class ProfileError(Exception):
    """Raised on invalid profile updates."""


def get_preferences(db: Session, user: User) -> UserPreferences:
    """Return the user's preferences, creating defaults if missing."""

    if user.preferences is not None:
        return user.preferences
    prefs = UserPreferences(user_id=user.id)
    db.add(prefs)
    db.flush()
    return prefs


def update_profile(db: Session, user: User, payload: UserProfileUpdate) -> User:
    data = payload.model_dump(exclude_unset=True)
    if "timezone" in data and data["timezone"] not in _VALID_TIMEZONES:
        raise ProfileError("Invalid timezone.")
    if "country" in data and data["country"]:
        data["country"] = data["country"].upper()
    if "display_name" in data and data["display_name"]:
        data["display_name"] = data["display_name"].strip()
    for key, value in data.items():
        setattr(user, key, value)
    db.flush()
    return user


def update_preferences(
    db: Session, user: User, payload: UserPreferencesUpdate
) -> UserPreferences:
    prefs = get_preferences(db, user)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(prefs, key, value)
    db.flush()
    return prefs
