"""GreyNoise provider stub."""

from app.enrichment.providers.base import EnrichmentProvider, ProviderResult


class GreyNoiseProvider(EnrichmentProvider):
    name = "greynoise"
    supported_ioc_types = {"ipv4"}

    def enrich(self, ioc_type: str, ioc_value: str) -> ProviderResult:
        return ProviderResult(
            provider=self.name,
            status="skipped",
            summary={"classification": "unknown", "noise": False, "stub": True},
            error_message="GreyNoise stub — configure GREYNOISE_API_KEY in future",
        )
