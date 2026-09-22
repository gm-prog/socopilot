"""OpenSearch integration."""

from app.integrations.opensearch.client import OpenSearchClient, get_search_backend

__all__ = ["OpenSearchClient", "get_search_backend"]
