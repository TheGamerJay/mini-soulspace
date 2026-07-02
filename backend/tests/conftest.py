"""Pytest fixtures: in-memory SQLite database + API client.

Uses portable model types so the full schema builds on SQLite, keeping the test
suite fast and dependency-free (no Docker/Postgres/Redis needed).
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Disable Redis-backed rate limiting for deterministic tests.
settings.RATE_LIMIT_ENABLED = False

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def _schema() -> Generator[None, None, None]:
    """Fresh schema per test."""

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def valid_registration(**overrides) -> dict:
    """A valid registration payload; override individual fields as needed."""

    payload = {
        "display_name": "Aria Moon",
        "email": "aria@example.com",
        "password": "StrongPass123",
        "confirm_password": "StrongPass123",
        "date_of_birth": "1995-05-20",
        "country": "US",
        "region": "California",
        "timezone": "America/Los_Angeles",
        "preferred_language": "en",
        "timezone_auto_detected": True,
        "agreement_accepted": True,
        "agreement_version": "2026-06-30",
    }
    payload.update(overrides)
    return payload
