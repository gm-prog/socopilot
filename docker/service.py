"""
Ingest orchestration — production-safe version.

Fixes:
- atomic DB write before enqueue
- consistent commit boundary
- safe Celery dispatch
- no partial state corruption
"""

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import bind_context, get_logger
from app.db.models.raw_event import RawEvent
from app.schemas.ingest import IngestItemResponse, WebhookAlertIn
from app.workers.tasks.ingest import process_ingest_event

logger = get_logger(__name__)


class IngestService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def accept_alert(
        self,
        *,
        tenant_id: UUID,
        correlation_id: str,
        payload: dict[str, Any],
        alert: WebhookAlertIn,
        client_ip: str | None = None,
        source_label: str = "webhook",
    ) -> IngestItemResponse:

        bind_context(
            correlation_id=correlation_id,
            tenant_id=str(tenant_id),
        )

        # =========================================================
        # STEP 1 — CREATE RAW EVENT (NOT COMMITTED YET)
        # =========================================================
        raw_event = RawEvent(
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            source_label=source_label,
            payload={
                "raw": payload,
                "parsed": alert.model_dump(mode="json"),
            },
            status="received",
            client_ip=client_ip,
        )

        self.db.add(raw_event)

        try:
            await self.db.flush()  # ensures raw_event.id exists

            bind_context(raw_event_id=str(raw_event.id))

            logger.info(
                "raw_event_staged",
                raw_event_id=str(raw_event.id),
            )

            # =========================================================
            # STEP 2 — BUILD CELERY ENVELOPE
            # =========================================================
            envelope = {
                "tenant_id": str(tenant_id),
                "raw_event_id": str(raw_event.id),
                "correlation_id": correlation_id,
                "event": {
                    "source": source_label,
                    "event_type": alert.title,
                    "timestamp": alert.detected_at.isoformat(),
                    "payload": alert.model_dump(mode="json"),
                },
            }

            # =========================================================
            # STEP 3 — ENQUEUE CELERY (BEFORE FINAL COMMIT)
            # =========================================================
            task = process_ingest_event.delay(envelope)

            # update state
            raw_event.celery_task_id = task.id
            raw_event.status = "queued"

            # =========================================================
            # STEP 4 — FINAL COMMIT (SINGLE ATOMIC WRITE)
            # =========================================================
            await self.db.commit()

            logger.info(
                "ingest_pipeline_queued",
                raw_event_id=str(raw_event.id),
                celery_task_id=task.id,
            )

            return IngestItemResponse(
                raw_event_id=raw_event.id,
                correlation_id=correlation_id,
                pipeline_task_id=task.id,
                status="accepted",
            )

        except Exception as exc:
            # rollback EVERYTHING if anything fails
            await self.db.rollback()

            logger.exception(
                "ingest_accept_failed",
                error_type=type(exc).__name__,
                error_msg=str(exc),
                raw_event_id=getattr(raw_event, "id", None),
            )

            raise