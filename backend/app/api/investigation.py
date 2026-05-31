from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.app.models import InvestigationEvent  # adjust if your models path differs

router = APIRouter(prefix="/alerts", tags=["investigation"])


@router.get("/{alert_id}/timeline")
def get_timeline(alert_id: int, db: Session = Depends(get_db)):
    return (
        db.query(InvestigationEvent)
        .filter(InvestigationEvent.alert_id == alert_id)
        .order_by(InvestigationEvent.created_at.asc())
        .all()
    )