"""System-level routes: service metadata and health checks."""

from __future__ import annotations

import redis
from fastapi import APIRouter, Response
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import engine
from app.schemas.system import HealthResponse, ReadinessResponse, RootResponse

logger = get_logger(__name__)

router = APIRouter(tags=["system"])


@router.get("/", response_model=RootResponse, summary="Service metadata")
def read_root() -> RootResponse:
    """Return basic information about the running service."""

    return RootResponse(
        app=settings.APP_NAME,
        status="running",
        phase=settings.APP_PHASE,
    )


@router.get("/health", response_model=HealthResponse, summary="Liveness check")
def health_check() -> HealthResponse:
    """Lightweight liveness probe used by orchestrators and uptime checks.

    Has no external dependencies, so it stays green as long as the process is
    up — this is the endpoint platform health checks should target.
    """

    return HealthResponse(status="healthy")


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness check (database + redis)",
)
def readiness_check(response: Response) -> ReadinessResponse:
    """Verify connectivity to every backing service.

    Returns HTTP 200 when all checks pass and HTTP 503 when any dependency is
    unreachable, so it doubles as a deployment verification endpoint.
    """

    checks: dict[str, str] = {}
    all_ok = True

    # --- PostgreSQL ----------------------------------------------------------
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001 - report, never crash the probe
        logger.warning("Database readiness check failed: %s", exc)
        checks["database"] = f"error: {type(exc).__name__}"
        all_ok = False

    # --- Redis ---------------------------------------------------------------
    try:
        client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=3)
        client.ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001 - report, never crash the probe
        logger.warning("Redis readiness check failed: %s", exc)
        checks["redis"] = f"error: {type(exc).__name__}"
        all_ok = False

    response.status_code = 200 if all_ok else 503
    return ReadinessResponse(status="ready" if all_ok else "degraded", checks=checks)
