"""Threat intel provider interface — stub for Phase 2."""

from abc import ABC, abstractmethod
from typing import Any


class ThreatIntelProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def lookup_ip(self, ip: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def lookup_hash(self, file_hash: str) -> dict[str, Any]:
        pass


class MockThreatIntelProvider(ThreatIntelProvider):
    name = "mock"

    async def lookup_ip(self, ip: str) -> dict[str, Any]:
        return {"provider": self.name, "ip": ip, "malicious": False, "score": 0}

    async def lookup_hash(self, file_hash: str) -> dict[str, Any]:
        return {"provider": self.name, "hash": file_hash, "malicious": False, "score": 0}
