"""Record and replay failed pipeline stages."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.ingest_dlq import IngestDLQ


class DLQService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(
        self,
        *,
        tenant_id: UUID,
        correlation_id: str,
        stage: str,
        error_message: str,
        raw_event_id: UUID | None = None,
        alert_id: UUID | None = None,
        payload: dict | None = None,
    ) -> IngestDLQ:
        entry = IngestDLQ(
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            raw_event_id=raw_event_id,
            alert_id=alert_id,
            stage=stage,
            error_message=error_message,
            payload=payload,
            status="open",
        )
        self.session.add(entry)
        return entry

    def mark_replayed(self, entry: IngestDLQ) -> None:
        entry.status = "replayed"
        entry.retry_count += 1
