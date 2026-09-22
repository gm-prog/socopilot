"""IOC lookup API."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUserDep, DbSession
from app.db.models.alert_ioc import AlertIOC
from app.schemas.phase2 import IOCResponse

router = APIRouter(prefix="/iocs", tags=["iocs"])


@router.get("", response_model=list[IOCResponse])
async def list_iocs(
    current_user: CurrentUserDep,
    db: DbSession,
    alert_id: UUID | None = None,
    ioc_type: str | None = None,
    ioc_value: str | None = None,
    limit: int = Query(100, ge=1, le=500),
) -> list[IOCResponse]:
    q = select(AlertIOC).where(AlertIOC.tenant_id == current_user.tenant_id)
    if alert_id:
        q = q.where(AlertIOC.alert_id == alert_id)
    if ioc_type:
        q = q.where(AlertIOC.ioc_type == ioc_type)
    if ioc_value:
        q = q.where(AlertIOC.ioc_value == ioc_value)
    q = q.limit(limit)
    result = await db.execute(q)
    return [IOCResponse.model_validate(r) for r in result.scalars().all()]


@router.get("/{ioc_id}", response_model=IOCResponse)
async def get_ioc(
    ioc_id: UUID,
    current_user: CurrentUserDep,
    db: DbSession,
) -> IOCResponse:
    result = await db.execute(
        select(AlertIOC).where(
            AlertIOC.id == ioc_id,
            AlertIOC.tenant_id == current_user.tenant_id,
        )
    )
    ioc = result.scalar_one_or_none()
    if ioc is None:
        raise HTTPException(status_code=404, detail="IOC not found")
    return IOCResponse.model_validate(ioc)
