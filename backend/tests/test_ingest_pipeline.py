"""SOC v2 ingestion pipeline unit tests."""

from app.services.event_normalizer import normalize_event
from app.services.ioc_extractor import extract_iocs
from app.services.severity import calculate_severity
from app.workers.tasks.ingest import run_process_ingest_event

SAMPLE_EVENT = {
    "source": "firewall",
    "event_type": "login_attempt",
    "payload": {
        "ip": "8.8.8.8",
        "user": "admin",
        "status": "failed",
    },
}


def test_normalize_event_does_not_mutate_input():
    event = {
        "source": "firewall",
        "event_type": "login_attempt",
        "payload": {"ip": "8.8.8.8", "status": "failed"},
    }
    original = {"source": "firewall", "event_type": "login_attempt", "payload": {"ip": "8.8.8.8", "status": "failed"}}
    event_copy = {
        "source": "firewall",
        "event_type": "login_attempt",
        "payload": {"ip": "8.8.8.8", "status": "failed"},
    }
    result = normalize_event(event_copy)
    assert result["source"] == "firewall"
    assert result["event_type"] == "login_attempt"
    assert result["payload"]["ip"] == "8.8.8.8"
    assert event_copy == original


def test_extract_iocs_from_sample_event():
    normalized = normalize_event(SAMPLE_EVENT)
    iocs = extract_iocs(normalized["payload"])
    assert "8.8.8.8" in iocs["ips"]
    assert isinstance(iocs["domains"], list)
    assert isinstance(iocs["urls"], list)
    assert isinstance(iocs["hashes"], list)


def test_severity_scoring_for_failed_login():
    normalized = normalize_event(SAMPLE_EVENT)
    iocs = extract_iocs(normalized["payload"])
    severity = calculate_severity(normalized, iocs)
    assert 1 <= severity <= 10
    assert severity >= 7


def test_run_process_ingest_event_structure():
    result = run_process_ingest_event(SAMPLE_EVENT)
    assert result["status"] == "processed"
    assert result["source"] == "firewall"
    assert result["event_type"] == "login_attempt"
    assert "event_id" in result
    assert result["iocs"]["ips"] == ["8.8.8.8"]
    assert isinstance(result["severity"], int)
    assert "received_at" in result["timestamps"]
    assert "processed_at" in result["timestamps"]


def test_extract_hashes_sha256():
    sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    payload = {"message": f"file hash {sha256}"}
    iocs = extract_iocs(payload)
    assert sha256 in iocs["hashes"]


def test_unknown_source_increases_severity():
    normalized = normalize_event(
        {
            "source": "mystery_sensor",
            "event_type": "heartbeat",
            "payload": {},
        }
    )
    iocs = extract_iocs(normalized["payload"])
    severity = calculate_severity(normalized, iocs)
    assert severity >= 4
