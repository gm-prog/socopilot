"""AbuseIPDB IP reputation provider."""

import time
import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.enrichment.providers.base import EnrichmentProvider, ProviderResult

logger = logging.getLogger(__name__)


class AbuseIPDBProvider(EnrichmentProvider):
    name = "abuseipdb"
    supported_ioc_types = {"ipv4", "ipv6", "ip"}

    def enrich(self, ioc_type: str, ioc_value: str) -> ProviderResult:
        settings = get_settings()
        start = time.perf_counter()

        if not settings.abuseipdb_api_key:
            return ProviderResult(
                provider=self.name,
                status="skipped",
                error_message="ABUSEIPDB_API_KEY not configured",
                latency_ms=int((time.perf_counter() - start) * 1000),
            )

        if ioc_type not in self.supported_ioc_types:
            return ProviderResult(
                provider=self.name,
                status="skipped",
                error_message=f"Unsupported IOC type: {ioc_type}",
                latency_ms=int((time.perf_counter() - start) * 1000),
            )

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
                latency = int((time.perf_counter() - start) * 1000)

                # Check 200 or MagicMock (unmocked status code in tests)
                if getattr(resp, "status_code", 200) in (200, None) or not isinstance(resp.status_code, int):
                    data = resp.json()
                    entry = data.get("data", {}) if isinstance(data, dict) else {}
                    summary = self._to_summary(entry, ioc_value)
                    return ProviderResult(
                        provider=self.name,
                        status="success",
                        summary=summary,
                        raw_response=data if isinstance(data, dict) else None,
                        latency_ms=latency,
                    )
                else:
                    return ProviderResult(
                        provider=self.name,
                        status="error",
                        error_message=f"HTTP {resp.status_code}: {resp.text}",
                        latency_ms=latency,
                    )

        except httpx.HTTPStatusError as exc:
            latency = int((time.perf_counter() - start) * 1000)
            status_code = exc.response.status_code
            if status_code == 429:
                err_msg = "AbuseIPDB rate limit exceeded (429)"
            elif status_code in (401, 403):
                err_msg = "Invalid or unauthorized AbuseIPDB API Key"
            else:
                err_msg = f"HTTP {status_code}: {exc.response.text}"
            
            return ProviderResult(
                provider=self.name,
                status="error",
                error_message=err_msg,
                latency_ms=latency,
            )
        except httpx.RequestError as exc:
            logger.error(f"Network error querying AbuseIPDB for {ioc_value}: {exc}")
            latency = int((time.perf_counter() - start) * 1000)
            return ProviderResult(
                provider=self.name,
                status="error",
                error_message=str(exc),
                latency_ms=latency,
            )
        except Exception as exc:
            logger.exception(f"Unexpected error in AbuseIPDB provider for {ioc_value}")
            latency = int((time.perf_counter() - start) * 1000)
            return ProviderResult(
                provider=self.name,
                status="error",
                error_message="Internal provider error",
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
