"""Fingerprint and time-bucket computation for deduplication."""

import hashlib
from datetime import UTC, datetime

from app.core.config import get_settings
from app.schemas.alerts import CanonicalAlertSchema


def compute_time_bucket(detected_at: datetime, bucket_minutes: int | None = None) -> str:
    settings = get_settings()
    minutes = bucket_minutes or settings.dedup_time_bucket_minutes
    if detected_at.tzinfo is None:
        detected_at = detected_at.replace(tzinfo=UTC)
    epoch = int(detected_at.timestamp())
    bucket_seconds = minutes * 60
    bucket_start = (epoch // bucket_seconds) * bucket_seconds
    return datetime.fromtimestamp(bucket_start, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _entity_fingerprint_part(entities: dict) -> str:
    parts: list[str] = []
    for key in sorted(entities.keys()):
        val = entities[key]
        if isinstance(val, list):
            parts.append(f"{key}={','.join(sorted(str(v) for v in val))}")
        else:
            parts.append(f"{key}={val}")
    return "|".join(parts)


def compute_fingerprint(tenant_id: str, alert: CanonicalAlertSchema) -> str:
    """Content fingerprint — excludes time bucket (bucket applied at dedup key)."""
    components = [
        str(tenant_id),
        alert.source,
        alert.rule_id or "",
        alert.title.strip().lower(),
        _entity_fingerprint_part(alert.entities),
    ]
    raw = "||".join(components)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def dedup_key(tenant_id: str, fingerprint: str, time_bucket: str) -> str:
    return hashlib.sha256(f"{tenant_id}:{fingerprint}:{time_bucket}".encode()).hexdigest()[:16]
