"""Correlate recent events into higher-fidelity alerts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.normalized_alert import NormalizedAlert
from app.db.models.raw_event import RawEvent
from app.db.repositories.ingest import IngestRepository
from app.dedup.fingerprint import compute_fingerprint, compute_time_bucket
from app.mitre.mapping import map_mitre_techniques
from app.schemas.alerts import CanonicalAlertSchema


def _parse_payload(raw: RawEvent) -> dict[str, Any]:
    body = raw.payload or {}
    if isinstance(body.get("event"), dict):
        inner = body["event"]
        return inner.get("payload") or inner
    if isinstance(body.get("parsed"), dict):
        return body["parsed"]
    return body if isinstance(body, dict) else {}


def _is_failed_login(payload: dict[str, Any], event_type: str) -> bool:
    status = str(payload.get("status", "")).lower()
    if status in {"failed", "failure", "denied", "reject", "blocked"}:
        return True
    if payload.get("success") is False:
        return True
    et = event_type.lower()
    return "login" in et or "auth" in et


class CorrelationEngine:
    """Windowed correlation over raw_events for a tenant."""

    def __init__(self, window_minutes: int = 5) -> None:
        self.window = timedelta(minutes=window_minutes)

    def evaluate(
        self,
        session: Session,
        *,
        tenant_id: UUID,
        correlation_id: str,
    ) -> list[NormalizedAlert]:
        since = datetime.now(UTC) - self.window
        rows = list(
            session.execute(
                select(RawEvent)
                .where(
                    RawEvent.tenant_id == tenant_id,
                    RawEvent.received_at >= since,
                )
                .order_by(RawEvent.received_at.desc())
                .limit(500)
            ).scalars()
        )
        if not rows:
            return []

        generated: list[NormalizedAlert] = []
        generated.extend(self._brute_force(session, tenant_id, correlation_id, rows))
        generated.extend(self._port_scan(session, tenant_id, correlation_id, rows))
        generated.extend(self._credential_stuffing(session, tenant_id, correlation_id, rows))
        return generated

    def _persist_correlated(
        self,
        session: Session,
        *,
        tenant_id: UUID,
        correlation_id: str,
        rule: str,
        title: str,
        description: str,
        severity: str,
        entities: dict[str, Any],
    ) -> NormalizedAlert | None:
        repo = IngestRepository(session)
        detected_at = datetime.now(UTC)
        canonical = CanonicalAlertSchema(
            source="correlation",
            source_event_id=f"{rule}:{correlation_id}",
            title=title,
            description=description,
            severity=severity,
            detected_at=detected_at,
            rule_id=rule,
            entities=entities,
            metadata={
                "correlation_rule": rule,
                "mitre_attack": map_mitre_techniques(
                    {"event_type": rule, "payload": entities}
                ),
            },
        )
        fingerprint = compute_fingerprint(str(tenant_id), canonical)
        time_bucket = compute_time_bucket(detected_at)
        existing = session.execute(
            select(NormalizedAlert).where(
                NormalizedAlert.tenant_id == tenant_id,
                NormalizedAlert.fingerprint == fingerprint,
                NormalizedAlert.time_bucket == time_bucket,
            )
        ).scalar_one_or_none()
        if existing:
            return None

        from app.dedup.engine import DedupResult

        alert = repo.persist_alert(
            tenant_id=tenant_id,
            raw_event_id=None,
            canonical=canonical,
            dedup=DedupResult(
                action="create",
                fingerprint=fingerprint,
                time_bucket=time_bucket,
            ),
        )
        alert.tags = ["correlated", rule]
        session.flush()
        return alert

    def _brute_force(
        self,
        session: Session,
        tenant_id: UUID,
        correlation_id: str,
        rows: list[RawEvent],
    ) -> list[NormalizedAlert]:
        by_ip: dict[str, int] = {}
        for raw in rows:
            payload = _parse_payload(raw)
            event_type = ""
            if isinstance(raw.payload.get("event"), dict):
                event_type = str(raw.payload["event"].get("event_type", ""))
            if not _is_failed_login(payload, event_type):
                continue
            ip = str(payload.get("ip") or payload.get("src_ip") or "unknown")
            by_ip[ip] = by_ip.get(ip, 0) + 1

        out: list[NormalizedAlert] = []
        for ip, count in by_ip.items():
            if count < 10:
                continue
            alert = self._persist_correlated(
                session,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
                rule="brute_force",
                title=f"Brute force — {count} failed logins from {ip}",
                description=f"{count} failed login events from {ip} within {self.window}",
                severity="high",
                entities={"src_ip": [ip], "failed_login_count": count},
            )
            if alert:
                out.append(alert)
        return out

    def _port_scan(
        self,
        session: Session,
        tenant_id: UUID,
        correlation_id: str,
        rows: list[RawEvent],
    ) -> list[NormalizedAlert]:
        by_src: dict[str, set[int]] = {}
        for raw in rows:
            payload = _parse_payload(raw)
            src = str(payload.get("src_ip") or payload.get("ip") or "")
            port = payload.get("dest_port") or payload.get("dst_port") or payload.get("port")
            if not src or port is None:
                continue
            try:
                by_src.setdefault(src, set()).add(int(port))
            except (TypeError, ValueError):
                continue

        out: list[NormalizedAlert] = []
        for src, ports in by_src.items():
            if len(ports) < 15:
                continue
            alert = self._persist_correlated(
                session,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
                rule="port_scan",
                title=f"Port scan — {src} probed {len(ports)} ports",
                description=f"Source {src} touched {len(ports)} destination ports in {self.window}",
                severity="high",
                entities={"src_ip": [src], "dest_ports": sorted(ports)},
            )
            if alert:
                out.append(alert)
        return out

    def _credential_stuffing(
        self,
        session: Session,
        tenant_id: UUID,
        correlation_id: str,
        rows: list[RawEvent],
    ) -> list[NormalizedAlert]:
        by_src: dict[str, set[str]] = {}
        for raw in rows:
            payload = _parse_payload(raw)
            src = str(payload.get("src_ip") or payload.get("ip") or "")
            user = payload.get("user") or payload.get("username")
            if not src or not user:
                continue
            by_src.setdefault(src, set()).add(str(user))

        out: list[NormalizedAlert] = []
        for src, users in by_src.items():
            if len(users) < 8:
                continue
            alert = self._persist_correlated(
                session,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
                rule="credential_stuffing",
                title=f"Credential stuffing — {src} tried {len(users)} accounts",
                description=f"Source {src} attempted {len(users)} distinct usernames in {self.window}",
                severity="critical",
                entities={"src_ip": [src], "usernames": sorted(users)[:50]},
            )
            if alert:
                out.append(alert)
        return out
