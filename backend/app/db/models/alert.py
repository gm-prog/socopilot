"""Alert database model."""

from datetime import datetime
from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.mixins import TenantMixin


class Alert(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    __tablename__ = "alerts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "alert_fingerprint", name="uq_alerts_tenant_fingerprint"),
        Index("ix_alerts_tenant_status", "tenant_id", "status"),
        Index("ix_alerts_tenant_severity", "tenant_id", "severity"),
        Index("ix_alerts_tenant_detected_at", "tenant_id", "detected_at"),
    )

    source: Mapped[str] = mapped_column(String(100), nullable=False, default="webhook")
    source_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    alert_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="RECEIVED", index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    normalized_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    raw_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tenant = relationship("Tenant", back_populates="alerts")
    pipeline_jobs = relationship("PipelineJob", back_populates="alert", lazy="selectin")
