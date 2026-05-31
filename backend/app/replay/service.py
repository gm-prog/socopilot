"""Replay raw events through the full ingest + post-ingest pipeline."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.raw_event import RawEvent
from app.pipelines.ingest_chain import dispatch_ingest_pipeline


class ReplayService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def replay_raw_event(
        self,
        tenant_id: UUID,
        raw_event_id: UUID,
        correlation_id: str,
    ) -> dict:
        raw = await self.db.get(RawEvent, raw_event_id)
        if raw is None or raw.tenant_id != tenant_id:
            raise ValueError("Raw event not found")

        raw.status = "received"
        raw.error_message = None
        raw.processed_at = None
        await self.db.flush()
        await self.db.commit()

        task = dispatch_ingest_pipeline(str(raw_event_id), correlation_id)
        raw.celery_task_id = task.id
        raw.status = "queued"
        await self.db.flush()

        return {
            "raw_event_id": str(raw_event_id),
            "correlation_id": correlation_id,
            "pipeline_task_id": task.id,
            "status": "replaying",
        }
