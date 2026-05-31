"""Normalization unit tests."""

from datetime import UTC, datetime

from app.normalization.normalizer import AlertNormalizer
from app.normalization.severity import normalize_severity
from app.normalization.source import normalize_source
from app.schemas.ingest import WebhookAlertIn


def test_normalize_severity_aliases():
    assert normalize_severity("crit") == "critical"
    assert normalize_severity("INFO") == "informational"
    assert normalize_severity("med") == "medium"


def test_normalize_source_aliases():
    assert normalize_source("generic") == "webhook"
    assert normalize_source("splunk") == "splunk"


def test_alert_normalizer_produces_canonical():
    normalizer = AlertNormalizer()
    raw = WebhookAlertIn(
        title="Suspicious PowerShell",
        severity="high",
        source="Generic",
        rule_id="R-1001",
        detected_at=datetime(2026, 5, 26, 12, 7, tzinfo=UTC),
        entities={"hosts": ["workstation-01"], "users": ["jsmith"]},
    )
    canonical = normalizer.normalize(raw)
    assert canonical.severity == "high"
    assert canonical.source == "webhook"
    assert canonical.title == "Suspicious PowerShell"
    assert canonical.entities["rule_id"] == "R-1001"
    assert "hosts" in canonical.entities
