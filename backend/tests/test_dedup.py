"""Deduplication and fingerprint unit tests."""

from datetime import UTC, datetime

from app.dedup.fingerprint import compute_fingerprint, compute_time_bucket
from app.schemas.alerts import CanonicalAlertSchema


def test_fingerprint_stable_for_same_content():
    tenant = "00000000-0000-0000-0000-000000000001"
    alert = CanonicalAlertSchema(
        source="webhook",
        title="Test Alert",
        severity="medium",
        detected_at=datetime(2026, 5, 26, 12, 0, tzinfo=UTC),
        rule_id="rule-1",
        entities={"hosts": ["h1"]},
    )
    fp1 = compute_fingerprint(tenant, alert)
    fp2 = compute_fingerprint(tenant, alert)
    assert fp1 == fp2
    assert len(fp1) == 64


def test_fingerprint_differs_for_different_tenant():
    alert = CanonicalAlertSchema(
        source="webhook",
        title="Test",
        severity="low",
        detected_at=datetime(2026, 5, 26, 12, 0, tzinfo=UTC),
    )
    fp1 = compute_fingerprint("tenant-a", alert)
    fp2 = compute_fingerprint("tenant-b", alert)
    assert fp1 != fp2


def test_time_bucket_15_minute_floor():
    dt = datetime(2026, 5, 26, 12, 7, 30, tzinfo=UTC)
    bucket = compute_time_bucket(dt, bucket_minutes=15)
    assert bucket == "2026-05-26T12:00:00Z"

    dt2 = datetime(2026, 5, 26, 12, 16, 0, tzinfo=UTC)
    bucket2 = compute_time_bucket(dt2, bucket_minutes=15)
    assert bucket2 == "2026-05-26T12:15:00Z"
