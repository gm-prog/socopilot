"""Case database model."""

from datetime import datetime
from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.mixins import TenantMixin


class Case(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    __tablename__ = "cases"
    __table_args__ = (
        Index("ix_cases_tenant_status", "tenant_id", "status"),
        Index("ix_cases_tenant_severity", "tenant_id", "severity"),
        Index("ix_cases_tenant_priority", "tenant_id", "priority"),
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="OPEN", index=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")
    assignee: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    tenant = relationship("Tenant", back_populates="cases")
    case_alerts = relationship("CaseAlert", back_populates="case", cascade="all, delete-orphan", lazy="selectin")
