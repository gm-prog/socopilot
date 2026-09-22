"""Normalize raw webhook payloads into canonical alerts."""

from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings
from app.normalization.severity import normalize_severity
from app.normalization.source import normalize_source
from app.schemas.alerts import CanonicalAlertSchema
from app.schemas.ingest import WebhookAlertIn


class AlertNormalizer:
    def normalize(
        self,
        raw: WebhookAlertIn | dict[str, Any],
        *,
        default_source: str | None = None,
    ) -> CanonicalAlertSchema:
        settings = get_settings()
        if isinstance(raw, dict):
            raw = WebhookAlertIn.model_validate(raw)

        source = normalize_source(
            raw.source or default_source,
            default=settings.ingest_default_source,
        )
        severity = normalize_severity(raw.severity)
        detected_at = raw.detected_at or datetime.now(UTC)

        entities = dict(raw.entities)
        if raw.rule_id and "rule_id" not in entities:
            entities["rule_id"] = raw.rule_id

        return CanonicalAlertSchema(
            source=source,
            source_event_id=raw.source_event_id,
            title=raw.title.strip(),
            description=raw.description,
            severity=severity,
            detected_at=detected_at if detected_at.tzinfo else detected_at.replace(tzinfo=UTC),
            rule_id=raw.rule_id,
            entities=entities,
            metadata=dict(raw.metadata),
        )
