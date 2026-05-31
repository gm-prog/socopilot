"""Case API schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

CaseSeverity = Literal["low", "medium", "high", "critical"]
CaseStatus = Literal["open", "investigating", "closed"]


class CaseCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    severity: CaseSeverity = "medium"
    status: CaseStatus = "open"
    alert_ids: list[UUID] = Field(default_factory=list)


class CaseResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    title: str
    description: str | None
    severity: CaseSeverity
    status: CaseStatus
    created_at: datetime
    updated_at: datetime
    alert_ids: list[UUID] = Field(default_factory=list)


class CaseListResponse(BaseModel):
    items: list[CaseResponse]
    total: int
    page: int
    page_size: int
