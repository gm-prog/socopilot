"""Map SOC v2 pipeline output to canonical alerts and IOC rows."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.alert_ioc import AlertIOC
from app.db.models.normalized_alert import NormalizedAlert
from app.db.models.raw_event import RawEvent
from app.db.repositories.ingest import IngestRepository
from app.dedup.engine import DedupEngine
from app.dedup.fingerprint import compute_fingerprint, compute_time_bucket
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
    """Persist v2 worker output: alert row, IOCs, raw event status."""
    repo = IngestRepository(session)
    raw = repo.get_raw_event(raw_event_id)
    if raw is None:
        raise ValueError(f"Raw event {raw_event_id} not found")

    canonical = v2_result_to_canonical(
        normalized=pipeline_result["normalized"],
        severity_score=pipeline_result["severity"],
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
    for ioc_key, values in iocs.items():
        ioc_type = type_map.get(ioc_key, ioc_key.rstrip("s"))
        for value in values:
            session.add(
                AlertIOC(
                    tenant_id=tenant_id,
                    alert_id=alert.id,
                    ioc_type=ioc_type,
                    ioc_value=value,
                    confidence=0.85,
                )
            )

    raw.status = "completed"
    raw.processed_at = datetime.now(UTC)
    session.flush()
    return alert
