"""Failed ingest pipeline records."""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.mixins import TenantMixin


class IngestFailure(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    __tablename__ = "ingest_failures"
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    raw_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    error_detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
