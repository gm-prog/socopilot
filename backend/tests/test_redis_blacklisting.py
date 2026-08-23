from unittest.mock import AsyncMock
import pytest
from app.core.redis import blacklist_jti, is_jti_blacklisted


@pytest.mark.asyncio
async def test_blacklist_jti_sets_key(mocker):
    mock_client = AsyncMock()
    mocker.patch("app.core.redis.get_redis_client", return_value=mock_client)

    await blacklist_jti("test-jti-123", 300)
    mock_client.setex.assert_called_once_with(name="denied_jti:test-jti-123", time=300, value="revoked")


@pytest.mark.asyncio
async def test_is_jti_blacklisted_returns_true(mocker):
    mock_client = AsyncMock()
    mock_client.get.return_value = "revoked"
    mocker.patch("app.core.redis.get_redis_client", return_value=mock_client)

    result = await is_jti_blacklisted("test-jti-123")
    assert result is True
    mock_client.get.assert_called_once_with("denied_jti:test-jti-123")


@pytest.mark.asyncio
async def test_is_jti_blacklisted_returns_false(mocker):
    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mocker.patch("app.core.redis.get_redis_client", return_value=mock_client)

    result = await is_jti_blacklisted("test-jti-456")
    assert result is False
