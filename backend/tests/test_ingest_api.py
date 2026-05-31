"""Ingest API tests with mocked ingest service."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.schemas.ingest import IngestItemResponse


@pytest.mark.asyncio
@patch("app.api.v1.ingest.IngestService")
async def test_ingest_single_alert(mock_service_cls, auth_client):
    mock_service = mock_service_cls.return_value
    mock_service.accept_alert = AsyncMock(
        return_value=IngestItemResponse(
            raw_event_id=uuid4(),
            correlation_id="corr-123",
            pipeline_task_id="celery-task-123",
            status="accepted",
        )
    )

    payload = {
        "title": "Brute Force Attempt",
        "severity": "high",
        "source": "webhook",
        "rule_id": "auth-001",
        "entities": {"src_ip": ["203.0.113.10"]},
    }

    response = await auth_client.post("/api/v1/ingest/alerts", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "accepted"
    assert "correlation_id" in data
    mock_service.accept_alert.assert_called_once()


@pytest.mark.asyncio
@patch("app.api.v1.ingest.IngestService")
async def test_ingest_batch(mock_service_cls, auth_client):
    mock_service = mock_service_cls.return_value
    mock_service.accept_alert = AsyncMock(
        side_effect=[
            IngestItemResponse(
                raw_event_id=uuid4(),
                correlation_id="corr-batch",
                pipeline_task_id="t1",
                status="accepted",
            ),
            IngestItemResponse(
                raw_event_id=uuid4(),
                correlation_id="corr-batch",
                pipeline_task_id="t2",
                status="accepted",
            ),
        ]
    )

    payload = {
        "alerts": [
            {"title": "Alert A", "severity": "low"},
            {"title": "Alert B", "severity": "critical"},
        ]
    }

    response = await auth_client.post("/api/v1/ingest/alerts", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 2
    assert mock_service.accept_alert.call_count == 2


@pytest.mark.asyncio
async def test_ingest_requires_auth():
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/ingest/alerts",
            json={"title": "Unauthorized", "severity": "low"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ingest_validation_error(auth_client):
    response = await auth_client.post("/api/v1/ingest/alerts", json={"severity": "high"})
    assert response.status_code == 422
