"""Investigation timeline event model."""

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


class InvestigationEvent(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    __tablename__ = "investigation_events"

    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("normalized_alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # API-compatibility aliases.
    #
    # The Pydantic response schema (InvestigationEventResponse) exposes
    # `event_metadata` and `created_by`, while the actual columns are
    # `payload` and `user_id`. These properties let pydantic's
    # from_attributes validation read the real columns without a name
    # mismatch (previously the API silently returned nulls and the POST
    # endpoint raised TypeError for the unknown `event_metadata` kwarg).
    # ------------------------------------------------------------------
    @property
    def event_metadata(self) -> dict[str, Any] | None:
        return self.payload

    @property
    def created_by(self) -> uuid.UUID | None:
        return self.user_id
