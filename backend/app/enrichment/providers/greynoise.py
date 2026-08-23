import os
import time
import httpx
import logging
from app.enrichment.providers.base import EnrichmentProvider, ProviderResult

logger = logging.getLogger(__name__)

class GreyNoiseProvider(EnrichmentProvider):
    name: str = "greynoise"
    supported_ioc_types: set[str] = {"ipv4", "ip"}

    def __init__(self):
        from app.core.config import settings
        self.api_key = settings.greynoise_api_key or os.getenv("GREYNOISE_API_KEY")
        self.enabled = settings.greynoise_enabled
        self.base_url = "https://api.greynoise.io/v3/community"

    def enrich(self, ioc_type: str, ioc_value: str) -> ProviderResult:
        start_time = time.time()

        if not self.supports(ioc_type):
            return ProviderResult(
                provider=self.name,
                status="skipped",
                summary={"stub": True, "noise": False, "riot": False, "classification": "not_found"},
                error_message=f"Unsupported IOC type: {ioc_type}",
                latency_ms=int((time.time() - start_time) * 1000)
            )

        if not self.enabled:
            return ProviderResult(
                provider=self.name,
                status="skipped",
                summary={"stub": True, "noise": False, "riot": False, "classification": "not_found"},
                error_message="Provider is disabled via configuration",
                latency_ms=int((time.time() - start_time) * 1000)
            )

        if not self.api_key:
            logger.warning("GREYNOISE_API_KEY environment variable is missing.")
            return ProviderResult(
                provider=self.name,
                status="skipped",
                summary={"stub": True, "noise": False, "riot": False, "classification": "not_found"},
                error_message="Missing GREYNOISE_API_KEY",
                latency_ms=int((time.time() - start_time) * 1000)
            )

        url = f"{self.base_url}/{ioc_value}"
        headers = {
            "key": self.api_key,
            "Accept": "application/json"
        }

        with httpx.Client(timeout=10.0) as client:
            try:
                response = client.get(url, headers=headers)
                latency = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    raw_json = response.json()
                    summary_payload = {
                        "noise": raw_json.get("noise", False),
                        "riot": raw_json.get("riot", False),
                        "classification": raw_json.get("classification", "unknown"),
                        "actor": raw_json.get("actor", "unknown"),
                        "last_seen": raw_json.get("last_seen", None)
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
                        summary={"noise": False, "riot": False, "classification": "not_found"},
                        raw_response=response.json() if response.content else None,
                        latency_ms=latency
                    )

                elif response.status_code == 401:
                    return ProviderResult(
                        provider=self.name,
                        status="error",
                        error_message="Invalid or unauthorized GreyNoise API Key",
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
                logger.error(f"Network error querying GreyNoise for {ioc_value}: {exc}")
                return ProviderResult(
                    provider=self.name,
                    status="error",
                    error_message=str(exc),
                    latency_ms=int((time.time() - start_time) * 1000)
                )
