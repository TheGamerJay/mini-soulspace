"""Mini SoulSpace — FastAPI application entry point.

Creates and configures the ASGI application. Kept intentionally thin: wiring
only. Business logic lives in ``app.services`` and ``app.brains``.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)

# Directory holding the built frontend (Next.js static export). Populated by the
# unified Docker image; absent during local backend-only development.
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""

    configure_logging()
    logger.info(
        "Starting %s (phase %s, env=%s)",
        settings.APP_NAME,
        settings.APP_PHASE,
        settings.ENVIRONMENT,
    )
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


def create_app() -> FastAPI:
    """Application factory."""

    app = FastAPI(
        title=settings.APP_NAME,
        description="An AI-powered personal SoulDiary — a diary that talks back.",
        version=f"phase-{settings.APP_PHASE}",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_PREFIX)

    # Serve the built frontend at the root. Registered last so it acts as a
    # catch-all fallback while explicit /api routes still take priority.
    if STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
        logger.info("Serving frontend static build from %s", STATIC_DIR)
    else:
        logger.info("No frontend build found at %s (API-only mode)", STATIC_DIR)

    return app


app = create_app()
