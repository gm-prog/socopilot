"""Normalized alert query and workflow API."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUserDep, DbSession
from app.db.models.alert_ioc import AlertIOC
from app.db.models.normalized_alert import NormalizedAlert
from app.db.models.raw_event import RawEvent
from app.db.repositories.ingest import AlertRepository
from app.schemas.alerts import AlertDetail, AlertListResponse, AlertSummary
from app.schemas.phase2 import AlertWorkflowUpdate, IOCResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    current_user: CurrentUserDep,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    severity: str | None = None,
    status: str | None = None,
    lifecycle_state: str | None = None,
) -> AlertListResponse:
    repo = AlertRepository(db)
    alerts, total = await repo.list_alerts(
        current_user.tenant_id,
        page=page,
        page_size=page_size,
        severity=severity,
        status=status,
        lifecycle_state=lifecycle_state,
    )
    return AlertListResponse(
        items=[AlertSummary.model_validate(a) for a in alerts],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{alert_id}", response_model=AlertDetail)
async def get_alert(
    alert_id: UUID,
    current_user: CurrentUserDep,
    db: DbSession,
) -> AlertDetail:
    repo = AlertRepository(db)
    alert = await repo.get_alert(current_user.tenant_id, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    raw_payload = None
    if alert.raw_event_id:
        result = await db.execute(select(RawEvent).where(RawEvent.id == alert.raw_event_id))
        raw = result.scalar_one_or_none()
        if raw:
            raw_payload = raw.payload

    ioc_result = await db.execute(
        select(AlertIOC).where(
            AlertIOC.alert_id == alert_id,
            AlertIOC.tenant_id == current_user.tenant_id,
        )
    )
    iocs = [IOCResponse.model_validate(i).model_dump() for i in ioc_result.scalars().all()]

    detail = AlertDetail.model_validate(alert)
    detail.raw_payload = raw_payload
    detail.iocs = iocs
    return detail


@router.patch("/{alert_id}", response_model=AlertDetail)
async def update_alert_workflow(
    alert_id: UUID,
    body: AlertWorkflowUpdate,
    current_user: CurrentUserDep,
    db: DbSession,
) -> AlertDetail:
    alert = await db.get(NormalizedAlert, alert_id)
    if alert is None or alert.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Alert not found")

    if body.lifecycle_state is not None:
        alert.lifecycle_state = body.lifecycle_state
        if body.lifecycle_state in ("resolved", "false_positive"):
            alert.closed_at = datetime.now(UTC)
    if body.assigned_to is not None:
        alert.assigned_to = body.assigned_to
        alert.assigned_at = datetime.now(UTC)
    if body.tags is not None:
        alert.tags = body.tags
    if body.analyst_notes is not None:
        alert.analyst_notes = body.analyst_notes

    await db.flush()
    return await get_alert(alert_id, current_user, db)
