"""Map SOC v2 pipeline output to canonical alerts and IOC rows."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.alert_ioc import AlertIOC
from app.db.models.normalized_alert import NormalizedAlert
from app.db.models.raw_event import RawEvent
from app.db.repositories.ingest import IngestRepository
from app.dedup.engine import DedupEngine
from app.mitre.mapping import map_mitre_techniques
from app.schemas.alerts import CanonicalAlertSchema


def severity_score_to_label(score: int) -> str:
    if score >= 9:
        return "critical"
    if score >= 7:
        return "high"
    if score >= 5:
        return "medium"
    return "low"


def v2_result_to_canonical(
    *,
    normalized: dict[str, Any],
    severity_score: int,
    event_id: str,
) -> CanonicalAlertSchema:
    payload = normalized.get("payload") or {}
    ips = payload.get("ip") or payload.get("src_ip") or []
    if isinstance(ips, str):
        ips = [ips]
    entities: dict[str, Any] = {}
    if ips:
        entities["src_ip"] = ips if isinstance(ips, list) else [str(ips)]

    detected_raw = normalized.get("timestamp")
    if detected_raw:
        detected_at = datetime.fromisoformat(str(detected_raw).replace("Z", "+00:00"))
        if detected_at.tzinfo is None:
            detected_at = detected_at.replace(tzinfo=UTC)
    else:
        detected_at = datetime.now(UTC)

    mitre = map_mitre_techniques(normalized)
    metadata = {"soc_v2": True, "event_id": event_id, "severity_score": severity_score}
    if mitre:
        metadata["mitre_attack"] = mitre

    return CanonicalAlertSchema(
        source=normalized["source"],
        source_event_id=event_id,
        title=f"{normalized['event_type']} — {normalized['source']}",
        description=str(payload)[:2000] if payload else None,
        severity=severity_score_to_label(severity_score),
        detected_at=detected_at,
        rule_id=normalized.get("event_type"),
        entities=entities,
        metadata=metadata,
    )


def persist_v2_pipeline_result(
    session: Session,
    *,
    tenant_id: UUID,
    raw_event_id: UUID,
    correlation_id: str,
    pipeline_result: dict[str, Any],
) -> NormalizedAlert:
    """Persist v2 worker output: alert row, IOCs, raw event status with severity escalation."""
    repo = IngestRepository(session)
    raw = repo.get_raw_event(raw_event_id)
    if raw is None:
        raise ValueError(f"Raw event {raw_event_id} not found")

    # Severity Escalation Logic
    final_severity = pipeline_result.get("severity", 5)
    detections = pipeline_result.get("detections", [])
    
    # If any detection is critical, force score to 9
    for det in detections:
        if det.get("severity") == "critical":
            final_severity = max(final_severity, 9)
        elif det.get("severity") == "high":
            final_severity = max(final_severity, 7)

    canonical = v2_result_to_canonical(
        normalized=pipeline_result["normalized"],
        severity_score=final_severity,
        event_id=pipeline_result["event_id"],
    )
    
    dedup = DedupEngine().evaluate(session, tenant_id, canonical)
    alert = repo.persist_alert(
        tenant_id=tenant_id,
        raw_event_id=raw_event_id,
        canonical=canonical,
        dedup=dedup,
    )

    type_map = {"ips": "ip", "domains": "domain", "urls": "url", "hashes": "hash"}
    iocs = pipeline_result.get("iocs") or {}

    ioc_rows: set[tuple[str, str]] = set()
    for ioc_key, values in iocs.items():
        ioc_type = type_map.get(ioc_key, ioc_key.rstrip("s"))
        for value in values:
            ioc_rows.add((ioc_type, str(value)))

    if ioc_rows:
        existing_iocs = {
            (ioc_type, ioc_value)
            for ioc_type, ioc_value in session.execute(
                select(AlertIOC.ioc_type, AlertIOC.ioc_value).where(
                    AlertIOC.tenant_id == tenant_id,
                    AlertIOC.alert_id == alert.id,
                )
            ).all()
        }

        now = datetime.now(UTC)
        new_iocs = []
        for ioc_type, ioc_value in ioc_rows:
            if (ioc_type, ioc_value) in existing_iocs:
                continue
            new_iocs.append(
                AlertIOC(
                    tenant_id=tenant_id,
                    alert_id=alert.id,
                    ioc_type=ioc_type,
                    ioc_value=ioc_value,
                    confidence=0.85,
                    first_seen_at=now,
                    last_seen_at=now,
                )
            )

        if new_iocs:
            session.add_all(new_iocs)
            try:
                session.flush()
            except IntegrityError:
                session.rollback()
                # Another concurrent process may have inserted the same IOC row.
                # We can safely ignore it because the unique constraint is preserved.

    raw.status = "completed"
    raw.processed_at = datetime.now(UTC)
    session.flush()
    return alert
