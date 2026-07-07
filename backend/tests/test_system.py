"""Smoke tests for the system routes (served under the /api prefix)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_service_metadata() -> None:
    response = client.get("/api/")
    assert response.status_code == 200
    body = response.json()
    assert body["app"] == "Mini SoulSpace"
    assert body["status"] == "running"
    assert body["phase"] == "4.0"


def test_health_returns_healthy() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_readiness_reports_dependency_checks() -> None:
    # Without live datastores this returns 503 (degraded); with them, 200 (ready).
    # Either way the contract (status + per-dependency checks) must hold.
    response = client.get("/api/health/ready")
    assert response.status_code in (200, 503)
    body = response.json()
    assert body["status"] in ("ready", "degraded")
    assert "database" in body["checks"]
    assert "redis" in body["checks"]
