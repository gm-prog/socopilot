"""Unit tests for app.connectors.generic_json — GenericJsonConnector."""

import pytest
from pydantic import ValidationError

from app.connectors.generic_json import GenericJsonConnector


@pytest.fixture
def connector():
    return GenericJsonConnector()


def test_parse_flat_payload(connector):
    payload = {"title": "Brute force attempt", "severity": "high"}
    alert = connector.parse(payload)
    assert alert.title == "Brute force attempt"
    assert alert.severity == "high"


def test_parse_nested_alert_key(connector):
    payload = {"alert": {"title": "Nested alert", "severity": "low"}}
    alert = connector.parse(payload)
    assert alert.title == "Nested alert"
    assert alert.severity == "low"


def test_parse_batch_with_alerts_key(connector):
    payload = {
        "alerts": [
            {"title": "Alert 1", "severity": "medium"},
            {"title": "Alert 2", "severity": "high"},
        ]
    }
    alerts = connector.parse_batch(payload)
    assert len(alerts) == 2
    assert alerts[0].title == "Alert 1"
    assert alerts[1].title == "Alert 2"


def test_parse_batch_falls_back_to_single(connector):
    payload = {"title": "Single alert", "severity": "low"}
    alerts = connector.parse_batch(payload)
    assert len(alerts) == 1
    assert alerts[0].title == "Single alert"


def test_parse_invalid_payload_raises(connector):
    with pytest.raises(ValidationError):
        connector.parse({"not_a_title": "missing required field"})


def test_connector_name():
    assert GenericJsonConnector.name == "generic_json"
