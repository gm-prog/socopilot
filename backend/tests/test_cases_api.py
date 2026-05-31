"""Cases API tests with mocked repository."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.db.models.case import Case
from app.db.models.case_alert import CaseAlert


@pytest.mark.asyncio
@patch("app.api.v1.cases.CaseRepository")
async def test_create_case(mock_repo_cls, auth_client, tenant_id):
    case_id = uuid4()
    alert_id = uuid4()
    now = datetime.now(UTC)
    mock_case = Case(
        id=case_id,
        tenant_id=tenant_id,
        title="Investigate phishing alert",
        description="Created from alert triage",
        severity="high",
        status="open",
        created_at=now,
        updated_at=now,
    )
    mock_case.case_alerts = [CaseAlert(alert_id=alert_id)]

    mock_repo = AsyncMock()
    mock_repo.create_case.return_value = mock_case
    mock_repo_cls.return_value = mock_repo

    response = await auth_client.post(
        "/api/v1/cases",
        json={
            "title": "Investigate phishing alert",
            "description": "Created from alert triage",
            "severity": "high",
            "status": "open",
            "alert_ids": [str(alert_id)],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == str(case_id)
    assert data["tenant_id"] == str(tenant_id)
    assert data["title"] == "Investigate phishing alert"
    assert data["alert_ids"] == [str(alert_id)]
    mock_repo.create_case.assert_awaited_once()
    assert mock_repo.create_case.await_args.args[0] == tenant_id


@pytest.mark.asyncio
@patch("app.api.v1.cases.CaseRepository")
async def test_list_cases(mock_repo_cls, auth_client, tenant_id):
    now = datetime.now(UTC)
    case_id = uuid4()
    alert_id = uuid4()
    mock_case = Case(
        id=case_id,
        tenant_id=tenant_id,
        title="Review endpoint activity",
        description=None,
        severity="medium",
        status="investigating",
        created_at=now,
        updated_at=now,
    )
    mock_case.case_alerts = [CaseAlert(alert_id=alert_id)]

    mock_repo = AsyncMock()
    mock_repo.list_cases.return_value = ([mock_case], 1)
    mock_repo_cls.return_value = mock_repo

    response = await auth_client.get("/api/v1/cases")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == str(case_id)
    assert data["items"][0]["status"] == "investigating"
    assert data["items"][0]["alert_ids"] == [str(alert_id)]
    mock_repo.list_cases.assert_awaited_once()
    assert mock_repo.list_cases.await_args.args[0] == tenant_id
