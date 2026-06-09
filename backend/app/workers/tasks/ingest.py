"""Celery ingest pipeline tasks."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.core.logging import bind_context, get_logger
from app.db.repositories.ingest import IngestRepository
from app.db.sync_session import get_sync_db
from app.dedup.engine import DedupEngine
from app.normalization.normalizer import AlertNormalizer
from app.realtime.alerts import publish_new_alert, serialize_alert_summary
from app.schemas.alerts import CanonicalAlertSchema
from app.schemas.ingest import WebhookAlertIn
from app.correlation.engine import CorrelationEngine
from app.detection.engine import DetectionEngine
from app.services.event_normalizer import normalize_event
from app.services.ioc_extractor import extract_iocs
from app.services.severity import calculate_severity
from app.services.v2_persist import persist_v2_pipeline_result
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


def _count_recent_failed_logins(session, tenant_id: UUID) -> int:
    """Count failed login events in the past 5 minutes for severity calculation."""
    from app.correlation.engine import _is_failed_login, _parse_payload
    from app.db.models.raw_event import RawEvent
    from datetime import timedelta
    from sqlalchemy import select

    since = datetime.now(UTC) - timedelta(minutes=5)
    rows = session.execute(
        select(RawEvent).where(
            RawEvent.tenant_id == tenant_id,
            RawEvent.received_at >= since,
        )
    ).scalars()
    count = 0
    for raw in rows:
        payload = _parse_payload(raw)
        event_type = ""
        if isinstance(raw.payload.get("event"), dict):
            event_type = str(raw.payload["event"].get("event_type", ""))
        if _is_failed_login(payload, event_type):
            count += 1
    return count


def run_process_ingest_event(event: dict[str, Any]) -> dict[str, Any]:
    """
    SOC v2 ingestion pipeline — pure orchestration executed only inside workers.

    Steps: normalize → IOC extraction → severity scoring → detection → correlation → persist → queue phase 2.
    """
    received_at = datetime.now(UTC).isoformat()
    core_event = event.get("event") if isinstance(event.get("event"), dict) else event
    tenant_id_raw = event.get("tenant_id")
    raw_event_id_raw = event.get("raw_event_id")
    correlation_id = event.get("correlation_id") or str(uuid4())

    logger.info(
        "event_received",
        source=core_event.get("source"),
        event_type=core_event.get("event_type"),
    )

    # Step 1: Normalize event
    normalized = normalize_event(core_event)
    logger.info(
        "normalized_complete",
        source=normalized["source"],
        event_type=normalized["event_type"],
    )

    # Step 2: Extract IOCs
    iocs = extract_iocs(normalized["payload"])
    logger.info(
        "ioc_extraction_complete",
        ip_count=len(iocs["ips"]),
        domain_count=len(iocs["domains"]),
        url_count=len(iocs["urls"]),
        hash_count=len(iocs["hashes"]),
    )

    # Step 3: Calculate severity
    severity = calculate_severity(normalized, iocs)
    logger.info("severity_calculated", severity=severity)

    processed_at = datetime.now(UTC).isoformat()
    result = {
        "event_id": str(uuid4()),
        "source": normalized["source"],
        "event_type": normalized["event_type"],
        "normalized": normalized,
        "iocs": iocs,
        "severity": severity,
        "status": "processed",
        "timestamps": {
            "received_at": received_at,
            "processed_at": processed_at,
        },
    }

    detection_matches: list[dict[str, str]] = []
    alert_id: str | None = None
    correlated_ids: list[str] = []

    if tenant_id_raw and raw_event_id_raw:
        tenant_id = UUID(str(tenant_id_raw))
        raw_event_id = UUID(str(raw_event_id_raw))
        try:
            with get_sync_db() as session:
                # Step 4: Run DetectionEngine
                failed_login_count = _count_recent_failed_logins(session, tenant_id)
                detection_matches = [
                    {"rule_id": m.rule_id, "title": m.title, "severity": m.severity}
                    for m in DetectionEngine().evaluate(
                        normalized,
                        context={"failed_login_count": failed_login_count},
                    )
                ]
                if detection_matches:
                    result["detections"] = detection_matches

                # Step 5: Persist via persist_v2_pipeline_result
                alert = persist_v2_pipeline_result(
                    session,
                    tenant_id=tenant_id,
                    raw_event_id=raw_event_id,
                    correlation_id=correlation_id,
                    pipeline_result=result,
                )
                alert_id = str(alert.id)

                # Step 6: Run CorrelationEngine
                correlated = CorrelationEngine().evaluate(
                    session,
                    tenant_id=tenant_id,
                    correlation_id=correlation_id,
                )
                correlated_ids = [str(a.id) for a in correlated]
                primary_summary = serialize_alert_summary(alert)
                correlated_summaries = [
                    serialize_alert_summary(c) for c in correlated
                ]
                session.commit()

            if alert_id:
                # Step 7: Queue Phase 2 tasks
                from app.pipelines.post_ingest import dispatch_post_ingest_pipeline

                dispatch_post_ingest_pipeline(
                    alert_id=alert_id,
                    tenant_id=str(tenant_id),
                    correlation_id=correlation_id,
                    raw_event_id=str(raw_event_id),
                )
                publish_new_alert(tenant_id=tenant_id, alert=primary_summary)
                for summary in correlated_summaries:
                    publish_new_alert(tenant_id=tenant_id, alert=summary)

            if correlated_ids:
                result["correlated_alert_ids"] = correlated_ids

            result["alert_id"] = alert_id
        except Exception as exc:
            logger.exception("v2_persist_failed", error=str(exc))
            with get_sync_db() as session:
                repo = IngestRepository(session)
                raw = repo.get_raw_event(UUID(str(raw_event_id_raw)))
                if raw:
                    repo.update_raw_event_status(raw, "failed", error=str(exc))
                    repo.record_failure(
                        tenant_id=UUID(str(tenant_id_raw)),
                        correlation_id=correlation_id,
                        stage="v2_persist",
                        error_message=str(exc),
                        raw_event_id=raw.id,
                        payload=event,
                    )
                    session.commit()
            raise

    logger.info(
        "event_processed_successfully",
        event_id=result["event_id"],
        severity=severity,
        source=normalized["source"],
        alert_id=alert_id,
    )
    return result


@celery_app.task(name="app.workers.tasks.ingest.process_ingest_event", bind=True)
def process_ingest_event(self, event: dict[str, Any]) -> dict[str, Any]:
    """Celery entrypoint for SOC v2 event ingestion."""
    bind_context(celery_task_id=self.request.id, stage="ingest_v2")
    return run_process_ingest_event(event)


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
