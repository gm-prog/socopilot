import os
import time
import httpx
import logging
from typing import Any
from app.enrichment.providers.base import EnrichmentProvider, ProviderResult

logger = logging.getLogger(__name__)

class VirusTotalProvider(EnrichmentProvider):
    name: str = "virustotal"
    supported_ioc_types: set[str] = {"ipv4", "ip", "domain", "hash", "md5", "sha1", "sha256", "url"}

    def __init__(self):
        from app.core.config import settings
        self.api_key = settings.virustotal_api_key or os.getenv("VIRUSTOTAL_API_KEY")
        self.enabled = settings.virustotal_enabled
        self.base_url = "https://www.virustotal.com/api/v3"

    def enrich(self, ioc_type: str, ioc_value: str) -> ProviderResult:
        start_time = time.time()

        if not self.supports(ioc_type):
            return ProviderResult(
                provider=self.name,
                status="skipped",
                error_message=f"Unsupported IOC type: {ioc_type}",
                latency_ms=int((time.time() - start_time) * 1000)
            )

        if not self.enabled:
            return ProviderResult(
                provider=self.name,
                status="skipped",
                error_message="Provider is disabled via configuration",
                latency_ms=int((time.time() - start_time) * 1000)
            )

        if not self.api_key:
            logger.warning("VIRUSTOTAL_API_KEY environment variable is missing.")
            return ProviderResult(
                provider=self.name,
                status="skipped",
                error_message="Missing VIRUSTOTAL_API_KEY",
                latency_ms=int((time.time() - start_time) * 1000)
            )

        endpoint_map = {
            "ipv4": f"{self.base_url}/ip_addresses/{ioc_value}",
            "ip": f"{self.base_url}/ip_addresses/{ioc_value}",
            "domain": f"{self.base_url}/domains/{ioc_value}",
            "hash": f"{self.base_url}/files/{ioc_value}",
            "md5": f"{self.base_url}/files/{ioc_value}",
            "sha1": f"{self.base_url}/files/{ioc_value}",
            "sha256": f"{self.base_url}/files/{ioc_value}"
        }

        url = endpoint_map[ioc_type]
        headers = {
            "x-apikey": self.api_key,
            "Accept": "application/json"
        }

        with httpx.Client(timeout=10.0) as client:
            try:
                response = client.get(url, headers=headers)
                latency = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    raw_json = response.json()
                    raw_attrs = raw_json.get("data", {}).get("attributes", {})
                    stats = raw_attrs.get("last_analysis_stats", {})

                    summary_payload = {
                        "malicious": stats.get("malicious", 0),
                        "suspicious": stats.get("suspicious", 0),
                        "harmless": stats.get("harmless", 0),
                        "reputation": raw_attrs.get("reputation", 0),
                        "tags": raw_attrs.get("tags", [])
                    }

                    return ProviderResult(
                        provider=self.name,
                        status="success",
                        summary=summary_payload,
                        raw_response=raw_json,
                        latency_ms=latency
                    )

                elif response.status_code == 404:
                    return ProviderResult(
                        provider=self.name,
                        status="success",
                        summary={"not_found": True},
                        raw_response=response.json() if response.content else None,
                        latency_ms=latency
                    )

                elif response.status_code == 429:
                    return ProviderResult(
                        provider=self.name,
                        status="error",
                        error_message="VirusTotal rate limit exceeded (429)",
                        latency_ms=latency
                    )

                else:
                    return ProviderResult(
                        provider=self.name,
                        status="error",
                        error_message=f"HTTP {response.status_code}: {response.text}",
                        latency_ms=latency
                    )

            except httpx.RequestError as exc:
                logger.error(f"Network error querying VirusTotal for {ioc_value}: {exc}")
                return ProviderResult(
                    provider=self.name,
                    status="error",
                    error_message=str(exc),
                    latency_ms=int((time.time() - start_time) * 1000)
                )
