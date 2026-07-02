"""Authentication routes: register, login, refresh, logout, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.auth.cookies import clear_auth_cookies, set_auth_cookies
from app.auth.dependencies import get_current_active_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, MessageResponse, RegisterRequest
from app.schemas.user import UserPreferencesRead, UserRead
from app.services import auth_service, token_service, user_service
from app.utils.rate_limit import check_rate_limit, reset_rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def _auth_response(db: Session, user: User) -> AuthResponse:
    prefs = user_service.get_preferences(db, user)
    return AuthResponse(
        user=UserRead.model_validate(user),
        preferences=UserPreferencesRead.model_validate(prefs),
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    ip = _client_ip(request)
    if not check_rate_limit(
        f"register:{ip}", settings.REGISTER_RATE_LIMIT, settings.REGISTER_RATE_WINDOW_SECONDS
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later.",
        )

    try:
        user = auth_service.register_user(db, payload, ip_address=ip)
    except auth_service.RegistrationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    tokens = token_service.issue_tokens(
        db, user, user_agent=request.headers.get("user-agent"), ip_address=ip
    )
    auth_service.touch_last_login(db, user)
    db.commit()

    set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return _auth_response(db, user)


@router.post("/login", response_model=AuthResponse, summary="Log in")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    ip = _client_ip(request)
    limit_key = f"login:{ip}:{payload.email}"
    if not check_rate_limit(
        limit_key, settings.LOGIN_RATE_LIMIT, settings.LOGIN_RATE_WINDOW_SECONDS
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    user = auth_service.authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    reset_rate_limit(limit_key)
    tokens = token_service.issue_tokens(
        db, user, user_agent=request.headers.get("user-agent"), ip_address=ip
    )
    auth_service.touch_last_login(db, user)
    db.commit()

    set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return _auth_response(db, user)


@router.post("/refresh", response_model=AuthResponse, summary="Rotate tokens")
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    raw_refresh = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not raw_refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        user, tokens = token_service.rotate_tokens(
            db,
            raw_refresh,
            user_agent=request.headers.get("user-agent"),
            ip_address=_client_ip(request),
        )
    except token_service.TokenError:
        db.commit()  # persist any family revocation from reuse detection
        clear_auth_cookies(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    db.commit()
    set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return _auth_response(db, user)


@router.post("/logout", response_model=MessageResponse, summary="Log out")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> MessageResponse:
    raw_refresh = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if raw_refresh:
        token_service.revoke_token(db, raw_refresh)
        db.commit()
    clear_auth_cookies(response)
    return MessageResponse(message="Logged out.")


@router.get("/me", response_model=AuthResponse, summary="Current user")
def me(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AuthResponse:
    return _auth_response(db, user)
