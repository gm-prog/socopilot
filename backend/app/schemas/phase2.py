"""Phase 2 API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class IOCResponse(BaseModel):
    id: UUID
    ioc_type: str
    ioc_value: str
    confidence: float
    first_seen_at: datetime
    last_seen_at: datetime

    model_config = {"from_attributes": True}


class EnrichmentResultResponse(BaseModel):
    id: UUID
    provider: str
    status: str
    latency_ms: int | None
    summary: dict[str, Any] | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertWorkflowUpdate(BaseModel):
    lifecycle_state: str | None = Field(
        default=None,
        pattern="^(new|triaged|investigating|contained|resolved|false_positive)$",
    )
    assigned_to: UUID | None = None
    tags: list[str] | None = None
    analyst_notes: str | None = None


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    limit: int = Field(default=10, ge=1, le=50)


class SemanticSearchResult(BaseModel):
    alert_id: UUID
    score: float
    title: str | None = None


class SemanticSearchResponse(BaseModel):
    results: list[SemanticSearchResult]
    message: str = "Stub semantic search — PostgreSQL vector cosine similarity"


class ReplayResponse(BaseModel):
    raw_event_id: UUID
    correlation_id: str
    pipeline_task_id: str | None
    status: str
