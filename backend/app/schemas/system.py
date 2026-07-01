"""Pydantic schemas for system routes."""

from __future__ import annotations

from pydantic import BaseModel


class RootResponse(BaseModel):
    """Response body for ``GET /``."""

    app: str
    status: str
    phase: str


class HealthResponse(BaseModel):
    """Response body for ``GET /health`` (liveness)."""

    status: str


class ReadinessResponse(BaseModel):
    """Response body for ``GET /health/ready`` (readiness).

    ``status`` is ``ready`` when every dependency check passes, otherwise
    ``degraded``. ``checks`` maps each dependency to ``ok`` or an error label.
    """

    status: str
    checks: dict[str, str]
