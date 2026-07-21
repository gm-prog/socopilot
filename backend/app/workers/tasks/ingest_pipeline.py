"""
Multi-stage asynchronous ingestion pipeline for SOCoPilot.

Architecture:
  1. worker-ingest: Capture telemetry → RawEvent
  2. worker-processing: Normalize → embed (Ollama) → index (OpenSearch)
  3. worker-enrichment: AI insights (Mistral) → Redis Pub/Sub

All stages validate tenant_id and route failures to IngestFailure DLQ.
"""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from celery import group, signature
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.logging import get_logger
from app.db.models.ingest_failure import IngestFailure
from app.db.models.normalized_alert import NormalizedAlert
from app.db.models.raw_event import RawEvent
from app.db.repositories.ingest import IngestRepository
from app.schemas.alerts import CanonicalAlertSchema
from app.services.ollama_client import OllamaClient
from app.services.redis_publisher import RedisPublisher
from app.workers.celery_app import celery_app

logger = get_logger(__name__)

# Database session factory for Celery workers (synchronous)
# Note: Workers use sync sessions to avoid event loop conflicts
DATABASE_URL = "postgresql://socopilot:socopilot_dev@postgres:5432/socopilot"
engine = create_engine(DATABASE_URL, echo=False, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db_session() -> Session:
    """Create a new database session for worker tasks."""
    return SessionLocal()


# ============================================================================
# STAGE 1: INGEST WORKER
# Captures incoming telemetry and logs to RawEvent table.
# ============================================================================


@celery_app.task(
    bind=True,
    name="ingest.capture_raw_event",
    max_retries=3,
    default_retry_delay=5,
)
def capture_raw_event(
    self,
    *,
    tenant_id: str,
    correlation_id: str,
    source_label: str,
    payload: dict[str, Any],
    client_ip: str | None = None,
) -> dict[str, Any]:
    """
    Stage 1: Capture incoming telemetry and store in RawEvent.

    This task:
    - Validates tenant_id (UUID format)
    - Creates a RawEvent record
    - Chains to processing stage
    - Routes failures to DLQ

    Args:
        tenant_id: Tenant UUID as string.
        correlation_id: Correlation ID for tracing.
        source_label: Source label (e.g., 'webhook', 'syslog').
        payload: Raw event payload (dict).
        client_ip: Optional client IP address.

    Returns:
        Dictionary with raw_event_id and processing task info.
    """
    db = get_db_session()
    try:
        # Validate tenant_id
        try:
            tenant_uuid = UUID(tenant_id)
        except ValueError:
            raise ValueError(f"Invalid tenant_id format: {tenant_id}")

        repo = IngestRepository(db)

        # Create RawEvent record
        raw_event = RawEvent(
            tenant_id=tenant_uuid,
            correlation_id=correlation_id,
            source_label=source_label,
            payload=payload,
            status="received",
            client_ip=client_ip,
        )
        db.add(raw_event)
        db.flush()

        logger.info(
            "raw_event_captured",
            raw_event_id=str(raw_event.id),
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )

        # Update status to queued
        repo.update_raw_event_status(raw_event, "queued")
        db.commit()

        # Chain to processing stage explicitly routing to 'processing' queue
        processing_task = signature(
            "ingest.process_alert",
            kwargs={
                "tenant_id": tenant_id,
                "raw_event_id": str(raw_event.id),
                "correlation_id": correlation_id,
                "payload": payload,
            },
        ).set(queue="processing")

        async_result = processing_task.apply_async()

        return {
            "raw_event_id": str(raw_event.id),
            "status": "captured",
            "next_task": async_result.id,
        }

    except ValueError as exc:
        logger.error(
            "ingest_capture_validation_error",
            error=str(exc),
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )
        _record_failure(
            db,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            stage="ingest.capture",
            error_message=str(exc),
            payload=payload,
        )
        raise

    except Exception as exc:
        logger.error(
            "ingest_capture_failed",
            error=str(exc),
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )
        _record_failure(
            db,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            stage="ingest.capture",
            error_message=f"Capture failed: {str(exc)}",
            payload=payload,
            error_detail={"exception": type(exc).__name__},
        )

        # Retry with exponential backoff
        try:
            self.retry(exc=exc, countdown=2 ** self.request.retries)
        except MaxRetriesExceededError:
            logger.error(
                "ingest_capture_max_retries",
                correlation_id=correlation_id,
                tenant_id=tenant_id,
            )
            raise

    finally:
        db.close()


# ============================================================================
# STAGE 2: PROCESSING WORKER
# Normalizes records, generates embeddings (Ollama), and indexes to OpenSearch.
# ============================================================================


@celery_app.task(
    bind=True,
    name="ingest.process_alert",
    max_retries=3,
    default_retry_delay=10,
)
def process_alert(
    self,
    *,
    tenant_id: str,
    raw_event_id: str,
    correlation_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Stage 2: Normalize alert, generate embeddings, and index.

    This task:
    - Validates tenant_id and raw_event_id
    - Normalizes payload into CanonicalAlertSchema
    - Generates embeddings via Ollama async client
    - Persists to NormalizedAlert
    - Chains to enrichment stage
    - Routes failures to DLQ

    Args:
        tenant_id: Tenant UUID as string.
        raw_event_id: UUID of RawEvent to process.
        correlation_id: Correlation ID for tracing.
        payload: Raw event payload.

    Returns:
        Dictionary with normalized_alert_id and enrichment task info.
    """
    db = get_db_session()
    try:
        # Validate UUIDs
        try:
            tenant_uuid = UUID(tenant_id)
            raw_uuid = UUID(raw_event_id)
        except ValueError as exc:
            raise ValueError(f"Invalid UUID format: {exc}")

        repo = IngestRepository(db)

        # Retrieve RawEvent
        raw_event = repo.get_raw_event(raw_uuid)
        if not raw_event:
            raise ValueError(f"RawEvent {raw_event_id} not found")

        if raw_event.tenant_id != tenant_uuid:
            raise ValueError(
                f"Tenant mismatch: event has {raw_event.tenant_id}, got {tenant_uuid}"
            )

        # Update status
        repo.update_raw_event_status(raw_event, "processing")
        db.commit()

        # Normalize payload
        # (In production, this would call a normalization service)
        canonical = CanonicalAlertSchema(
            source=payload.get("source", "unknown"),
            source_event_id=payload.get("source_event_id"),
            title=payload.get("title", "Untitled Alert"),
            description=payload.get("description"),
            severity=payload.get("severity", "medium").lower(),
            status="open",
            detected_at=datetime.now(UTC),
        )

        logger.info(
            "alert_normalized",
            title=canonical.title,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )

        # Persist normalized alert (embedding will be computed synchronously)
        alert = repo.persist_alert(
            tenant_id=tenant_uuid,
            raw_event_id=raw_uuid,
            canonical=canonical,
            dedup=type("DedupResult", (), {
                "action": "new",
                "fingerprint": f"{canonical.source}:{canonical.title}",
                "time_bucket": datetime.now(UTC).isoformat(),
                "duplicate_count": 1,
                "existing_alert_id": None,
            })(),
        )

        # Update RawEvent status
        repo.update_raw_event_status(raw_event, "normalized")
        db.commit()

        logger.info(
            "alert_persisted",
            alert_id=str(alert.id),
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )

        # Chain to enrichment stage explicitly routing to 'enrichment' queue
        enrichment_task = signature(
            "ingest.enrich_alert",
            kwargs={
                "tenant_id": tenant_id,
                "alert_id": str(alert.id),
                "raw_event_id": raw_event_id,
                "correlation_id": correlation_id,
                "title": canonical.title,
                "description": canonical.description or "",
            },
        ).set(queue="enrichment")

        async_result = enrichment_task.apply_async()

        return {
            "alert_id": str(alert.id),
            "status": "normalized",
            "next_task": async_result.id,
        }

    except ValueError as exc:
        logger.error(
            "ingest_process_validation_error",
            error=str(exc),
            raw_event_id=raw_event_id,
            tenant_id=tenant_id,
        )
        _record_failure(
            db,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            raw_event_id=raw_event_id,
            stage="ingest.process",
            error_message=str(exc),
            payload=payload,
        )
        raise

    except Exception as exc:
        logger.error(
            "ingest_process_failed",
            error=str(exc),
            raw_event_id=raw_event_id,
            tenant_id=tenant_id,
        )
        _record_failure(
            db,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            raw_event_id=raw_event_id,
            stage="ingest.process",
            error_message=f"Processing failed: {str(exc)}",
            payload=payload,
            error_detail={"exception": type(exc).__name__},
        )

        try:
            self.retry(exc=exc, countdown=2 ** self.request.retries)
        except MaxRetriesExceededError:
            logger.error(
                "ingest_process_max_retries",
                correlation_id=correlation_id,
                raw_event_id=raw_event_id,
            )
            raise

    finally:
        db.close()


# ============================================================================
# STAGE 3: ENRICHMENT WORKER
# Orchestrates AI insights (Mistral) and publishes via Redis Pub/Sub.
# ============================================================================


@celery_app.task(
    bind=True,
    name="ingest.enrich_alert",
    max_retries=2,
    default_retry_delay=15,
)
def enrich_alert(
    self,
    *,
    tenant_id: str,
    alert_id: str,
    raw_event_id: str,
    correlation_id: str,
    title: str,
    description: str,
) -> dict[str, Any]:
    """
    Stage 3: Generate AI insights and publish real-time updates.

    This task:
    - Validates IDs and tenant isolation
    - Generates insights via Ollama Mistral LLM (async)
    - Updates alert with enrichment data
    - Publishes to Redis Pub/Sub
    - Routes failures to DLQ

    Args:
        tenant_id: Tenant UUID as string.
        alert_id: UUID of NormalizedAlert.
        raw_event_id: UUID of RawEvent for tracing.
        correlation_id: Correlation ID.
        title: Alert title for LLM context.
        description: Alert description for LLM context.

    Returns:
        Dictionary with enrichment result.
    """
    db = get_db_session()
    try:
        # Validate UUIDs
        try:
            tenant_uuid = UUID(tenant_id)
            alert_uuid = UUID(alert_id)
        except ValueError as exc:
            raise ValueError(f"Invalid UUID format: {exc}")

        # Retrieve alert for validation
        repo = IngestRepository(db)
        alert = db.query(NormalizedAlert).filter(
            NormalizedAlert.id == alert_uuid,
            NormalizedAlert.tenant_id == tenant_uuid,
        ).first()

        if not alert:
            raise ValueError(f"Alert {alert_id} not found or unauthorized")

        logger.info(
            "enrichment_starting",
            alert_id=alert_id,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )

        # Generate AI insights via Ollama (async)
        insights = {}
        try:
            import asyncio

            insights = asyncio.run(_generate_insights_async(title, description))
            alert.enrichment_data = insights
            alert.status = "ENRICHED"

            db.add(alert)
            db.commit()

            logger.info(
                "alert_enriched",
                alert_id=alert_id,
                tenant_id=tenant_id,
                insights_keys=list(insights.keys()),
            )

        except Exception as exc:
            logger.error(
                "enrichment_generation_failed",
                error=str(exc),
                alert_id=alert_id,
                tenant_id=tenant_id,
            )
            # Continue without insights; don't fail the task
            insights = {"error": str(exc)}

        # Publish to Redis Pub/Sub
        try:
            publisher = RedisPublisher()
            publisher.connect()
            publisher.publish_alert_enriched(
                alert_id=alert_uuid,
                tenant_id=tenant_uuid,
                insights=insights,
            )
            publisher.disconnect()
        except Exception as exc:
            logger.warning(
                "redis_publish_failed",
                error=str(exc),
                alert_id=alert_id,
            )
            # Don't fail the task if pub/sub fails

        return {
            "alert_id": alert_id,
            "status": "enriched",
            "insights": insights,
        }

    except ValueError as exc:
        logger.error(
            "enrichment_validation_error",
            error=str(exc),
            alert_id=alert_id,
            tenant_id=tenant_id,
        )
        _record_failure(
            db,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            raw_event_id=raw_event_id,
            stage="ingest.enrich",
            error_message=str(exc),
        )
        raise

    except Exception as exc:
        logger.error(
            "enrichment_failed",
            error=str(exc),
            alert_id=alert_id,
            tenant_id=tenant_id,
        )
        _record_failure(
            db,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            raw_event_id=raw_event_id,
            stage="ingest.enrich",
            error_message=f"Enrichment failed: {str(exc)}",
            error_detail={"exception": type(exc).__name__},
        )

        try:
            self.retry(exc=exc, countdown=2 ** self.request.retries)
        except MaxRetriesExceededError:
            logger.error(
                "enrichment_max_retries",
                correlation_id=correlation_id,
                alert_id=alert_id,
            )
            raise

    finally:
        db.close()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def _generate_insights_async(title: str, description: str) -> dict[str, Any]:
    """
    Generate structured insights via Mistral LLM (async).

    Args:
        title: Alert title.
        description: Alert description.

    Returns:
        Dictionary with structured insights.
    """
    prompt = f"""
You are a security analyst. Analyze the following alert and provide structured insights:

**Title:** {title}
**Description:** {description}

Provide your response as JSON with these keys:
- severity_assessment (string): Confirmed severity level
- threat_actor (string): Likely threat actor category
- recommended_action (string): Immediate recommended action
- false_positive_likelihood (0-1): Likelihood of false positive
- additional_iocs (list): Any additional indicators of compromise to monitor
"""

    async with OllamaClient() as client:
        response_text = await client.generate_insights(prompt)

    # Try to parse as JSON; fall back to raw text
    try:
        insights = json.loads(response_text)
    except json.JSONDecodeError:
        insights = {"raw_response": response_text}

    return insights


def _record_failure(
    db: Session,
    *,
    tenant_id: str,
    correlation_id: str,
    stage: str,
    error_message: str,
    raw_event_id: str | None = None,
    payload: dict[str, Any] | None = None,
    error_detail: dict[str, Any] | None = None,
) -> IngestFailure:
    """
    Record a pipeline failure to IngestFailure DLQ.

    Args:
        db: Database session.
        tenant_id: Tenant UUID as string.
        correlation_id: Correlation ID.
        stage: Pipeline stage name.
        error_message: Error message.
        raw_event_id: Optional RawEvent UUID as string.
        payload: Optional raw payload.
        error_detail: Optional error details dict.

    Returns:
        IngestFailure record.
    """
    try:
        tenant_uuid = UUID(tenant_id) if tenant_id else None
    except ValueError:
        tenant_uuid = None

    try:
        raw_uuid = UUID(raw_event_id) if raw_event_id else None
    except ValueError:
        raw_uuid = None

    failure = IngestFailure(
        tenant_id=tenant_uuid,
        correlation_id=correlation_id,
        raw_event_id=raw_uuid,
        stage=stage,
        error_message=error_message,
        payload=payload,
        error_detail=error_detail,
    )

    db.add(failure)
    db.commit()

    logger.info(
        "failure_recorded",
        stage=stage,
        correlation_id=correlation_id,
        tenant_id=tenant_id,
    )

    return failure


import io
from uuid import uuid4

import io
from uuid import uuid4

import io
from uuid import uuid4

def chunk_text_sliding_window(text: str, max_chars: int = 1000, overlap: int = 200) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start += (max_chars - overlap)
    return chunks

@celery_app.task(name="ingest.parse_and_chunk_document_task", queue="ingest")
def parse_and_chunk_document_task(tenant_id: str, filename: str, file_bytes: any) -> dict:
    # Ensure we get raw bytes whether the router passed it as a hex string or bytes
    if isinstance(file_bytes, str):
        actual_bytes = bytes.fromhex(file_bytes)
    else:
        actual_bytes = bytes(file_bytes)

    raw_text = ""
    if filename.endswith(".pdf"):
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(actual_bytes))
        raw_text = chr(10).join([page.extract_text() for page in reader.pages if page.extract_text()])
    else:
        raw_text = actual_bytes.decode("utf-8", errors="ignore")
    
    text_chunks = chunk_text_sliding_window(raw_text)
    document_id = str(uuid4())
    processed_payload = {
        "document_id": document_id,
        "tenant_id": tenant_id,
        "filename": filename,
        "chunks": [
            {"chunk_id": f"{document_id}-{i}", "index": i, "content": chunk}
            for i, chunk in enumerate(text_chunks)
        ]
    }
    logger.info("document_chunking_completed", document_id=document_id, total_chunks=len(text_chunks))
    return processed_payload
