"""Case to alert linkage model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin


class CaseAlert(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "case_alerts"
    __table_args__ = (
        UniqueConstraint("case_id", "alert_id", name="uq_case_alerts_case_alert"),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("normalized_alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    case = relationship("Case", back_populates="case_alerts")
    alert = relationship("NormalizedAlert", back_populates="case_links", lazy="selectin")
