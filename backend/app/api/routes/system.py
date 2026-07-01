"""System-level routes: service metadata and health checks."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.system import HealthResponse, RootResponse

router = APIRouter(tags=["system"])


@router.get("/", response_model=RootResponse, summary="Service metadata")
def read_root() -> RootResponse:
    """Return basic information about the running service."""

    return RootResponse(
        app=settings.APP_NAME,
        status="running",
        phase=settings.APP_PHASE,
    )


@router.get("/health", response_model=HealthResponse, summary="Health check")
def health_check() -> HealthResponse:
    """Lightweight liveness probe used by orchestrators and uptime checks."""

    return HealthResponse(status="healthy")
