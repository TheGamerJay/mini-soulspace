"""Pydantic schemas for system routes."""

from __future__ import annotations

from pydantic import BaseModel


class RootResponse(BaseModel):
    """Response body for ``GET /``."""

    app: str
    status: str
    phase: str


class HealthResponse(BaseModel):
    """Response body for ``GET /health``."""

    status: str
