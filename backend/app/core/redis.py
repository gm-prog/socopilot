"""Redis client utility for token revocation and caching."""

import redis.asyncio as aioredis
from app.core.config import get_settings

settings = get_settings()
_redis_client: aioredis.Redis | None = None


async def get_redis_client() -> aioredis.Redis:
    """Return a singleton async Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis_client() -> None:
    """Close active Redis connection pool on application shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


async def blacklist_jti(jti: str, expire_seconds: int) -> None:
    """Store revoked token JTI with expiration matching remaining token lifetime."""
    if expire_seconds <= 0:
        return
    client = await get_redis_client()
    await client.setex(name=f"denied_jti:{jti}", time=expire_seconds, value="revoked")


async def is_jti_blacklisted(jti: str) -> bool:
    """Check whether token JTI exists in revocation list."""
    client = await get_redis_client()
    value = await client.get(f"denied_jti:{jti}")
    return value is not None
