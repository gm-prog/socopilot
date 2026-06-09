"""Ingest orchestration — raw event storage and pipeline dispatch."""

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
        raw_event = RawEvent(
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            source_label=source_label,
            payload={"raw": payload, "parsed": alert.model_dump(mode="json")},
            status="received",
            client_ip=client_ip,
        )
        self.db.add(raw_event)
        await self.db.flush()
        await self.db.commit()

        bind_context(raw_event_id=str(raw_event.id))
        logger.info("raw_event_stored", status="received")

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

        try:
            task = process_ingest_event.delay(envelope)
        except Exception as exc:
            raw_event.status = "failed"
            raw_event.error_message = f"Pipeline dispatch failed: {exc}"
            await self.db.flush()
            logger.error("ingest_pipeline_dispatch_failed", error=str(exc), raw_event_id=str(raw_event.id))
            raise

        raw_event.celery_task_id = task.id
        raw_event.status = "queued"
        await self.db.flush()

        logger.info("ingest_pipeline_queued", celery_task_id=task.id)
        return IngestItemResponse(
            raw_event_id=raw_event.id,
            correlation_id=correlation_id,
            pipeline_task_id=task.id,
            status="accepted",
        )

    @staticmethod
    def new_correlation_id(header_value: str | None = None) -> str:
        return header_value or str(uuid4())
