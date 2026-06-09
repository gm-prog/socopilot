"""Regex-based IOC extraction for the SOC v2 ingestion pipeline."""

from __future__ import annotations

import json
import re
from typing import Any

IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
IPV6_RE = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b")
DOMAIN_RE = re.compile(r"\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
MD5_RE = re.compile(r"\b[a-fA-F0-9]{32}\b")
SHA1_RE = re.compile(r"\b[a-fA-F0-9]{40}\b")
SHA256_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")

PRIVATE_IPV4_PREFIXES = (
    "10.",
    "127.",
    "192.168.",
    "172.16.",
    "172.17.",
    "172.18.",
    "172.19.",
    "172.2",
    "169.254.",
)


def _payload_to_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            parts.append(json.dumps(value, default=str))
        elif value is not None:
            parts.append(str(value))
        parts.append(str(key))
    return " ".join(parts)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        normalized = value.strip().rstrip(".,;")
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        out.append(normalized)
    return out


def _extract_ips(text: str, payload: dict[str, Any]) -> list[str]:
    ips: list[str] = []
    for match in IPV4_RE.finditer(text):
        ips.append(match.group())
    for match in IPV6_RE.finditer(text):
        ips.append(match.group())

    for key in ("ip", "src_ip", "dst_ip", "source_ip", "dest_ip"):
        value = payload.get(key)
        if value:
            ips.append(str(value))
    for key in ("ips", "source_ips", "destination_ips"):
        value = payload.get(key)
        if isinstance(value, list):
            ips.extend(str(item) for item in value if item)

    return _dedupe(ips)


def _extract_domains(text: str, payload: dict[str, Any]) -> list[str]:
    domains: list[str] = []
    for match in DOMAIN_RE.finditer(text):
        candidate = match.group().lower()
        if IPV4_RE.fullmatch(candidate):
            continue
        if "@" in candidate:
            continue
        domains.append(candidate)

    for key in ("domain", "hostname", "host"):
        value = payload.get(key)
        if value and not IPV4_RE.fullmatch(str(value)):
            domains.append(str(value).lower())
    value = payload.get("domains")
    if isinstance(value, list):
        domains.extend(str(item).lower() for item in value if item)

    return _dedupe(domains)


def _extract_urls(text: str, payload: dict[str, Any]) -> list[str]:
    urls = [match.group().rstrip(".,;") for match in URL_RE.finditer(text)]
    for key in ("url", "uri"):
        value = payload.get(key)
        if value:
            urls.append(str(value))
    value = payload.get("urls")
    if isinstance(value, list):
        urls.extend(str(item) for item in value if item)
    return _dedupe(urls)


def _extract_hashes(text: str, payload: dict[str, Any]) -> list[str]:
    hashes: list[str] = []
    hashes.extend(match.group().lower() for match in MD5_RE.finditer(text))
    hashes.extend(match.group().lower() for match in SHA1_RE.finditer(text))
    hashes.extend(match.group().lower() for match in SHA256_RE.finditer(text))

    for key in ("md5", "sha1", "sha256", "hash", "file_hash"):
        value = payload.get(key)
        if value:
            hashes.append(str(value).lower())
    value = payload.get("hashes")
    if isinstance(value, list):
        hashes.extend(str(item).lower() for item in value if item)

    return _dedupe(hashes)


def extract_iocs(payload: dict[str, Any]) -> dict[str, list[str]]:
    """
    Extract IOC categories from a normalized event payload.

    Returns:
        {"ips": [], "domains": [], "urls": [], "hashes": []}
    """
    if not isinstance(payload, dict):
        payload = {}

    text = _payload_to_text(payload)
    return {
        "ips": _extract_ips(text, payload),
        "domains": _extract_domains(text, payload),
        "urls": _extract_urls(text, payload),
        "hashes": _extract_hashes(text, payload),
    }
