"""Authentication request/response schemas with server-side validation."""

from __future__ import annotations

import re
from datetime import date
from zoneinfo import available_timezones

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.core.config import settings
from app.schemas.user import UserPreferencesRead, UserRead

_VALID_TIMEZONES = available_timezones()
_PASSWORD_MIN_LENGTH = 12
_PASSWORD_MAX_LENGTH = 128
_LANGUAGE_RE = re.compile(r"^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{2,8})?$")


def validate_password_strength(value: str) -> str:
    """Enforce the password policy (shared by register + future change-password)."""

    if len(value) < _PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {_PASSWORD_MIN_LENGTH} characters.")
    if len(value) > _PASSWORD_MAX_LENGTH:
        raise ValueError(f"Password must be at most {_PASSWORD_MAX_LENGTH} characters.")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain a lowercase letter.")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain an uppercase letter.")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain a number.")
    return value


def _calculate_age(dob: date, today: date | None = None) -> int:
    today = today or date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class RegisterRequest(BaseModel):
    """Registration payload — every field is validated server-side."""

    display_name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str
    confirm_password: str
    date_of_birth: date
    country: str = Field(min_length=2, max_length=2)
    region: str = Field(min_length=1, max_length=100)
    timezone: str = Field(max_length=64)
    preferred_language: str = Field(max_length=10)
    timezone_auto_detected: bool = True

    # Single combined agreement (Acknowledgment + ToS + Privacy).
    agreement_accepted: bool
    agreement_version: str = Field(max_length=20)

    @field_validator("display_name")
    @classmethod
    def _clean_display_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Display name must be at least 2 characters.")
        return v

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return validate_password_strength(v)

    @field_validator("country")
    @classmethod
    def _upper_country(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("timezone")
    @classmethod
    def _check_timezone(cls, v: str) -> str:
        v = v.strip()
        if v not in _VALID_TIMEZONES:
            raise ValueError("Invalid timezone.")
        return v

    @field_validator("preferred_language")
    @classmethod
    def _check_language(cls, v: str) -> str:
        v = v.strip()
        if not _LANGUAGE_RE.match(v):
            raise ValueError("Invalid language code.")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def _check_dob(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future.")
        if settings.min_age_enabled and _calculate_age(v) < settings.MIN_SIGNUP_AGE:
            raise ValueError(f"You must be at least {settings.MIN_SIGNUP_AGE} years old.")
        return v

    @model_validator(mode="after")
    def _check_rules(self) -> RegisterRequest:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        if not self.agreement_accepted:
            raise ValueError("You must accept the agreement to create an account.")
        return self


class LoginRequest(BaseModel):
    """Login payload."""

    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class AuthResponse(BaseModel):
    """Returned after successful register/login and from /auth/me."""

    user: UserRead
    preferences: UserPreferencesRead


class MessageResponse(BaseModel):
    """Generic message envelope."""

    message: str
