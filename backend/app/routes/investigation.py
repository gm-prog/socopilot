from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUserDep, DbSession
from app.db.session import get_db
from app.db.models.investigation_event import InvestigationEvent

router = APIRouter()


@router.get("/alerts/{alert_id}/timeline")
async def get_timeline(
    alert_id: UUID,
    current_user: CurrentUserDep,
    db: DbSession,
):
    from sqlalchemy import select

    result = await db.execute(
        select(InvestigationEvent)
        .where(InvestigationEvent.alert_id == alert_id)
        .order_by(InvestigationEvent.created_at.asc())
    )
    return result.scalars().all()


def add_event(db: Session, alert_id: UUID, event_type: str, payload=None, user_id=None):
    event = InvestigationEvent(
        alert_id=alert_id,
        event_type=event_type,
        payload=payload,
        user_id=user_id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event