"""Health endpoint tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1 import health
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint(monkeypatch):
    async def ok_check() -> str:
        return "ok"

    monkeypatch.setattr(health, "_check_database", ok_check)
    monkeypatch.setattr(health, "_check_redis", ok_check)
    monkeypatch.setattr(health, "_check_celery", ok_check)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["checks"] == {
        "database": "ok",
        "redis": "ok",
        "celery": "ok",
    }
    assert data["version"]
