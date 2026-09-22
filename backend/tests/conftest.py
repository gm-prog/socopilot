"""
Pytest configuration and global fixtures.
Blocks all external network calls (Redis, OpenSearch, Ollama) by default.
"""

from unittest.mock import AsyncMock, MagicMock
import pytest

# ==========================================
# 1. MOCK FIXTURES FOR EXTERNAL CLIENTS
# ==========================================

@pytest.fixture
def mock_redis(mocker):
    """Mocks RedisPublisher including its context manager (__enter__/__exit__)."""
    mock = MagicMock()
    mock.connect.return_value = mock
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = None

    mock.publish_alert_created.return_value = 1
    mock.publish_alert_enriched.return_value = 1
    mock.publish_alert_status.return_value = 1

    mocker.patch("app.services.redis_publisher.RedisPublisher", return_value=mock)
    return mock


@pytest.fixture
def mock_async_redis_client(mocker):
    """Mocks async Redis client for token revocation blacklisting."""
    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    mock_client.close.return_value = None
    mocker.patch("app.core.redis.get_redis_client", return_value=mock_client)
    return mock_client


@pytest.fixture
def mock_opensearch(mocker):
    """Mocks OpenSearchClient with both sync and async operations."""
    mock = MagicMock()

    mock.ensure_indices.return_value = True
    mock.index_alert_sync.return_value = "mock-alert-id"
    mock.index_ioc_sync.return_value = "mock-ioc-id"
    mock.search_alerts_sync.return_value = []

    mock.status = AsyncMock(return_value={"available": True, "backend": "opensearch", "enabled": True})
    mock.index_alert = AsyncMock(return_value="mock-alert-id")
    mock.search_alerts = AsyncMock(return_value=[])

    mocker.patch("app.integrations.opensearch.client.OpenSearchClient", return_value=mock)
    mocker.patch("app.integrations.opensearch.client.get_search_backend", return_value=mock)
    return mock


@pytest.fixture
def mock_ollama_integration(mocker):
    """Mocks Phase 0 Ollama connectivity client."""
    mock = MagicMock()

    mock.health_check = AsyncMock(return_value={"status": "ok", "llm_ready": True, "embed_ready": True})
    mock.list_models = AsyncMock(return_value=["mistral:7b-instruct", "nomic-embed-text"])
    mock.generate_text = AsyncMock(return_value="Mocked async generation response")

    mock.generate_text_sync.return_value = "Mocked sync generation response"

    mocker.patch("app.integrations.ollama.client.OllamaClient", return_value=mock)
    return mock


@pytest.fixture
def mock_ollama_service(mocker):
    """Mocks the Ollama service client including async context managers."""
    mock = MagicMock()

    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=None)

    mock.get_embedding = AsyncMock(return_value=[0.1] * 768)
    mock.batch_embeddings = AsyncMock(return_value=[[0.1] * 768])
    mock.generate_insights = AsyncMock(return_value="Mocked AI enrichment insights")

    mocker.patch("app.services.ollama_client.OllamaClient", return_value=mock)
    return mock


# ==========================================
# 2. GLOBAL AUTO-USE SAFETY FIXTURE
# ==========================================

@pytest.fixture(autouse=True)
def block_external_services(
    mock_redis,
    mock_async_redis_client,
    mock_opensearch,
    mock_ollama_integration,
    mock_ollama_service
):
    """
    SAFETY NET: Runs automatically before EVERY test to prevent network calls.
    """
    yield

# ==========================================
# 3. COMMON API & DB TEST FIXTURES
# ==========================================

import uuid
from httpx import AsyncClient, ASGITransport

@pytest.fixture
def tenant_id():
    """Returns a consistent mock tenant UUID."""
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def mock_db_session():
    """Mocks a SQLAlchemy database session with chainable execute results."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalars.return_value.first.return_value = None
    mock_result.first.return_value = None
    session.execute = AsyncMock(return_value=mock_result)

    return session


@pytest.fixture
async def auth_client(mock_db_session, tenant_id):
    """
    Async TestClient configured for authenticated API requests.
    Overrides DB and authentication dependencies cleanly.
    """
    from app.main import app
    from app.core.dependencies import get_db

    async def _get_db_override():
        yield mock_db_session

    app.dependency_overrides[get_db] = _get_db_override

    try:
        from app.core.dependencies import get_current_user
        from types import SimpleNamespace
        async def _get_current_user_override():
            return SimpleNamespace(
                id=str(uuid.UUID("22222222-2222-2222-2222-222222222222")),
                tenant_id=tenant_id,
                email="analyst@socopilot.local",
                role="analyst",
                is_active=True
            )
        app.dependency_overrides[get_current_user] = _get_current_user_override
    except (ImportError, AttributeError):
        pass

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": "Bearer mock-test-token"}
    ) as client:
        yield client

    app.dependency_overrides.clear()
