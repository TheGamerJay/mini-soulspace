"""User profile & preferences routes (protected)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    UserPreferencesRead,
    UserPreferencesUpdate,
    UserProfileUpdate,
    UserRead,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead, summary="Get my profile")
def read_me(user: User = Depends(get_current_active_user)) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead, summary="Update my profile")
def update_me(
    payload: UserProfileUpdate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserRead:
    try:
        user = user_service.update_profile(db, user, payload)
    except user_service.ProfileError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    db.commit()
    return UserRead.model_validate(user)


@router.get("/me/preferences", response_model=UserPreferencesRead, summary="Get my preferences")
def read_preferences(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserPreferencesRead:
    prefs = user_service.get_preferences(db, user)
    db.commit()
    return UserPreferencesRead.model_validate(prefs)


@router.patch("/me/preferences", response_model=UserPreferencesRead, summary="Update my preferences")
def update_preferences(
    payload: UserPreferencesUpdate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserPreferencesRead:
    prefs = user_service.update_preferences(db, user, payload)
    db.commit()
    return UserPreferencesRead.model_validate(prefs)
