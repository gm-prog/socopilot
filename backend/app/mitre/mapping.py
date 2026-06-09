"""MITRE ATT&CK technique mapping for normalized SOC events."""

from __future__ import annotations

from typing import Any


def _payload_text(normalized: dict[str, Any]) -> str:
    event_type = str(normalized.get("event_type", "")).lower()
    payload = normalized.get("payload") or {}
    parts = [event_type, str(payload).lower()]
    for key in ("command", "process", "shell", "script"):
        if key in payload:
            parts.append(str(payload[key]).lower())
    return " ".join(parts)


def map_mitre_techniques(normalized: dict[str, Any]) -> list[dict[str, str]]:
    """Return technique objects: {\"id\": \"T1110\", \"name\": \"...\"}."""
    text = _payload_text(normalized)
    event_type = str(normalized.get("event_type", "")).lower()
    techniques: list[dict[str, str]] = []

    brute_tokens = ("brute", "failed login", "login_attempt", "auth failure")
    if any(t in text for t in brute_tokens) or (
        "login" in event_type and "fail" in text
    ):
        techniques.append({"id": "T1110", "name": "Brute Force"})

    if "powershell" in text or "pwsh" in text:
        techniques.append({"id": "T1059.001", "name": "PowerShell"})

    if "port scan" in text or event_type == "port_scan":
        techniques.append({"id": "T1046", "name": "Network Service Discovery"})

    if "credential" in text and "stuff" in text:
        techniques.append({"id": "T1110.004", "name": "Credential Stuffing"})

    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for tech in techniques:
        if tech["id"] not in seen:
            seen.add(tech["id"])
            unique.append(tech)
    return unique
