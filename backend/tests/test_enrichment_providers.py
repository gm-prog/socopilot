"""Unit tests for enrichment provider stubs and base class."""

from app.enrichment.providers.base import EnrichmentProvider, ProviderResult
from app.enrichment.providers.greynoise import GreyNoiseProvider
from app.enrichment.providers.shodan import ShodanProvider


# ---- ProviderResult dataclass ----

def test_provider_result_defaults():
    r = ProviderResult(provider="test", status="success")
    assert r.summary == {}
    assert r.raw_response is None
    assert r.error_message is None
    assert r.latency_ms == 0


# ---- base EnrichmentProvider.supports ----

def test_supports_matching_type():
    class DummyProvider(EnrichmentProvider):
        name = "dummy"
        supported_ioc_types = {"ipv4", "domain"}

        def enrich(self, ioc_type: str, ioc_value: str) -> ProviderResult:
            return ProviderResult(provider=self.name, status="skipped")

    p = DummyProvider()
    assert p.supports("ipv4") is True
    assert p.supports("domain") is True
    assert p.supports("sha256") is False


# ---- GreyNoise provider ----

def test_greynoise_metadata():
    p = GreyNoiseProvider()
    assert p.name == "greynoise"
    assert "ipv4" in p.supported_ioc_types


def test_greynoise_supports():
    p = GreyNoiseProvider()
    assert p.supports("ipv4") is True
    assert p.supports("md5") is False


def test_greynoise_enrich_returns_skipped():
    result = GreyNoiseProvider().enrich("ipv4", "8.8.8.8")
    assert result.status == "skipped"
    assert result.summary["stub"] is True
    assert "classification" in result.summary


# ---- Shodan provider ----

def test_shodan_metadata():
    p = ShodanProvider()
    assert p.name == "shodan"
    assert "ipv4" in p.supported_ioc_types


def test_shodan_supports():
    p = ShodanProvider()
    assert p.supports("ipv4") is True
    assert p.supports("email") is False


def test_shodan_enrich_returns_skipped():
    result = ShodanProvider().enrich("ipv4", "1.2.3.4")
    assert result.status == "skipped"
    assert result.summary["stub"] is True
    assert "ports" in result.summary
