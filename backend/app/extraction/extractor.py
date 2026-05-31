"""Extract IOCs from alert fields and nested payloads."""

from dataclasses import dataclass, field
from typing import Any

from app.extraction.patterns import (
    DOMAIN_RE,
    EMAIL_RE,
    HOSTNAME_RE,
    IPV4_RE,
    IPV6_RE,
    MD5_RE,
    PRIVATE_IPV4_PREFIXES,
    SHA1_RE,
    SHA256_RE,
    URL_RE,
    USERNAME_RE,
)
from app.schemas.alerts import CanonicalAlertSchema


@dataclass
class ExtractedIOC:
    ioc_type: str
    ioc_value: str
    confidence: float = 0.8
    source_field: str = "text"


@dataclass
class ExtractionResult:
    iocs: list[ExtractedIOC] = field(default_factory=list)

    def deduplicated(self) -> list[ExtractedIOC]:
        seen: set[tuple[str, str]] = set()
        out: list[ExtractedIOC] = []
        for ioc in self.iocs:
            key = (ioc.ioc_type, ioc.ioc_value.lower())
            if key in seen:
                continue
            seen.add(key)
            out.append(ioc)
        return out


class IOCExtractor:
    def extract_from_text(self, text: str, source_field: str = "text") -> list[ExtractedIOC]:
        if not text:
            return []
        found: list[ExtractedIOC] = []

        for m in IPV4_RE.finditer(text):
            ip = m.group()
            conf = 0.7 if ip.startswith(PRIVATE_IPV4_PREFIXES) else 0.9
            found.append(ExtractedIOC("ipv4", ip, conf, source_field))
        for m in IPV6_RE.finditer(text):
            found.append(ExtractedIOC("ipv6", m.group(), 0.85, source_field))
        for m in URL_RE.finditer(text):
            found.append(ExtractedIOC("url", m.group().rstrip(".,;"), 0.9, source_field))
        for m in SHA256_RE.finditer(text):
            found.append(ExtractedIOC("sha256", m.group().lower(), 0.95, source_field))
        for m in SHA1_RE.finditer(text):
            found.append(ExtractedIOC("sha1", m.group().lower(), 0.95, source_field))
        for m in MD5_RE.finditer(text):
            found.append(ExtractedIOC("md5", m.group().lower(), 0.95, source_field))
        for m in EMAIL_RE.finditer(text):
            found.append(ExtractedIOC("email", m.group().lower(), 0.9, source_field))
        for m in DOMAIN_RE.finditer(text):
            val = m.group().lower()
            if "@" not in val and not val.endswith(".local"):
                found.append(ExtractedIOC("domain", val, 0.75, source_field))
        return found

    def extract_from_entities(self, entities: dict[str, Any]) -> list[ExtractedIOC]:
        found: list[ExtractedIOC] = []
        type_map = {
            "ips": "ipv4",
            "src_ip": "ipv4",
            "dst_ip": "ipv4",
            "hosts": "hostname",
            "host": "hostname",
            "hostname": "hostname",
            "users": "username",
            "user": "username",
            "username": "username",
            "domains": "domain",
            "domain": "domain",
            "urls": "url",
            "url": "url",
            "hashes": "sha256",
            "md5": "md5",
            "sha1": "sha1",
            "sha256": "sha256",
            "emails": "email",
            "email": "email",
        }
        for key, val in entities.items():
            ioc_type = type_map.get(key.lower())
            if not ioc_type:
                continue
            values = val if isinstance(val, list) else [val]
            for v in values:
                if v is None:
                    continue
                s = str(v).strip()
                if s:
                    found.append(ExtractedIOC(ioc_type, s, 0.95, f"entities.{key}"))
        return found

    def extract(self, canonical: CanonicalAlertSchema, raw_payload: dict | None = None) -> ExtractionResult:
        result = ExtractionResult()
        for field_name, text in [
            ("title", canonical.title),
            ("description", canonical.description or ""),
        ]:
            result.iocs.extend(self.extract_from_text(text, field_name))

        result.iocs.extend(self.extract_from_entities(canonical.entities))

        if raw_payload:
            import json

            blob = json.dumps(raw_payload, default=str)
            result.iocs.extend(self.extract_from_text(blob, "raw_payload"))

        result.iocs = result.deduplicated()
        return result


def extract_iocs_from_alert(
    canonical: CanonicalAlertSchema,
    raw_payload: dict | None = None,
) -> list[ExtractedIOC]:
    return IOCExtractor().extract(canonical, raw_payload).iocs
