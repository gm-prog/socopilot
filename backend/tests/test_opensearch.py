"""OpenSearch client fallback tests."""

import pytest

from app.integrations.opensearch.client import OpenSearchClient, PostgreSQLSearchBackend, get_search_backend


@pytest.mark.asyncio
async def test_fallback_when_disabled():
    backend = PostgreSQLSearchBackend()
    status = await backend.status()
    assert status["backend"] == "postgresql"


@pytest.mark.asyncio
async def test_index_noop_when_disabled():
    backend = PostgreSQLSearchBackend()
    assert await backend.index_alert("id", {}) is None
