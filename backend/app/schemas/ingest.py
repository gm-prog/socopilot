"""Ingest API request/response schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class WebhookAlertIn(BaseModel):
    """Generic JSON webhook alert payload."""

    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    severity: str = Field(default="medium", max_length=50)
    source: str | None = Field(default=None, max_length=100)
    source_event_id: str | None = Field(default=None, max_length=255)
    rule_id: str | None = Field(default=None, max_length=255)
    detected_at: datetime | None = None
    entities: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("entities", "metadata", mode="before")
    @classmethod
    def empty_dict_if_none(cls, v: Any) -> dict:
        return v if v is not None else {}


class IngestAlertsRequest(BaseModel):
    """Single alert or batch ingest."""

    alert: WebhookAlertIn | None = None
    alerts: list[WebhookAlertIn] | None = None

    def items(self) -> list[WebhookAlertIn]:
        if self.alerts:
            return self.alerts
        if self.alert:
            return [self.alert]
        return []


class IngestItemResponse(BaseModel):
    raw_event_id: UUID
    correlation_id: str
    pipeline_task_id: str | None = None
    status: str = "accepted"


class IngestAlertsResponse(BaseModel):
    correlation_id: str
    accepted: int
    items: list[IngestItemResponse]


class IngestEventRequest(BaseModel):
    """SOC v2 event-driven ingest payload."""

    source: str = Field(min_length=1, max_length=100)
    event_type: str = Field(min_length=1, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str | None = None
    tenant_id: UUID | None = None
    correlation_id: str | None = None


class IngestEventQueuedResponse(BaseModel):
    status: str = "queued"
    task_id: str
