import uuid

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.mixins import TenantMixin


class NormalizedAlert(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    __tablename__ = "normalized_alerts"

    raw_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_events.id", ondelete="SET NULL"),
        nullable=True,
    )

    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    time_bucket: Mapped[str] = mapped_column(String(32), nullable=False)

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="webhook",
    )

    source_event_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="medium",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="RECEIVED",
        index=True,
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

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

    normalized_payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    duplicate_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
    )

    lifecycle_state: Mapped[str] = mapped_column(
        String(50),
        server_default="new",
        nullable=False,
    )

    tags: Mapped[list] = mapped_column(
        JSONB,
        server_default="[]",
        nullable=False,
    )

    # Phase 2 fields

    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    assigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    analyst_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    enrichment_summary: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(384),
        nullable=True,
    )

    # Relationships

    raw_event = relationship(
        "RawEvent",
        back_populates="normalized_alert",
        uselist=False,
    )

    iocs = relationship(
        "AlertIOC",
        back_populates="alert",
        lazy="selectin",
    )

    case_links = relationship(
        "CaseAlert",
        back_populates="alert",
        lazy="selectin",
    )