"""Helpers for setting and clearing the httpOnly auth cookies."""

from __future__ import annotations

from fastapi import Response

from app.core.config import settings


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Attach the access + refresh tokens as httpOnly cookies."""

    response.set_cookie(
        key=settings.ACCESS_COOKIE_NAME,
        value=access_token,
        max_age=settings.ACCESS_TOKEN_TTL_MINUTES * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_TTL_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        domain=settings.COOKIE_DOMAIN,
        path=settings.REFRESH_COOKIE_PATH,
    )


def clear_auth_cookies(response: Response) -> None:
    """Remove both auth cookies (logout)."""

    response.delete_cookie(
        key=settings.ACCESS_COOKIE_NAME,
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        domain=settings.COOKIE_DOMAIN,
        path=settings.REFRESH_COOKIE_PATH,
    )
