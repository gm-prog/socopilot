"""Normalized alert records after ingest pipeline."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class NormalizedAlert(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "normalized_alerts"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "fingerprint",
            "time_bucket",
            name="uq_normalized_alerts_tenant_fingerprint_bucket",
        ),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    time_bucket: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="NORMALIZED", index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    normalized_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    lifecycle_state: Mapped[str] = mapped_column(
        String(50), nullable=False, default="new", index=True
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    analyst_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    enrichment_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    raw_event = relationship("RawEvent", back_populates="normalized_alert", lazy="selectin")
    iocs = relationship("AlertIOC", back_populates="alert", lazy="selectin")
    case_links = relationship("CaseAlert", back_populates="alert", lazy="selectin")
