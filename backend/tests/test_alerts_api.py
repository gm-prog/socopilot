"""Alerts list API tests with mocked repository."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.db.models.normalized_alert import NormalizedAlert


@pytest.mark.asyncio
@patch("app.api.v1.alerts.AlertRepository")
async def test_list_alerts(mock_repo_cls, auth_client):
    alert_id = uuid4()
    now = datetime.now(UTC)
    mock_alert = NormalizedAlert(
        id=alert_id,
        tenant_id=uuid4(),
        fingerprint="abc" * 21 + "a",
        time_bucket="2026-05-26T12:00:00Z",
        source="webhook",
        title="Test",
        severity="high",
        status="NORMALIZED",
        detected_at=now,
        ingested_at=now,
        last_seen_at=now,
        duplicate_count=1,
        normalized_payload={},
        lifecycle_state="new",
        tags=[],
    )
    mock_repo = AsyncMock()
    mock_repo.list_alerts.return_value = ([mock_alert], 1)
    mock_repo_cls.return_value = mock_repo

    response = await auth_client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Test"
