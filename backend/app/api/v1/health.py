"""Health and readiness endpoints."""

import asyncio

import redis.asyncio as aioredis
from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app import __version__
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.schemas.health import SubsystemHealthResponse
from app.workers.celery_app import celery_app

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


def _safe_error(exc: Exception) -> str:
    """Return a generic error type without leaking hostnames, ports, or stack traces."""
    return type(exc).__name__


async def _check_database() -> str:
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return "ok"


async def _check_redis() -> str:
    settings = get_settings()
    client = aioredis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
    try:
        await client.ping()
        return "ok"
    finally:
        await client.aclose()


def _ping_celery_workers() -> str:
    inspector = celery_app.control.inspect(timeout=2)
    responses = inspector.ping()
    if not responses:
        raise RuntimeError("no celery workers responded")
    return "ok"


async def _check_celery() -> str:
    return await asyncio.to_thread(_ping_celery_workers)


@router.get("/health", response_model=SubsystemHealthResponse)
async def health(response: Response) -> SubsystemHealthResponse:
    checks: dict[str, str] = {}

    for name, check in (
        ("database", _check_database),
        ("redis", _check_redis),
        ("celery", _check_celery),
    ):
        try:
            checks[name] = await check()
        except Exception as exc:
            logger.warning("health_check_failed", subsystem=name, error=str(exc))
            checks[name] = f"error: {_safe_error(exc)}"

    overall = "ok" if all(value == "ok" for value in checks.values()) else "down"
    if overall != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return SubsystemHealthResponse(status=overall, checks=checks, version=__version__)


@router.get("/ready", response_model=SubsystemHealthResponse)
async def readiness(response: Response) -> SubsystemHealthResponse:
    return await health(response)
