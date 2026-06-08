from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.dependencies import CurrentUserDep, DbSession
from app.db.models.investigation_event import InvestigationEvent

router = APIRouter(prefix="/alerts", tags=["investigation"])


@router.get("/{alert_id}/timeline")
async def get_timeline(
    alert_id: UUID,
    current_user: CurrentUserDep,
    db: DbSession,
):
    result = await db.execute(
        select(InvestigationEvent)
        .where(InvestigationEvent.alert_id == alert_id)
        .order_by(InvestigationEvent.created_at.asc())
    )
    return result.scalars().all()