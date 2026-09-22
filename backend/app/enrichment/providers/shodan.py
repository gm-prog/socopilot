import os
import time
import httpx
import logging
from app.enrichment.providers.base import EnrichmentProvider, ProviderResult

logger = logging.getLogger(__name__)

class ShodanProvider(EnrichmentProvider):
    name: str = "shodan"
    supported_ioc_types: set[str] = {"ipv4", "ip"}

    def __init__(self):
        from app.core.config import settings
        self.api_key = settings.shodan_api_key or os.getenv("SHODAN_API_KEY")
        self.enabled = settings.shodan_enabled
        # Uses InternetDB public endpoint (free, no paid key required)
        self.base_url = "https://internetdb.shodan.io"

    def enrich(self, ioc_type: str, ioc_value: str) -> ProviderResult:
        start_time = time.time()

        if not self.supports(ioc_type):
            return ProviderResult(
                provider=self.name,
                status="skipped",
                summary={"stub": True, "ports": [], "hostnames": [], "vulns": []},
                error_message=f"Unsupported IOC type: {ioc_type}",
                latency_ms=int((time.time() - start_time) * 1000)
            )

        if not self.enabled:
            return ProviderResult(
                provider=self.name,
                status="skipped",
                summary={"stub": True, "ports": [], "hostnames": [], "vulns": []},
                error_message="Provider is disabled via configuration",
                latency_ms=int((time.time() - start_time) * 1000)
            )

        url = f"{self.base_url}/{ioc_value}"

        with httpx.Client(timeout=10.0) as client:
            try:
                response = client.get(url)
                latency = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    raw_json = response.json()
                    summary_payload = {
                        "ports": raw_json.get("ports", []),
                        "cpes": raw_json.get("cpes", []),
                        "hostnames": raw_json.get("hostnames", []),
                        "tags": raw_json.get("tags", []),
                        "vulns": raw_json.get("vulns", [])
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
                        summary={"ports": [], "hostnames": [], "vulns": []},
                        raw_response={"message": "No host information found"},
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
                logger.error(f"Network error querying Shodan InternetDB for {ioc_value}: {exc}")
                return ProviderResult(
                    provider=self.name,
                    status="error",
                    error_message=str(exc),
                    latency_ms=int((time.time() - start_time) * 1000)
                )
