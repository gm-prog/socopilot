from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.db.base import Base


class InvestigationEvent(Base):
    __tablename__ = "investigation_events"

    id = Column(Integer, primary_key=True, index=True)

    alert_id = Column(Integer, ForeignKey("alerts.id"), index=True)

    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)

    user_id = Column(Integer, nullable=True)

    created_at = Column(DateTime, server_default=func.now())