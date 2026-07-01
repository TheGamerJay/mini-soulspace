"""Top-level API router that aggregates every route module."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import system

api_router = APIRouter()
api_router.include_router(system.router)
