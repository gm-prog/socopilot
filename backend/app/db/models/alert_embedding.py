"""Alert semantic embeddings (Phase 2 foundation)."""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.mixins import TenantMixin


class AlertEmbedding(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    __tablename__ = "alert_embeddings"
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("normalized_alerts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    vector: Mapped[list] = mapped_column(JSONB, nullable=False)
    text_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
