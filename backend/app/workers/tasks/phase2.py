import json
import logging
from typing import Any
from uuid import UUID

from structlog import contextvars

from app.db.sync_session import get_sync_db
try:
    from app.db.models.normalized_alert import NormalizedAlert
except ImportError:
    from app.models.alert import NormalizedAlert

try:
    from app.integrations.opensearch.client import OpenSearchClient
except ImportError:
    from app.integrations.opensearch import OpenSearchClient

from app.workers.celery_app import celery_app
from app.dlq.service import DLQService
from app.core.metrics import DLQ_ENTRIES

logger = logging.getLogger(__name__)


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



def bind_context(**kwargs):
    for k, v in kwargs.items():
        contextvars.bind_contextvars(**{k: v})


@celery_app.task(
    name='app.workers.tasks.phase2.index_alert_opensearch',
    autoretry_for=(ValueError,),
    retry_kwargs={'max_retries': 5, 'countdown': 2},
    exponential_backoff=True,
)
def index_alert_opensearch(header: Any) -> dict[str, Any]:
    # Defensive parsing for dict or raw str / stringified JSON
    if isinstance(header, str):
        try:
            parsed = json.loads(header)
            if isinstance(parsed, dict):
                header = parsed
            else:
                header = {'alert_id': header}
        except Exception:
            header = {'alert_id': header}

    raw_alert_id = header.get('alert_id') if isinstance(header, dict) else str(header)
    bind_context(alert_id=raw_alert_id, stage='indexing')
    alert_id = UUID(str(raw_alert_id))

    # Fetch alert and construct doc payload inside active DB session context
    with get_sync_db() as session:
        alert = session.get(NormalizedAlert, alert_id)
        if alert is None:
            logger.warning(f'Alert {alert_id} not found in database')
            raise ValueError(f'Alert {alert_id} not found in database (transient sync delay)')

        doc = {
            'tenant_id': str(alert.tenant_id),
            'title': alert.title,
            'description': alert.description,
            'severity': alert.severity,
            'source': alert.source,
            'lifecycle_state': alert.lifecycle_state,
            'detected_at': alert.detected_at.isoformat() if alert.detected_at else None,
            'fingerprint': alert.fingerprint,
        }

    try:
<<<<<<< HEAD
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
                logger.warning("indexing_skipped_alert_not_found", alert_id=alert_id)
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
                logger.warning("embedding_skipped_alert_not_found", alert_id=str(alert_id))
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
            embedding = resp.json().get("embedding")
            if embedding is None:
                logger.warning("ollama_embed_empty_response", model=model)
            return embedding
    except httpx.TimeoutException:
        logger.warning("ollama_embed_timeout", model=model)
        return None
    except httpx.HTTPStatusError as exc:
        logger.warning("ollama_embed_http_error", model=model, status_code=exc.response.status_code)
        return None
    except Exception as exc:
        logger.warning("ollama_embed_failed", model=model, error=str(exc))
        return None
=======
        client = OpenSearchClient()
        if hasattr(client, 'ensure_indices'):
            client.ensure_indices()
        if hasattr(client, 'index_alert_sync'):
            client.index_alert_sync(str(alert_id), doc)
        elif hasattr(client, 'index_alert'):
            client.index_alert(str(alert_id), doc)
        logger.info(f'Successfully indexed alert {alert_id} into OpenSearch')
        return header
    except Exception as exc:
        with get_sync_db() as session:
            _record_dlq(
                session,
                header if isinstance(header, dict) else {'alert_id': raw_alert_id},
                'indexing',
                str(exc),
                header if isinstance(header, dict) else {'alert_id': raw_alert_id},
            )
            session.commit()
        logger.warning(f'indexing_failed: {exc}')
        return header
>>>>>>> 1d16aa5 (feat: semantic search, real-time alerts, and frontend store migration)
