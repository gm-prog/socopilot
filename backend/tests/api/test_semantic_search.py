import sys
from unittest.mock import AsyncMock, MagicMock
import pytest

# 1. Inject missing dependencies/stubs before import
mock_user_schema = AsyncMock()
sys.modules["app.schemas.user"] = mock_user_schema

mock_model_obj = AsyncMock()
import app.services.embedding as embedding_module
embedding_module.model = mock_model_obj

# Define dummy fallback dependency
def dummy_get_current_user():
    pass

import app.core.security as security_module
if not hasattr(security_module, "get_current_user"):
    security_module.get_current_user = dummy_get_current_user

# 2. Import FastAPI app and search module
from fastapi.testclient import TestClient
from app.main import app
import app.api.v1.semantic_search as semantic_search_module
from app.db.session import get_db

client = TestClient(app)


@pytest.fixture
def mock_user():
    user = AsyncMock()
    user.id = 1
    user.tenant_id = "tenant-123"
    return user


@pytest.fixture
def override_deps(mock_user):
    def _get_current_user_override():
        return mock_user

    mock_db = AsyncMock()
    def _get_db_override():
        yield mock_db

    # Extract exact route dependency reference for user auth
    route = next(r for r in app.routes if getattr(r, "path", None) == "/api/v1/search/semantic")
    user_dep = next(
        d.call for d in route.dependant.dependencies
        if d.name == "user" or d.call.__name__ == "get_current_user"
    )

    app.dependency_overrides[user_dep] = _get_current_user_override
    app.dependency_overrides[get_db] = _get_db_override
    yield mock_db
    app.dependency_overrides.clear()


def test_semantic_search_missing_query(override_deps):
    response = client.post(
        "/api/v1/search/semantic",
        json={},
        headers={"Authorization": "Bearer mock_token"}
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_semantic_search_success(override_deps):
    mock_db = override_deps

    mock_vector = AsyncMock()
    mock_vector.tolist.return_value = [0.1, 0.2, 0.3]
    mock_model_obj.encode.return_value = mock_vector

    # Standard synchronous database row
    mock_row = MagicMock()
    mock_row.alert_id = 101
    mock_row.distance = 0.1234

    # Synchronous result mock for .all()
    mock_result = MagicMock()
    mock_result.all.return_value = [mock_row]
    mock_db.execute.return_value = mock_result

    response = client.post(
        "/api/v1/search/semantic",
        json={"query": "unauthorized login", "limit": 5},
        headers={"Authorization": "Bearer mock_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["alert_id"] == "101"
    assert data["results"][0]["score"] == 0.8766
