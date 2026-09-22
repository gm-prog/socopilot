"""Regression tests for the investigation timeline API.

Guards against the `event_metadata` <-> `payload` schema/model mismatch that
caused POST /api/v1/alerts/{id}/timeline to raise TypeError (HTTP 500) and
GET /api/v1/alerts/{id}/timeline to silently return null metadata.
"""

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db.models.investigation_event import InvestigationEvent

TIMELINE_BODY = {
    "event_type": "note",
    "title": "Analyst note",
    "description": "Checked with the network team",
    "event_metadata": {"ticket": "INC-1234"},
}


@pytest.fixture
def alert_uuid():
    return uuid.UUID("33333333-3333-3333-3333-333333333333")


@pytest.fixture
def timeline_session(mock_db_session, tenant_id):
    """Session mock where the alert-existence lookup succeeds and refresh
    backfills server-generated fields (id, created_at)."""
    from unittest.mock import AsyncMock

    mock_db_session.flush = AsyncMock()
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = SimpleNamespace(
        id=uuid.UUID("33333333-3333-3333-3333-333333333333")
    )

    def _refresh(obj, *args, **kwargs):
        obj.id = obj.id or uuid.uuid4()
        obj.created_at = obj.created_at or datetime.now(UTC)
        obj.tenant_id = obj.tenant_id or tenant_id

    mock_db_session.refresh = AsyncMock(side_effect=_refresh)
    return mock_db_session


@pytest.mark.asyncio
async def test_create_timeline_event_accepts_event_metadata(
    auth_client, timeline_session, alert_uuid
):
    """The endpoint must map request `event_metadata` onto the model's
    `payload` column instead of passing an invalid kwarg (regression)."""
    resp = await auth_client.post(
        f"/api/v1/alerts/{alert_uuid}/timeline", json=TIMELINE_BODY
    )

    assert resp.status_code == 201, resp.text

    added = timeline_session.add.call_args_list[-1][0][0]
    assert isinstance(added, InvestigationEvent)
    assert added.payload == {"ticket": "INC-1234"}
    assert added.event_metadata == {"ticket": "INC-1234"}  # alias property works


@pytest.mark.asyncio
async def test_get_timeline_maps_payload_and_user_id(auth_client, tenant_id, alert_uuid):
    """GET must expose the ORM `payload`/`user_id` columns through the API's
    `event_metadata`/`created_by` fields instead of nulls."""
    user_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    orm_event = InvestigationEvent(
        tenant_id=tenant_id,
        alert_id=alert_uuid,
        event_type="note",
        title="Analyst note",
        payload={"k": "v"},
        user_id=user_id,
    )
    orm_event.id = uuid.uuid4()
    orm_event.created_at = datetime.now(UTC)

    result_alert = MagicMock()
    result_alert.scalar_one_or_none.return_value = SimpleNamespace(id=alert_uuid)
    result_events = MagicMock()
    result_events.scalars.return_value.all.return_value = [orm_event]
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[result_alert, result_events])

    from app.api.v1.alerts import get_alert_timeline

    user = SimpleNamespace(tenant_id=tenant_id, id=user_id)
    events = await get_alert_timeline(alert_id=alert_uuid, current_user=user, db=db)

    assert len(events) == 1
    assert events[0].event_metadata == {"k": "v"}
    assert events[0].created_by == user_id
