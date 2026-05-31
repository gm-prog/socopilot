"""Shodan provider stub."""

from app.enrichment.providers.base import EnrichmentProvider, ProviderResult


class ShodanProvider(EnrichmentProvider):
    name = "shodan"
    supported_ioc_types = {"ipv4"}

    def enrich(self, ioc_type: str, ioc_value: str) -> ProviderResult:
        return ProviderResult(
            provider=self.name,
            status="skipped",
            summary={"hostname": None, "ports": [], "stub": True},
            error_message="Shodan stub — configure SHODAN_API_KEY in future",
        )
