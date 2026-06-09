"""Severity scoring engine for the SOC v2 ingestion pipeline."""

from __future__ import annotations

import json
from typing import Any

from app.services.ioc_extractor import PRIVATE_IPV4_PREFIXES

KNOWN_SOURCES = frozenset(
    {
        "firewall",
        "ids",
        "ips",
        "edr",
        "siem",
        "crowdstrike",
        "sentinel",
        "defender",
        "webhook",
        "syslog",
        "waf",
        "proxy",
        "email_gateway",
    }
)

SUSPICIOUS_KEYWORDS = (
    "malware",
    "exploit",
    "ransomware",
    "brute",
    "unauthorized",
    "attack",
    "intrusion",
    "credential",
    "exfil",
    "c2",
    "command and control",
)

MIN_SEVERITY = 1
MAX_SEVERITY = 10
BASE_SEVERITY = 3


def _is_failed_login(normalized_event: dict[str, Any]) -> bool:
    event_type = str(normalized_event.get("event_type", "")).lower()
    payload = normalized_event.get("payload") or {}
    status = str(payload.get("status", "")).lower()
    action = str(payload.get("action", "")).lower()
    result = str(payload.get("result", "")).lower()

    if "login" not in event_type and "auth" not in event_type:
        return False

    failure_tokens = {"failed", "failure", "denied", "reject", "blocked"}
    return (
        status in failure_tokens
        or action in failure_tokens
        or result in failure_tokens
        or payload.get("success") is False
    )


def _is_repeated_failure(normalized_event: dict[str, Any]) -> bool:
    payload = normalized_event.get("payload") or {}
    for key in ("attempts", "count", "failure_count", "failed_attempts"):
        value = payload.get(key)
        if isinstance(value, int) and value > 1:
            return True
        if isinstance(value, str) and value.isdigit() and int(value) > 1:
            return True
    return False


def _has_suspicious_keywords(normalized_event: dict[str, Any]) -> bool:
    blob = json.dumps(normalized_event, default=str).lower()
    return any(keyword in blob for keyword in SUSPICIOUS_KEYWORDS)


def _has_suspicious_ip_patterns(iocs: dict[str, list[str]], normalized_event: dict[str, Any]) -> bool:
    ips = iocs.get("ips") or []
    if not ips:
        return False

    for ip in ips:
        if any(ip.startswith(prefix) for prefix in PRIVATE_IPV4_PREFIXES):
            return True

    if _is_failed_login(normalized_event):
        return True

    return False


def calculate_severity(normalized_event: dict[str, Any], iocs: dict[str, list[str]]) -> int:
    """
    Rule engine scoring.

    Start at 3, apply additive rules, clamp to [1, 10].
    """
    score = BASE_SEVERITY

    if _is_failed_login(normalized_event):
        score += 3

    if _is_repeated_failure(normalized_event):
        score += 2

    if iocs.get("ips"):
        score += 1
    if iocs.get("domains"):
        score += 1
    if iocs.get("urls"):
        score += 1
    if iocs.get("hashes"):
        score += 2

    if _has_suspicious_ip_patterns(iocs, normalized_event):
        score += 2

    if _has_suspicious_keywords(normalized_event):
        score += 2

    source = str(normalized_event.get("source", "")).lower()
    if source not in KNOWN_SOURCES:
        score += 1

    return max(MIN_SEVERITY, min(MAX_SEVERITY, score))
