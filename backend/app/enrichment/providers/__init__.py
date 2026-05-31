"""Threat intel provider registry."""

from app.enrichment.providers.abuseipdb import AbuseIPDBProvider
from app.enrichment.providers.base import EnrichmentProvider, ProviderResult
from app.enrichment.providers.greynoise import GreyNoiseProvider
from app.enrichment.providers.shodan import ShodanProvider
from app.enrichment.providers.virustotal import VirusTotalProvider

PROVIDER_REGISTRY: dict[str, type[EnrichmentProvider]] = {
    "abuseipdb": AbuseIPDBProvider,
    "virustotal": VirusTotalProvider,
    "greynoise": GreyNoiseProvider,
    "shodan": ShodanProvider,
}


def get_provider(name: str) -> EnrichmentProvider:
    cls = PROVIDER_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown provider: {name}")
    return cls()
