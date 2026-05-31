"""Deduplication decision engine."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.normalized_alert import NormalizedAlert
from app.dedup.fingerprint import compute_fingerprint, compute_time_bucket
from app.schemas.alerts import CanonicalAlertSchema


@dataclass
class DedupResult:
    action: str  # "create" | "duplicate"
    fingerprint: str
    time_bucket: str
    existing_alert_id: UUID | None = None
    duplicate_count: int = 1


class DedupEngine:
    def evaluate(
        self,
        session: Session,
        tenant_id: UUID,
        canonical: CanonicalAlertSchema,
    ) -> DedupResult:
        fingerprint = compute_fingerprint(str(tenant_id), canonical)
        time_bucket = compute_time_bucket(canonical.detected_at)

        existing = session.execute(
            select(NormalizedAlert).where(
                NormalizedAlert.tenant_id == tenant_id,
                NormalizedAlert.fingerprint == fingerprint,
                NormalizedAlert.time_bucket == time_bucket,
            )
        ).scalar_one_or_none()

        if existing:
            return DedupResult(
                action="duplicate",
                fingerprint=fingerprint,
                time_bucket=time_bucket,
                existing_alert_id=existing.id,
                duplicate_count=existing.duplicate_count + 1,
            )

        return DedupResult(
            action="create",
            fingerprint=fingerprint,
            time_bucket=time_bucket,
        )
