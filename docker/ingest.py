"""Celery ingest pipeline tasks (hardened)."""

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


def _safe_uuid(value: Any) -> UUID | None:
    """Strict UUID validation helper."""
    if not value:
        return None
    try:
        return UUID(str(value))
    except Exception:
        logger.error("invalid_uuid_received", value=str(value))
        return None


def _count_recent_failed_logins(session, tenant_id: UUID) -> int:
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
    received_at = datetime.now(UTC).isoformat()

    core_event = event.get("event") if isinstance(event.get("event"), dict) else event

    tenant_id = _safe_uuid(event.get("tenant_id"))
    raw_event_id = _safe_uuid(event.get("raw_event_id"))

    correlation_id = event.get("correlation_id") or str(uuid4())

    # HARD FAIL FAST (important fix)
    if not tenant_id or not raw_event_id:
        logger.error(
            "invalid_ingest_event_payload",
            tenant_id=str(event.get("tenant_id")),
            raw_event_id=str(event.get("raw_event_id")),
        )
        return {
            "status": "failed",
            "reason": "invalid_uuid",
            "correlation_id": correlation_id,
        }

    logger.info(
        "event_received",
        source=(core_event or {}).get("source"),
        event_type=(core_event or {}).get("event_type"),
    )

    # Step 1: Normalize
    normalized = normalize_event(core_event)

    # Step 2: IOC extraction
    iocs = extract_iocs(normalized["payload"])

    # Step 3: Severity
    severity = calculate_severity(normalized, iocs)

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
            "processed_at": datetime.now(UTC).isoformat(),
        },
    }

    detection_matches = []
    alert_id = None
    correlated_ids = []

    try:
        with get_sync_db() as session:

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

            alert = persist_v2_pipeline_result(
                session,
                tenant_id=tenant_id,
                raw_event_id=raw_event_id,
                correlation_id=correlation_id,
                pipeline_result=result,
            )

            alert_id = str(alert.id)

            correlated = CorrelationEngine().evaluate(
                session,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
            )

            correlated_ids = [str(a.id) for a in correlated]

            session.commit()

        from app.pipelines.post_ingest import dispatch_post_ingest_pipeline

        dispatch_post_ingest_pipeline(
            alert_id=alert_id,
            tenant_id=str(tenant_id),
            correlation_id=correlation_id,
            raw_event_id=str(raw_event_id),
        )

        publish_new_alert(tenant_id=tenant_id, alert=serialize_alert_summary(alert))

        for c in correlated:
            publish_new_alert(tenant_id=tenant_id, alert=serialize_alert_summary(c))

        result["alert_id"] = alert_id
        result["correlated_alert_ids"] = correlated_ids

    except Exception as exc:
        logger.exception("pipeline_failed", error=str(exc))
        return {
            "status": "failed",
            "error": str(exc),
            "event_id": result["event_id"],
        }

    return result


@celery_app.task(name="app.workers.tasks.ingest.process_ingest_event", bind=True)
def process_ingest_event(self, event: dict[str, Any]) -> dict[str, Any]:
    bind_context(celery_task_id=self.request.id, stage="ingest_v2")
    return run_process_ingest_event(event)