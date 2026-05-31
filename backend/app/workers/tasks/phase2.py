"""Phase 2 Celery tasks — extraction, enrichment, indexing, embeddings."""

import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import bind_context, get_logger
from app.core.metrics import DLQ_ENTRIES, EMBEDDING_LATENCY, EXTRACTION_COUNT
from app.db.models.alert_ioc import AlertIOC
from app.db.models.normalized_alert import NormalizedAlert
from app.db.models.raw_event import RawEvent
from app.db.sync_session import get_sync_db
from app.dlq.service import DLQService
from app.enrichment.dispatcher import EnrichmentDispatcher
from app.extraction.extractor import IOCExtractor
from app.integrations.opensearch.client import OpenSearchClient
from app.schemas.alerts import CanonicalAlertSchema
from app.vector.store import VectorStore
from app.workers.celery_app import celery_app
from app.workers.tasks.enrichment import run_enrichment_job

logger = get_logger(__name__)


def _record_dlq(session, header: dict, stage: str, error: str, payload: dict | None = None):
    DLQService(session).record(
        tenant_id=UUID(header["tenant_id"]),
        correlation_id=header.get("correlation_id", ""),
        stage=stage,
        error_message=error,
        raw_event_id=UUID(header["raw_event_id"]) if header.get("raw_event_id") else None,
        alert_id=UUID(header["alert_id"]),
        payload=payload,
    )
    DLQ_ENTRIES.labels(stage=stage).inc()


@celery_app.task(name="app.workers.tasks.phase2.extract_iocs_task")
def extract_iocs_task(header: dict[str, Any]) -> dict[str, Any]:
    bind_context(
        correlation_id=header.get("correlation_id"),
        alert_id=header.get("alert_id"),
        stage="extraction",
    )
    alert_id = UUID(header["alert_id"])
    tenant_id = UUID(header["tenant_id"])

    try:
        with get_sync_db() as session:
            alert = session.get(NormalizedAlert, alert_id)
            if alert is None:
                raise ValueError(f"Alert {alert_id} not found")

            raw_payload = None
            if alert.raw_event_id:
                raw = session.get(RawEvent, alert.raw_event_id)
                raw_payload = raw.payload if raw else None

            canonical = CanonicalAlertSchema.model_validate(alert.normalized_payload)
            extracted = IOCExtractor().extract(canonical, raw_payload)
            now = datetime.now(UTC)

            for ioc in extracted.iocs:
                existing = session.execute(
                    select(AlertIOC).where(
                        AlertIOC.tenant_id == tenant_id,
                        AlertIOC.alert_id == alert_id,
                        AlertIOC.ioc_type == ioc.ioc_type,
                        AlertIOC.ioc_value == ioc.ioc_value,
                    )
                ).scalar_one_or_none()
                if existing:
                    existing.last_seen_at = now
                else:
                    session.add(
                        AlertIOC(
                            tenant_id=tenant_id,
                            alert_id=alert_id,
                            ioc_type=ioc.ioc_type,
                            ioc_value=ioc.ioc_value,
                            confidence=ioc.confidence,
                            first_seen_at=now,
                            last_seen_at=now,
                        )
                    )
                EXTRACTION_COUNT.labels(ioc_type=ioc.ioc_type).inc()

            session.flush()
            header["ioc_count"] = len(extracted.iocs)
            logger.info("iocs_extracted", count=len(extracted.iocs))
            return header
    except Exception as exc:
        with get_sync_db() as session:
            _record_dlq(session, header, "extraction", str(exc), header)
        raise


@celery_app.task(name="app.workers.tasks.phase2.dispatch_enrichment_jobs")
def dispatch_enrichment_jobs(header: dict[str, Any]) -> dict[str, Any]:
    bind_context(alert_id=header.get("alert_id"), stage="enrichment_dispatch")
    alert_id = UUID(header["alert_id"])
    tenant_id = UUID(header["tenant_id"])

    try:
        with get_sync_db() as session:
            jobs = EnrichmentDispatcher().create_jobs(session, tenant_id, alert_id)
            for job in jobs:
                if job.status == "pending":
                    task = run_enrichment_job.delay(str(job.id))
                    job.celery_task_id = task.id
            session.flush()
            header["enrichment_jobs"] = len(jobs)
            return header
    except Exception as exc:
        with get_sync_db() as session:
            _record_dlq(session, header, "enrichment", str(exc), header)
        raise


@celery_app.task(name="app.workers.tasks.phase2.index_alert_opensearch")
def index_alert_opensearch(header: dict[str, Any]) -> dict[str, Any]:
    bind_context(alert_id=header.get("alert_id"), stage="indexing")
    alert_id = header["alert_id"]
    try:
        with get_sync_db() as session:
            alert = session.get(NormalizedAlert, UUID(alert_id))
            if alert is None:
                return header
            doc = {
                "tenant_id": str(alert.tenant_id),
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity,
                "source": alert.source,
                "lifecycle_state": alert.lifecycle_state,
                "detected_at": alert.detected_at.isoformat(),
                "fingerprint": alert.fingerprint,
            }
            OpenSearchClient().index_alert_sync(alert_id, doc)
        return header
    except Exception as exc:
        with get_sync_db() as session:
            _record_dlq(session, header, "indexing", str(exc), header)
        logger.warning("indexing_failed", error=str(exc))
        return header


@celery_app.task(name="app.workers.tasks.phase2.generate_alert_embedding")
def generate_alert_embedding(header: dict[str, Any]) -> dict[str, Any]:
    bind_context(alert_id=header.get("alert_id"), stage="embedding")
    settings = get_settings()
    alert_id = UUID(header["alert_id"])
    tenant_id = UUID(header["tenant_id"])

    try:
        start = time.perf_counter()
        with get_sync_db() as session:
            alert = session.get(NormalizedAlert, alert_id)
            if alert is None:
                return header
            text = f"{alert.title}\n{alert.description or ''}"
            vector = _embed_text(text, settings.ollama_embed_model)
            if vector:
                VectorStore().upsert(
                    session,
                    tenant_id=tenant_id,
                    alert_id=alert_id,
                    model_name=settings.ollama_embed_model,
                    vector=vector,
                )
        EMBEDDING_LATENCY.observe(time.perf_counter() - start)
        return header
    except Exception as exc:
        with get_sync_db() as session:
            _record_dlq(session, header, "embedding", str(exc), header)
        logger.warning("embedding_failed", error=str(exc))
        return header


def _embed_text(text: str, model: str) -> list[float] | None:
    settings = get_settings()
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{settings.ollama_host.rstrip('/')}/api/embed",
                json={"model": model, "prompt": text[:8000]},
            )
            resp.raise_for_status()
            return resp.json().get("embedding")
    except Exception as exc:
        logger.warning("ollama_embed_failed", error=str(exc))
        return None
