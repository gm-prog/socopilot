"""Elasticsearch client abstraction — disabled until Phase 2."""

from abc import ABC, abstractmethod

from app.core.config import get_settings


class SearchBackend(ABC):
    @abstractmethod
    async def status(self) -> dict:
        pass

    @abstractmethod
    async def index_alert(self, alert_id: str, document: dict) -> str | None:
        pass

    @abstractmethod
    async def search_alerts(self, query: dict, limit: int = 50) -> list[dict]:
        pass


class PostgreSQLSearchBackend(SearchBackend):
    """Phase 0/1: alerts stored and queried via PostgreSQL only."""

    async def status(self) -> dict:
        return {
            "backend": "postgresql",
            "enabled": True,
            "message": "Primary search backend (Elasticsearch disabled)",
        }

    async def index_alert(self, alert_id: str, document: dict) -> str | None:
        return None

    async def search_alerts(self, query: dict, limit: int = 50) -> list[dict]:
        return []


class ElasticsearchClient(SearchBackend):
    """Phase 2 implementation stub."""

    def __init__(self) -> None:
        settings = get_settings()
        self.enabled = settings.elasticsearch_enabled
        self.url = settings.elasticsearch_url
        self._fallback = PostgreSQLSearchBackend()

    async def status(self) -> dict:
        if not self.enabled:
            return await self._fallback.status()
        return {
            "backend": "elasticsearch",
            "enabled": True,
            "url": self.url,
            "message": "Not implemented in Phase 0",
        }

    async def index_alert(self, alert_id: str, document: dict) -> str | None:
        if not self.enabled:
            return None
        raise NotImplementedError("Elasticsearch indexing available in Phase 2")

    async def search_alerts(self, query: dict, limit: int = 50) -> list[dict]:
        if not self.enabled:
            return await self._fallback.search_alerts(query, limit)
        raise NotImplementedError("Elasticsearch search available in Phase 2")
