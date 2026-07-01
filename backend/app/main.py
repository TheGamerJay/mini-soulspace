"""Mini SoulSpace — FastAPI application entry point.

Creates and configures the ASGI application. Kept intentionally thin: wiring
only. Business logic lives in ``app.services`` and ``app.brains``.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


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
    return app


app = create_app()
