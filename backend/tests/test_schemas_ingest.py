"""Unit tests for app.schemas.ingest — request/response models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.ingest import IngestAlertsRequest, WebhookAlertIn


# ---- WebhookAlertIn ----

def test_webhook_alert_defaults():
    alert = WebhookAlertIn(title="Test")
    assert alert.severity == "medium"
    assert alert.source is None
    assert alert.entities == {}
    assert alert.metadata == {}


def test_webhook_alert_none_entities_coerced():
    alert = WebhookAlertIn(title="Test", entities=None)
    assert alert.entities == {}


def test_webhook_alert_none_metadata_coerced():
    alert = WebhookAlertIn(title="Test", metadata=None)
    assert alert.metadata == {}


def test_webhook_alert_title_required():
    with pytest.raises(ValidationError):
        WebhookAlertIn()


def test_webhook_alert_title_min_length():
    with pytest.raises(ValidationError):
        WebhookAlertIn(title="")


def test_webhook_alert_full_fields():
    alert = WebhookAlertIn(
        title="Full alert",
        description="Some desc",
        severity="critical",
        source="splunk",
        source_event_id="evt-001",
        rule_id="rule-42",
        detected_at=datetime(2026, 1, 1, tzinfo=UTC),
        entities={"ips": ["1.2.3.4"]},
        metadata={"custom": True},
    )
    assert alert.title == "Full alert"
    assert alert.rule_id == "rule-42"
    assert alert.entities["ips"] == ["1.2.3.4"]


# ---- IngestAlertsRequest.items() ----

def test_items_with_single_alert():
    req = IngestAlertsRequest(alert=WebhookAlertIn(title="Single"))
    items = req.items()
    assert len(items) == 1
    assert items[0].title == "Single"


def test_items_with_batch_alerts():
    req = IngestAlertsRequest(
        alerts=[WebhookAlertIn(title="A"), WebhookAlertIn(title="B")]
    )
    items = req.items()
    assert len(items) == 2


def test_items_empty_returns_empty():
    req = IngestAlertsRequest()
    assert req.items() == []


def test_items_alerts_takes_precedence_over_alert():
    req = IngestAlertsRequest(
        alert=WebhookAlertIn(title="Single"),
        alerts=[WebhookAlertIn(title="Batch1")],
    )
    items = req.items()
    assert len(items) == 1
    assert items[0].title == "Batch1"
