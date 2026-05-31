"""Pytest fixtures."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import CurrentUser, get_current_user
from app.main import app


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
async def auth_client(tenant_id, user_id):
    async def override_user():
        return CurrentUser(
            {
                "sub": str(user_id),
                "tenant_id": str(tenant_id),
                "role": "admin",
                "type": "access",
            }
        )

    app.dependency_overrides[get_current_user] = override_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
