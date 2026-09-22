"""MITRE mapping and detection engine tests."""

from app.detection.engine import DetectionEngine
from app.mitre.mapping import map_mitre_techniques
from app.services.event_normalizer import normalize_event


def test_mitre_brute_force_mapping():
    normalized = normalize_event(
        {
            "source": "firewall",
            "event_type": "login_attempt",
            "payload": {"status": "failed"},
        }
    )
    techniques = map_mitre_techniques(normalized)
    ids = {t["id"] for t in techniques}
    assert "T1110" in ids


def test_mitre_powershell_mapping():
    normalized = normalize_event(
        {
            "source": "edr",
            "event_type": "process",
            "payload": {"command": "powershell -enc abc"},
        }
    )
    techniques = map_mitre_techniques(normalized)
    ids = {t["id"] for t in techniques}
    assert "T1059.001" in ids


def test_detection_engine_powershell_rule():
    normalized = normalize_event(
        {
            "source": "edr",
            "event_type": "powershell_exec",
            "payload": {},
        }
    )
    matches = DetectionEngine().evaluate(normalized, context={"failed_login_count": 0})
    assert any(m.rule_id == "suspicious_powershell" for m in matches)
