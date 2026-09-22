"""Alerts list API tests with mocked repository."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch, MagicMock
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


@pytest.mark.asyncio
@patch("app.api.v1.alerts.AlertRepository")
async def test_get_alert_not_found(mock_repo_cls, auth_client):
    mock_repo = AsyncMock()
    mock_repo.get_alert.return_value = None
    mock_repo_cls.return_value = mock_repo

    response = await auth_client.get(f"/api/v1/alerts/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Alert not found"


@pytest.mark.asyncio
@patch("app.api.v1.alerts.AlertRepository")
async def test_get_alert_success_with_raw_and_iocs(mock_repo_cls, auth_client, mock_db_session):
    alert_id = uuid4()
    tenant_id = uuid4()
    raw_event_id = uuid4()
    now = datetime.now(UTC)

    mock_alert = NormalizedAlert(
        id=alert_id,
        tenant_id=tenant_id,
        raw_event_id=raw_event_id,
        fingerprint="a" * 64,
        time_bucket="2026-05-26T12:00:00Z",
        source="webhook",
        title="Test Alert",
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
    mock_repo.get_alert.return_value = mock_alert
    mock_repo_cls.return_value = mock_repo

    mock_raw = AsyncMock()
    mock_raw.payload = {"event": "details"}
    
    mock_ioc = AsyncMock()
    mock_ioc.id = uuid4()
    mock_ioc.alert_id = alert_id
    mock_ioc.tenant_id = tenant_id
    mock_ioc.ioc_type = "ip"
    mock_ioc.ioc_value = "192.168.1.1"

    async def mock_execute(query):
        res = MagicMock()
        query_str = str(query)
        if "raw_event" in query_str.lower():
            res.scalar_one_or_none.return_value = mock_raw
        else:
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = [mock_ioc]
            res.scalars.return_value = scalars_mock
        return res

    mock_db_session.execute = AsyncMock(side_effect=mock_execute)

    response = await auth_client.get(f"/api/v1/alerts/{alert_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_alert_workflow_not_found(auth_client, mock_db_session):
    res = MagicMock()
    res.scalar_one_or_none.return_value = None
    mock_db_session.execute = AsyncMock(return_value=res)

    response = await auth_client.patch(
        f"/api/v1/alerts/{uuid4()}",
        json={"lifecycle_state": "resolved"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_alert_timeline_not_found(auth_client, mock_db_session):
    res = MagicMock()
    res.scalar_one_or_none.return_value = None
    mock_db_session.execute = AsyncMock(return_value=res)

    response = await auth_client.get(f"/api/v1/alerts/{uuid4()}/timeline")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_alert_timeline_event_not_found(auth_client, mock_db_session):
    res = MagicMock()
    res.scalar_one_or_none.return_value = None
    mock_db_session.execute = AsyncMock(return_value=res)

    payload = {
        "event_type": "note",
        "title": "Test Title",
        "description": "Test Desc",
        "event_metadata": {}
    }
    response = await auth_client.post(f"/api/v1/alerts/{uuid4()}/timeline", json=payload)
    assert response.status_code == 404
