"""Top-level API router that aggregates every route module."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import auth, legal, system, users

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(legal.router)
