import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

BASE_URL = "http://testserver"

@pytest.fixture
async def client():
    """Async HTTP client fixture configured for FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url=BASE_URL
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login and token generation."""
    login_payload = {
        "email": "admin@example.com",
        "password": "changeme123"
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data.get("token_type") == "bearer"


@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient):
    """Test /auth/me endpoint with a valid Bearer token."""
    login_payload = {
        "email": "admin@example.com",
        "password": "changeme123"
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == "admin@example.com"
    assert "id" in user_data
    assert "role" in user_data


@pytest.mark.asyncio
async def test_get_me_missing_token(client: AsyncClient):
    """Test /auth/me without Authorization header (should return 401)."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient):
    """Test /auth/me with malformed/invalid token (should return 401)."""
    headers = {"Authorization": "Bearer invalid_token_xyz_123"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
