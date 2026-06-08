"""Extended IOC extraction tests — covering uncovered branches."""

from datetime import UTC, datetime

from app.extraction.extractor import ExtractionResult, ExtractedIOC, IOCExtractor
from app.schemas.alerts import CanonicalAlertSchema


def _make_canonical(title="Test", description=None, entities=None):
    return CanonicalAlertSchema(
        source="webhook",
        title=title,
        description=description,
        severity="medium",
        detected_at=datetime.now(UTC),
        entities=entities or {},
    )


# ---- extract_from_text edge cases ----

def test_extract_empty_text():
    assert IOCExtractor().extract_from_text("") == []


def test_extract_ipv6():
    iocs = IOCExtractor().extract_from_text("from 2001:0db8:85a3::8a2e:0370:7334")
    types = {i.ioc_type for i in iocs}
    assert "ipv6" in types


def test_extract_url():
    iocs = IOCExtractor().extract_from_text("visit https://evil.example.com/malware")
    types = {i.ioc_type for i in iocs}
    assert "url" in types


def test_extract_sha256():
    sha = "a" * 64
    iocs = IOCExtractor().extract_from_text(f"hash {sha}")
    types = {i.ioc_type for i in iocs}
    assert "sha256" in types


def test_extract_sha1():
    sha1 = "b" * 40
    iocs = IOCExtractor().extract_from_text(f"sha1={sha1}")
    types = {i.ioc_type for i in iocs}
    assert "sha1" in types


def test_extract_email():
    iocs = IOCExtractor().extract_from_text("phishing from attacker@evil.org")
    types = {i.ioc_type for i in iocs}
    assert "email" in types


def test_extract_domain():
    iocs = IOCExtractor().extract_from_text("callback to malware.example.com seen")
    types = {i.ioc_type for i in iocs}
    assert "domain" in types


def test_domain_skip_local():
    iocs = IOCExtractor().extract_from_text("host myserver.local")
    domains = [i for i in iocs if i.ioc_type == "domain"]
    assert len(domains) == 0


def test_private_ip_lower_confidence():
    iocs = IOCExtractor().extract_from_text("from 192.168.1.1")
    ipv4 = [i for i in iocs if i.ioc_type == "ipv4"]
    assert len(ipv4) == 1
    assert ipv4[0].confidence == 0.7


def test_public_ip_higher_confidence():
    iocs = IOCExtractor().extract_from_text("from 8.8.8.8")
    ipv4 = [i for i in iocs if i.ioc_type == "ipv4"]
    assert len(ipv4) == 1
    assert ipv4[0].confidence == 0.9


# ---- extract_from_entities ----

def test_entities_ip_extraction():
    extractor = IOCExtractor()
    iocs = extractor.extract_from_entities({"src_ip": "203.0.113.5"})
    assert len(iocs) == 1
    assert iocs[0].ioc_type == "ipv4"


def test_entities_list_values():
    extractor = IOCExtractor()
    iocs = extractor.extract_from_entities({"hosts": ["h1", "h2"]})
    assert len(iocs) == 2
    assert all(i.ioc_type == "hostname" for i in iocs)


def test_entities_skip_none_values():
    extractor = IOCExtractor()
    iocs = extractor.extract_from_entities({"hosts": [None, "valid-host"]})
    assert len(iocs) == 1


def test_entities_skip_unknown_key():
    extractor = IOCExtractor()
    iocs = extractor.extract_from_entities({"unknown_field": "data"})
    assert len(iocs) == 0


def test_entities_skip_empty_string():
    extractor = IOCExtractor()
    iocs = extractor.extract_from_entities({"hosts": [""]})
    assert len(iocs) == 0


# ---- extract with raw_payload ----

def test_extract_with_raw_payload():
    canonical = _make_canonical(title="Test")
    raw = {"ip": "10.0.0.1", "data": "payload"}
    result = IOCExtractor().extract(canonical, raw_payload=raw)
    ipv4 = [i for i in result.iocs if i.ioc_type == "ipv4"]
    assert len(ipv4) >= 1


# ---- ExtractionResult.deduplicated ----

def test_deduplication_preserves_first():
    result = ExtractionResult(
        iocs=[
            ExtractedIOC("ipv4", "1.2.3.4", 0.9, "title"),
            ExtractedIOC("ipv4", "1.2.3.4", 0.7, "description"),
        ]
    )
    deduped = result.deduplicated()
    assert len(deduped) == 1
    assert deduped[0].confidence == 0.9


def test_deduplication_case_insensitive():
    result = ExtractionResult(
        iocs=[
            ExtractedIOC("md5", "AABB" * 8, 0.95, "title"),
            ExtractedIOC("md5", "aabb" * 8, 0.95, "desc"),
        ]
    )
    deduped = result.deduplicated()
    assert len(deduped) == 1
