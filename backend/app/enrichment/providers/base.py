"""Enrichment provider abstraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderResult:
    provider: str
    status: str  # success | error | skipped
    summary: dict[str, Any] = field(default_factory=dict)
    raw_response: dict[str, Any] | None = None
    error_message: str | None = None
    latency_ms: int = 0


class EnrichmentProvider(ABC):
    name: str = "base"
    supported_ioc_types: set[str] = set()

    @abstractmethod
    def enrich(self, ioc_type: str, ioc_value: str) -> ProviderResult:
        pass

    def supports(self, ioc_type: str) -> bool:
        return ioc_type in self.supported_ioc_types
