import pytest
from datetime import datetime, timezone
from app.schemas.alerts import CanonicalAlertSchema
from app.correlation.engine import (
    CorrelationEngine,
    compute_fingerprint,
    compute_time_bucket,
)

def test_compute_fingerprint():
    """Verify SHA-256 fingerprint generation using CanonicalAlertSchema."""
    alert = CanonicalAlertSchema(
        source="firewall",
        title="SSH Brute Force Attempt",
        severity="HIGH",
        detected_at=datetime.now(timezone.utc),
        entities={"ip": "192.168.1.50"},
    )
    fp1 = compute_fingerprint("tenant-123", alert)
    fp2 = compute_fingerprint("tenant-123", alert)
    
    assert isinstance(fp1, str)
    assert len(fp1) == 64
    assert fp1 == fp2

def test_compute_time_bucket():
    """Verify time bucketing rounds down to discrete intervals."""
    dt = datetime(2026, 8, 6, 12, 7, 30, tzinfo=timezone.utc)
    bucket = compute_time_bucket(detected_at=dt, bucket_minutes=5)
    
    assert bucket == "2026-08-06T12:05:00Z"

@pytest.mark.asyncio
async def test_correlation_engine_instantiation():
    """Ensure CorrelationEngine initializes with configured time window."""
    engine = CorrelationEngine(window_minutes=10)
    assert engine.window.total_seconds() == 600
