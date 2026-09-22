from typing import List
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.db.base import Base

class AlertEmbedding(Base):
    __tablename__ = "alert_embeddings"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    alert_id: Mapped[str] = mapped_column(String, ForeignKey("normalized_alerts.id"), index=True, nullable=False)

    embedding: Mapped[List[float]] = mapped_column(Vector(768), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
