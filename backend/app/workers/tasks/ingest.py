"""Celery ingest pipeline tasks."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.logging import bind_context, get_logger
from app.db.repositories.ingest import IngestRepository
from app.db.sync_session import get_sync_db
from app.dedup.engine import DedupEngine
from app.normalization.normalizer import AlertNormalizer
from app.realtime.alerts import publish_new_alert, serialize_alert_summary
from app.schemas.alerts import CanonicalAlertSchema
from app.schemas.ingest import WebhookAlertIn
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="app.workers.tasks.ingest.normalize_raw_event", bind=True)
def normalize_raw_event(self, raw_event_id: str, correlation_id: str) -> dict[str, Any]:
  """Load raw event and produce canonical alert dict."""
  bind_context(correlation_id=correlation_id, raw_event_id=raw_event_id, stage="normalize")
  normalizer = AlertNormalizer()

  with get_sync_db() as session:
    repo = IngestRepository(session)
    raw = repo.get_raw_event(UUID(raw_event_id))
    if raw is None:
      raise ValueError(f"Raw event {raw_event_id} not found")

    raw.status = "processing"
    try:
      parsed = raw.payload.get("parsed") or raw.payload.get("raw") or raw.payload
      alert_in = WebhookAlertIn.model_validate(parsed)
      canonical = normalizer.normalize(alert_in, default_source=raw.source_label)
      logger.info("alert_normalized", severity=canonical.severity, source=canonical.source)
      return {
        "raw_event_id": raw_event_id,
        "tenant_id": str(raw.tenant_id),
        "correlation_id": correlation_id,
        "canonical": canonical.model_dump(mode="json"),
      }
    except Exception as exc:
      repo.update_raw_event_status(raw, "failed", error=str(exc))
      repo.record_failure(
        tenant_id=raw.tenant_id,
        correlation_id=correlation_id,
        stage="normalization",
        error_message=str(exc),
        raw_event_id=raw.id,
        payload=raw.payload,
      )
      from app.dlq.service import DLQService
      DLQService(session).record(
        tenant_id=raw.tenant_id,
        correlation_id=correlation_id,
        stage="normalization",
        error_message=str(exc),
        raw_event_id=raw.id,
        payload=raw.payload,
      )
      logger.exception("normalization_failed")
      raise


@celery_app.task(name="app.workers.tasks.ingest.dedup_alert")
def dedup_alert(pipeline_data: dict[str, Any]) -> dict[str, Any]:
  """Evaluate deduplication for normalized alert."""
  correlation_id = pipeline_data["correlation_id"]
  bind_context(
    correlation_id=correlation_id,
    raw_event_id=pipeline_data["raw_event_id"],
    stage="dedup",
  )
  canonical = CanonicalAlertSchema.model_validate(pipeline_data["canonical"])
  tenant_id = UUID(pipeline_data["tenant_id"])
  engine = DedupEngine()

  with get_sync_db() as session:
    dedup = engine.evaluate(session, tenant_id, canonical)
    logger.info(
      "dedup_evaluated",
      action=dedup.action,
      fingerprint=dedup.fingerprint[:12],
      time_bucket=dedup.time_bucket,
    )
    pipeline_data["dedup"] = {
      "action": dedup.action,
      "fingerprint": dedup.fingerprint,
      "time_bucket": dedup.time_bucket,
      "existing_alert_id": str(dedup.existing_alert_id) if dedup.existing_alert_id else None,
      "duplicate_count": dedup.duplicate_count,
    }
    return pipeline_data


@celery_app.task(name="app.workers.tasks.ingest.persist_alert")
def persist_alert(pipeline_data: dict[str, Any]) -> dict[str, Any]:
  """Persist normalized alert or increment duplicate counter."""
  correlation_id = pipeline_data["correlation_id"]
  raw_event_id = UUID(pipeline_data["raw_event_id"])
  bind_context(correlation_id=correlation_id, raw_event_id=str(raw_event_id), stage="persist")

  canonical = CanonicalAlertSchema.model_validate(pipeline_data["canonical"])
  tenant_id = UUID(pipeline_data["tenant_id"])
  dedup_data = pipeline_data["dedup"]

  from app.dedup.engine import DedupResult

  dedup = DedupResult(
    action=dedup_data["action"],
    fingerprint=dedup_data["fingerprint"],
    time_bucket=dedup_data["time_bucket"],
    existing_alert_id=UUID(dedup_data["existing_alert_id"])
    if dedup_data.get("existing_alert_id")
    else None,
    duplicate_count=dedup_data.get("duplicate_count", 1),
  )

  with get_sync_db() as session:
    repo = IngestRepository(session)
    raw = repo.get_raw_event(raw_event_id)
    if raw is None:
      raise ValueError(f"Raw event {raw_event_id} not found")

    try:
      alert = repo.persist_alert(
        tenant_id=tenant_id,
        raw_event_id=raw_event_id,
        canonical=canonical,
        dedup=dedup,
      )
      repo.update_raw_event_status(raw, "completed")
      session.flush()
      from app.core.metrics import DEDUP_CREATES, DEDUP_HITS
      from app.pipelines.post_ingest import dispatch_post_ingest_pipeline

      if dedup.action == "duplicate":
        DEDUP_HITS.inc()
      else:
        DEDUP_CREATES.inc()

      logger.info(
        "alert_persisted",
        alert_id=str(alert.id),
        action=dedup.action,
        duplicate_count=alert.duplicate_count,
      )

      alert_summary = serialize_alert_summary(alert)
      session.commit()

      if dedup.action != "duplicate":
        publish_new_alert(tenant_id=tenant_id, alert=alert_summary)
      else:
        logger.info(
          "alert_duplicate_filtered",
          alert_id=str(alert.id),
          tenant_id=str(tenant_id),
          duplicate_count=alert.duplicate_count,
        )

      dispatch_post_ingest_pipeline(
        alert_id=str(alert.id),
        tenant_id=str(tenant_id),
        correlation_id=correlation_id,
        raw_event_id=str(raw_event_id),
      )

      return {
        "alert_id": str(alert.id),
        "action": dedup.action,
        "duplicate_count": alert.duplicate_count,
        "correlation_id": correlation_id,
        "tenant_id": str(tenant_id),
        "raw_event_id": str(raw_event_id),
      }
    except Exception as exc:
      repo.update_raw_event_status(raw, "failed", error=str(exc))
      repo.record_failure(
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        stage="persist",
        error_message=str(exc),
        raw_event_id=raw_event_id,
        payload=pipeline_data,
      )
      from app.dlq.service import DLQService
      DLQService(session).record(
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        stage="persist",
        error_message=str(exc),
        raw_event_id=raw_event_id,
        payload=pipeline_data,
      )
      logger.exception("persist_failed")
      raise
