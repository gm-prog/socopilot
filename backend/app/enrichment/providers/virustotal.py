"""VirusTotal provider stub."""

from app.enrichment.providers.base import EnrichmentProvider, ProviderResult


class VirusTotalProvider(EnrichmentProvider):
    name = "virustotal"
    supported_ioc_types = {"md5", "sha1", "sha256", "domain", "url", "ipv4"}

    def enrich(self, ioc_type: str, ioc_value: str) -> ProviderResult:
        return ProviderResult(
            provider=self.name,
            status="skipped",
            summary={"stub": True, "ioc_type": ioc_type, "ioc_value": ioc_value},
            error_message="VirusTotal integration planned — stub only",
        )
