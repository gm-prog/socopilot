"""AbuseIPDB IP reputation provider."""

import time
from typing import Any

import httpx

from app.core.config import get_settings
from app.enrichment.providers.base import EnrichmentProvider, ProviderResult


class AbuseIPDBProvider(EnrichmentProvider):
    name = "abuseipdb"
    supported_ioc_types = {"ipv4", "ipv6"}

    def enrich(self, ioc_type: str, ioc_value: str) -> ProviderResult:
        settings = get_settings()
        if not settings.abuseipdb_api_key:
            return ProviderResult(
                provider=self.name,
                status="skipped",
                error_message="ABUSEIPDB_API_KEY not configured",
            )
        if ioc_type not in self.supported_ioc_types:
            return ProviderResult(
                provider=self.name,
                status="skipped",
                error_message=f"Unsupported IOC type: {ioc_type}",
            )

        start = time.perf_counter()
        try:
            with httpx.Client(timeout=settings.enrichment_timeout_seconds) as client:
                resp = client.get(
                    "https://api.abuseipdb.com/api/v2/check",
                    headers={
                        "Key": settings.abuseipdb_api_key,
                        "Accept": "application/json",
                    },
                    params={"ipAddress": ioc_value, "maxAgeInDays": 90},
                )
                resp.raise_for_status()
                data = resp.json()
            latency = int((time.perf_counter() - start) * 1000)
            entry = data.get("data", {})
            summary = self._to_summary(entry, ioc_value)
            return ProviderResult(
                provider=self.name,
                status="success",
                summary=summary,
                raw_response=data,
                latency_ms=latency,
            )
        except Exception as exc:
            latency = int((time.perf_counter() - start) * 1000)
            return ProviderResult(
                provider=self.name,
                status="error",
                error_message=str(exc),
                latency_ms=latency,
            )

    def _to_summary(self, entry: dict[str, Any], ip: str) -> dict[str, Any]:
        return {
            "ip": ip,
            "abuse_confidence": entry.get("abuseConfidenceScore", 0),
            "country": entry.get("countryCode"),
            "isp": entry.get("isp"),
            "domain": entry.get("domain"),
            "total_reports": entry.get("totalReports", 0),
            "is_tor": entry.get("isTor", False),
            "is_whitelisted": entry.get("isWhitelisted", False),
            "last_reported_at": entry.get("lastReportedAt"),
            "usage_type": entry.get("usageType"),
        }
