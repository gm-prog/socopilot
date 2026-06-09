from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUserDep, DbSession
from app.db.models.investigation_event import InvestigationEvent

router = APIRouter()


@router.get("/alerts/{alert_id}/timeline")
async def get_timeline(
    alert_id: UUID,
    current_user: CurrentUserDep,
    db: DbSession,
) -> list[InvestigationEvent]:
    result = await db.execute(
        select(InvestigationEvent)
        .where(InvestigationEvent.alert_id == alert_id)
        .order_by(InvestigationEvent.created_at.asc())
    )
    return list(result.scalars().all())


async def add_event(
    db: AsyncSession,
    alert_id: UUID,
    event_type: str,
    payload=None,
    user_id: UUID | None = None,
):
    event = InvestigationEvent(
        alert_id=alert_id,
        event_type=event_type,
        payload=payload,
        user_id=user_id,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event
