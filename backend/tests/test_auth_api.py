from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_db
from app.core.security import get_password_hash
from app.main import app


class FakeResult:
    def __init__(self, obj):
        self._obj = obj

    def scalar_one_or_none(self):
        return self._obj


class FakeSession(SimpleNamespace):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.execute = AsyncMock(side_effect=self._execute)
        self.add = lambda _obj: None
        self.flush = AsyncMock()
        self.rollback = AsyncMock()
        self.commit = AsyncMock()

    async def _execute(self, statement):
        sql = str(statement)
        if "FROM tenants" in sql:
            return FakeResult(None)
        if "FROM users" in sql and "WHERE users.email" in sql:
            return FakeResult(self.user)
        if "FROM users" in sql and "WHERE users.id" in sql:
            return FakeResult(self.user)
        return FakeResult(None)


def make_user():
    return SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        email="smoke-test@example.com",
        hashed_password=get_password_hash("Password123!"),
        role="admin",
        is_active=True,
    )


@pytest.mark.asyncio
async def test_auth_register_login_refresh():
    user = make_user()
    fake_session = FakeSession(user)

    async def override_get_db():
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        register_resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": user.email,
                "password": "Password123!",
                "tenant_name": "smoke-test-tenant",
                "role": "admin",
            },
        )
        assert register_resp.status_code == 201
        assert register_resp.json().get("access_token")

        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": user.email,
                "password": "Password123!",
            },
        )
        assert login_resp.status_code == 200
        assert login_resp.json().get("access_token")
        assert "soc_refresh_token" in login_resp.cookies

        refresh_resp = await client.post("/api/v1/auth/refresh")
        assert refresh_resp.status_code == 200
        assert refresh_resp.json().get("access_token")

    app.dependency_overrides.pop(get_db, None)
