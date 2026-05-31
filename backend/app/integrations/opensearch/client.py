"""OpenSearch client with PostgreSQL graceful fallback."""

import time
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.integrations.elasticsearch.client import PostgreSQLSearchBackend, SearchBackend

logger = get_logger(__name__)


def get_search_backend() -> SearchBackend:
    settings = get_settings()
    if settings.opensearch_enabled or settings.elasticsearch_enabled:
        return OpenSearchClient()
    return PostgreSQLSearchBackend()


class OpenSearchClient(SearchBackend):
    """OpenSearch indexing — sync methods for Celery, async wrappers for API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.enabled = settings.opensearch_enabled or settings.elasticsearch_enabled
        self.url = settings.search_url
        self.index_alerts = settings.opensearch_index_alerts
        self.index_iocs = settings.opensearch_index_iocs
        self._client = None
        self._fallback = PostgreSQLSearchBackend()

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from opensearchpy import OpenSearch

            self._client = OpenSearch(
                hosts=[self.url],
                use_ssl=False,
                verify_certs=False,
                ssl_show_warn=False,
            )
            return self._client
        except Exception as exc:
            logger.warning("opensearch_client_init_failed", error=str(exc))
            return None

    def ensure_indices(self) -> bool:
        client = self._get_client()
        if client is None:
            return False
        for index in (self.index_alerts, self.index_iocs):
            if not client.indices.exists(index=index):
                client.indices.create(
                    index=index,
                    body={
                        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
                        "mappings": {
                            "properties": {
                                "tenant_id": {"type": "keyword"},
                                "alert_id": {"type": "keyword"},
                                "title": {"type": "text"},
                                "severity": {"type": "keyword"},
                                "detected_at": {"type": "date"},
                                "ioc_type": {"type": "keyword"},
                                "ioc_value": {"type": "keyword"},
                            }
                        },
                    },
                )
        return True

    async def status(self) -> dict:
        if not self.enabled:
            return await self._fallback.status()
        client = self._get_client()
        if client is None:
            return {
                "backend": "opensearch",
                "enabled": True,
                "available": False,
                "message": "OpenSearch client unavailable — using PostgreSQL fallback",
            }
        try:
            health = client.cluster.health()
            return {
                "backend": "opensearch",
                "enabled": True,
                "available": True,
                "url": self.url,
                "cluster_status": health.get("status"),
            }
        except Exception as exc:
            return {
                "backend": "opensearch",
                "enabled": True,
                "available": False,
                "error": str(exc),
            }

    def index_alert_sync(self, alert_id: str, document: dict) -> str | None:
        if not self.enabled:
            return None
        client = self._get_client()
        if client is None:
            return None
        start = time.perf_counter()
        try:
            self.ensure_indices()
            doc = {**document, "alert_id": alert_id}
            resp = client.index(index=self.index_alerts, body=doc, id=alert_id, refresh=False)
            from app.core.metrics import OPENSEARCH_INDEX_LATENCY

            OPENSEARCH_INDEX_LATENCY.observe(time.perf_counter() - start)
            return resp.get("_id")
        except Exception as exc:
            logger.warning("opensearch_index_alert_failed", alert_id=alert_id, error=str(exc))
            return None

    def index_ioc_sync(self, ioc_id: str, document: dict) -> str | None:
        if not self.enabled:
            return None
        client = self._get_client()
        if client is None:
            return None
        try:
            self.ensure_indices()
            resp = client.index(index=self.index_iocs, body=document, id=ioc_id, refresh=False)
            return resp.get("_id")
        except Exception as exc:
            logger.warning("opensearch_index_ioc_failed", error=str(exc))
            return None

    async def index_alert(self, alert_id: str, document: dict) -> str | None:
        return self.index_alert_sync(alert_id, document)

    def search_alerts_sync(self, query: str, tenant_id: str, limit: int = 20) -> list[dict]:
        if not self.enabled:
            return []
        client = self._get_client()
        if client is None:
            return []
        try:
            body: dict[str, Any] = {
                "size": limit,
                "query": {
                    "bool": {
                        "must": [{"term": {"tenant_id": tenant_id}}],
                        "should": [
                            {"match": {"title": query}},
                            {"match": {"description": query}},
                        ],
                        "minimum_should_match": 1,
                    }
                },
            }
            resp = client.search(index=self.index_alerts, body=body)
            return [hit["_source"] for hit in resp.get("hits", {}).get("hits", [])]
        except Exception as exc:
            logger.warning("opensearch_search_failed", error=str(exc))
            return []

    async def search_alerts(self, query: dict, limit: int = 50) -> list[dict]:
        if not self.enabled:
            return await self._fallback.search_alerts(query, limit)
        q = query.get("q", "")
        tenant_id = query.get("tenant_id", "")
        return self.search_alerts_sync(q, tenant_id, limit)
