import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.db.base import Base


class AlertEmbedding(Base):
    """Alert embedding cache (pgvector).

    NOTE: keys are UUIDs with real foreign keys (tenants / normalized_alerts),
    matching the 003 migration and the rest of the schema. An earlier
    revision declared these as String, which caused the head migration to
    attempt a UUID->VARCHAR retype that cannot execute against the live
    foreign keys and would have broken tenant isolation.
    """

    __tablename__ = "alert_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("normalized_alerts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # 768 dims — matches the configured embedding model (nomic-embed-text).
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
