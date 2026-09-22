"""SOC v2 event ingest — raw storage and Celery dispatch."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from kombu.exceptions import OperationalError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import bind_context, get_logger
from app.db.models.raw_event import RawEvent
from app.db.models.tenant import Tenant
from app.db.repositories.tenant import DEFAULT_TENANT_NAME
from app.schemas.ingest import IngestEventQueuedResponse, IngestEventRequest
from app.workers.tasks.ingest import process_ingest_event

logger = get_logger(__name__)


async def resolve_tenant_id(
    db: AsyncSession,
    requested: UUID | None,
) -> UUID:
    if requested is not None:
        return requested

    settings = get_settings()

    if settings.ingest_default_tenant_id:
        return UUID(settings.ingest_default_tenant_id)

    result = await db.execute(
        select(Tenant.id).where(Tenant.name == DEFAULT_TENANT_NAME)
    )

    tenant_id = result.scalar_one_or_none()

    if tenant_id is None:
        raise ValueError(
            "No tenant available for ingest — register a tenant "
            "or set INGEST_DEFAULT_TENANT_ID"
        )

    return tenant_id


class IngestEventService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def queue_event(
        self,
        *,
        body: IngestEventRequest,
        tenant_id: UUID,
        user_id: UUID,
    ) -> IngestEventQueuedResponse:

        correlation_id = body.correlation_id or str(uuid4())

        event_payload: dict[str, Any] = body.model_dump(
            mode="json",
            exclude={"tenant_id", "correlation_id"},
        )

        bind_context(
            correlation_id=correlation_id,
            tenant_id=str(tenant_id),
            user_id=str(user_id),
        )

        raw_event = RawEvent(
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            source_label=body.source,
            payload={"event": event_payload},
            status="received",
        )

        self.db.add(raw_event)

        await self.db.flush()

        raw_event.status = "persisted"

        await self.db.commit()

        await self.db.refresh(raw_event)

        logger.info(
            "raw_event_persisted",
            raw_event_id=str(raw_event.id),
        )

        envelope = {
            "tenant_id": str(tenant_id),
            "raw_event_id": str(raw_event.id),
            "correlation_id": correlation_id,
            "event": event_payload,
        }

        try:
            task = process_ingest_event.delay(envelope)

        except OperationalError as exc:
            logger.exception(
                "celery_broker_unavailable",
                raw_event_id=str(raw_event.id),
            )
            raise RuntimeError(
                "Celery broker not reachable"
            ) from exc

        raw_event.celery_task_id = task.id
        raw_event.status = "queued"

        await self.db.commit()

        logger.info(
            "ingest_event_queued",
            raw_event_id=str(raw_event.id),
            task_id=task.id,
        )

        return IngestEventQueuedResponse(
            status="queued",
            task_id=task.id,
        )