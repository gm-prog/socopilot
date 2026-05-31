"""Ingest pipeline persistence."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.models.ingest_failure import IngestFailure
from app.db.models.normalized_alert import NormalizedAlert
from app.db.models.raw_event import RawEvent
from app.dedup.engine import DedupResult
from app.schemas.alerts import CanonicalAlertSchema


class IngestRepository:
  """Sync repository for Celery workers."""

  def __init__(self, session: Session) -> None:
    self.session = session

  def get_raw_event(self, raw_event_id: UUID) -> RawEvent | None:
    return self.session.get(RawEvent, raw_event_id)

  def update_raw_event_status(
    self,
    raw_event: RawEvent,
    status: str,
    *,
    error: str | None = None,
  ) -> None:
    raw_event.status = status
    if status in ("completed", "failed"):
      raw_event.processed_at = datetime.now(UTC)
    if error:
      raw_event.error_message = error

  def record_failure(
    self,
    *,
    tenant_id: UUID,
    correlation_id: str,
    stage: str,
    error_message: str,
    raw_event_id: UUID | None = None,
    payload: dict | None = None,
    error_detail: dict | None = None,
  ) -> IngestFailure:
    failure = IngestFailure(
      tenant_id=tenant_id,
      correlation_id=correlation_id,
      raw_event_id=raw_event_id,
      stage=stage,
      error_message=error_message,
      payload=payload,
      error_detail=error_detail,
    )
    self.session.add(failure)
    return failure

  def persist_alert(
    self,
    *,
    tenant_id: UUID,
    raw_event_id: UUID,
    canonical: CanonicalAlertSchema,
    dedup: DedupResult,
  ) -> NormalizedAlert:
    if dedup.action == "duplicate" and dedup.existing_alert_id:
      alert = self.session.get(NormalizedAlert, dedup.existing_alert_id)
      if alert is None:
        raise ValueError(f"Alert {dedup.existing_alert_id} not found for dedup")
      alert.duplicate_count = dedup.duplicate_count
      alert.last_seen_at = datetime.now(UTC)
      return alert

    alert = NormalizedAlert(
      tenant_id=tenant_id,
      raw_event_id=raw_event_id,
      fingerprint=dedup.fingerprint,
      time_bucket=dedup.time_bucket,
      source=canonical.source,
      source_event_id=canonical.source_event_id,
      title=canonical.title,
      description=canonical.description,
      severity=canonical.severity,
      status="NORMALIZED",
      lifecycle_state="new",
      detected_at=canonical.detected_at,
      normalized_payload=canonical.model_dump_canonical(),
      duplicate_count=1,
      tags=[],
    )
    self.session.add(alert)
    self.session.flush()
    return alert


class AlertRepository:
  """Async repository for API reads."""

  def __init__(self, session: AsyncSession) -> None:
    self.session = session

  async def list_alerts(
    self,
    tenant_id: UUID,
    *,
    page: int = 1,
    page_size: int = 50,
    severity: str | None = None,
    status: str | None = None,
    lifecycle_state: str | None = None,
  ) -> tuple[list[NormalizedAlert], int]:
    query = select(NormalizedAlert).where(NormalizedAlert.tenant_id == tenant_id)
    count_query = select(func.count()).select_from(NormalizedAlert).where(
      NormalizedAlert.tenant_id == tenant_id
    )
    if severity:
      query = query.where(NormalizedAlert.severity == severity)
      count_query = count_query.where(NormalizedAlert.severity == severity)
    if status:
      query = query.where(NormalizedAlert.status == status)
      count_query = count_query.where(NormalizedAlert.status == status)
    if lifecycle_state:
      query = query.where(NormalizedAlert.lifecycle_state == lifecycle_state)
      count_query = count_query.where(NormalizedAlert.lifecycle_state == lifecycle_state)

    total = (await self.session.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    result = await self.session.execute(
      query.order_by(NormalizedAlert.last_seen_at.desc()).offset(offset).limit(page_size)
    )
    return list(result.scalars().all()), total

  async def get_alert(self, tenant_id: UUID, alert_id: UUID) -> NormalizedAlert | None:
    result = await self.session.execute(
      select(NormalizedAlert).where(
        NormalizedAlert.id == alert_id,
        NormalizedAlert.tenant_id == tenant_id,
      )
    )
    return result.scalar_one_or_none()
