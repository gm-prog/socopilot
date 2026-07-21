"""Raw SIEM event storage with global tenant isolation capabilities."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.mixins import TenantMixin


class RawEvent(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    """
    Stores raw, incoming events from diverse SIEM agents and endpoints.
    Inherits from TenantMixin to automatically enforce multi-tenant compile boundaries.
    """
    __tablename__ = "raw_events"

    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_label: Mapped[str] = mapped_column(String(100), nullable=False, default="webhook")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="received", index=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    normalized_alert = relationship(
        "NormalizedAlert",
        back_populates="raw_event",
        uselist=False,
        lazy="selectin",
    )
