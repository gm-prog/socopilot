"""Alert list/detail API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AlertSummary(BaseModel):
    id: UUID
    title: str
    severity: str
    status: str
    lifecycle_state: str = "new"
    source: str
    detected_at: datetime
    ingested_at: datetime
    last_seen_at: datetime
    duplicate_count: int
    fingerprint: str
    time_bucket: str
    assigned_to: UUID | None = None
    tags: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class AlertDetail(AlertSummary):
    description: str | None
    source_event_id: str | None
    raw_event_id: UUID | None
    normalized_payload: dict[str, Any]
    raw_payload: dict[str, Any] | None = None
    enrichment_summary: dict[str, Any] | None = None
    analyst_notes: str | None = None
    assigned_at: datetime | None = None
    closed_at: datetime | None = None
    iocs: list[dict[str, Any]] = Field(default_factory=list)


class AlertListResponse(BaseModel):
    items: list[AlertSummary]
    total: int
    page: int
    page_size: int


class CanonicalAlertSchema(BaseModel):
    """Internal canonical alert representation."""

    source: str
    source_event_id: str | None = None
    title: str
    description: str | None = None
    severity: str
    detected_at: datetime
    rule_id: str | None = None
    entities: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_dump_canonical(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
