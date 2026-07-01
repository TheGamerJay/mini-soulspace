"""Smoke tests for the system routes."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_service_metadata() -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["app"] == "Mini SoulSpace"
    assert body["status"] == "running"
    assert body["phase"] == "0"


def test_health_returns_healthy() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
