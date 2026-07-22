from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models.investigation_event import InvestigationEvent
from app.db.session import get_db

router = APIRouter(prefix="/alerts", tags=["investigation"])


@router.get("/{alert_id}/timeline")
def get_timeline(alert_id: int, db: Session = Depends(get_db)):
    """Retrieve the investigation timeline for a specific alert."""
    return (
        db.query(InvestigationEvent)
        .filter(InvestigationEvent.alert_id == alert_id)
        .order_by(InvestigationEvent.created_at.asc())
        .all()
    )


def add_event(db: Session, alert_id: int, event_type: str, payload=None, user_id=None):
    """Utility function to append historical actions to an investigation timeline."""
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
