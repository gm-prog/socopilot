"""IOC extraction unit tests."""

from datetime import UTC, datetime

from app.extraction.extractor import IOCExtractor
from app.schemas.alerts import CanonicalAlertSchema


def test_extract_ipv4_and_hash():
    canonical = CanonicalAlertSchema(
        source="webhook",
        title="Malware on host",
        description="File abcdef0123456789abcdef0123456789 seen from 203.0.113.50",
        severity="high",
        detected_at=datetime.now(UTC),
        entities={"hosts": ["workstation-01"]},
    )
    iocs = IOCExtractor().extract(canonical).iocs
    types = {i.ioc_type for i in iocs}
    assert "ipv4" in types
    assert "md5" in types
    assert "hostname" in types


def test_deduplicate_iocs():
    canonical = CanonicalAlertSchema(
        source="webhook",
        title="203.0.113.1",
        description="Connection from 203.0.113.1",
        severity="low",
        detected_at=datetime.now(UTC),
    )
    iocs = IOCExtractor().extract(canonical).iocs
    ipv4 = [i for i in iocs if i.ioc_type == "ipv4"]
    assert len(ipv4) == 1
