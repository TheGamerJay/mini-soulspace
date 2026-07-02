"""User & preferences schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class UserPreferencesRead(BaseModel):
    """Public representation of a user's preferences."""

    model_config = ConfigDict(from_attributes=True)

    birthday_messages_enabled: bool
    milestone_messages_enabled: bool
    reflection_reminders_enabled: bool
    preferred_theme: str
    timezone_auto_detected: bool


class UserRead(BaseModel):
    """Safe, public representation of a user (never includes the password)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str
    date_of_birth: date
    country: str
    region: str
    timezone: str
    preferred_language: str
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None
    created_at: datetime


class UserProfileUpdate(BaseModel):
    """Editable profile fields. All optional (partial update)."""

    display_name: str | None = Field(default=None, min_length=2, max_length=50)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    region: str | None = Field(default=None, min_length=1, max_length=100)
    timezone: str | None = Field(default=None, max_length=64)
    preferred_language: str | None = Field(default=None, max_length=10)


class UserPreferencesUpdate(BaseModel):
    """Editable preference fields (partial update)."""

    birthday_messages_enabled: bool | None = None
    milestone_messages_enabled: bool | None = None
    reflection_reminders_enabled: bool | None = None
    preferred_theme: str | None = Field(default=None, max_length=20)
    timezone_auto_detected: bool | None = None
