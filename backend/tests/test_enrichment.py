"""Enrichment provider tests."""

from unittest.mock import MagicMock, patch

from app.enrichment.providers.abuseipdb import AbuseIPDBProvider
from app.enrichment.providers.virustotal import VirusTotalProvider


def test_abuseipdb_skipped_without_key():
    with patch("app.enrichment.providers.abuseipdb.get_settings") as mock_settings:
        mock_settings.return_value.abuseipdb_api_key = ""
        result = AbuseIPDBProvider().enrich("ipv4", "203.0.113.1")
    assert result.status == "skipped"


@patch("app.enrichment.providers.abuseipdb.httpx.Client")
def test_abuseipdb_success(mock_client_cls):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": {
            "abuseConfidenceScore": 85,
            "countryCode": "US",
            "isp": "Example ISP",
            "totalReports": 10,
            "isTor": False,
        }
    }
    mock_resp.raise_for_status = MagicMock()
    mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp

    with patch("app.enrichment.providers.abuseipdb.get_settings") as mock_settings:
        mock_settings.return_value.abuseipdb_api_key = "test-key"
        mock_settings.return_value.enrichment_timeout_seconds = 10
        result = AbuseIPDBProvider().enrich("ipv4", "203.0.113.1")

    assert result.status == "success"
    assert result.summary["abuse_confidence"] == 85


def test_virustotal_stub():
    result = VirusTotalProvider().enrich("md5", "a" * 32)
    assert result.status == "skipped"
