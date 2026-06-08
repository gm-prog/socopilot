"""Health and readiness endpoints."""

import httpx
import redis.asyncio as aioredis
from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.schemas.health import HealthResponse, ReadinessCheck, ReadinessResponse
from app.workers.celery_app import celery_app

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


def _safe_error(exc: Exception) -> str:
    """Return a generic error type without leaking hostnames, ports, or stack traces."""
    return type(exc).__name__


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="socopilot-api", version=__version__)


@router.get("/ready", response_model=ReadinessResponse)
async def readiness() -> ReadinessResponse:
    settings = get_settings()
    checks: list[ReadinessCheck] = []

    # PostgreSQL
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks.append(ReadinessCheck(name="postgresql", status="ok"))
    except Exception as exc:
        logger.warning("readiness_postgresql_failed", error=str(exc))
        checks.append(ReadinessCheck(name="postgresql", status="fail", detail=_safe_error(exc)))

    # Redis
    try:
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await client.ping()
        await client.aclose()
        checks.append(ReadinessCheck(name="redis", status="ok"))
    except Exception as exc:
        logger.warning("readiness_redis_failed", error=str(exc))
        checks.append(ReadinessCheck(name="redis", status="fail", detail=_safe_error(exc)))

    # Celery broker reachability
    try:
        conn = celery_app.connection()
        conn.ensure_connection(max_retries=1)
        conn.release()
        checks.append(ReadinessCheck(name="celery_broker", status="ok"))
    except Exception as exc:
        logger.warning("readiness_celery_failed", error=str(exc))
        checks.append(ReadinessCheck(name="celery_broker", status="fail", detail=_safe_error(exc)))

    # Ollama
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_host.rstrip('/')}/api/tags")
            if resp.status_code == 200:
                checks.append(ReadinessCheck(name="ollama", status="ok"))
            else:
                checks.append(
                    ReadinessCheck(
                        name="ollama",
                        status="degraded",
                        detail=f"HTTP {resp.status_code}",
                    )
                )
    except Exception as exc:
        logger.warning("readiness_ollama_failed", error=str(exc))
        checks.append(ReadinessCheck(name="ollama", status="fail", detail=_safe_error(exc)))

    if settings.opensearch_enabled or settings.elasticsearch_enabled:
        try:
            from app.integrations.opensearch.client import get_search_backend

            os_status = await get_search_backend().status()
            if os_status.get("available"):
                checks.append(ReadinessCheck(name="opensearch", status="ok"))
            else:
                checks.append(
                    ReadinessCheck(
                        name="opensearch",
                        status="degraded",
                        detail=os_status.get("error") or os_status.get("message", "unavailable"),
                    )
                )
        except Exception as exc:
            logger.warning("readiness_opensearch_failed", error=str(exc))
            checks.append(ReadinessCheck(name="opensearch", status="degraded", detail=_safe_error(exc)))

    overall = "ok" if all(c.status == "ok" for c in checks) else "degraded"
    if any(c.status == "fail" for c in checks):
        overall = "fail"

    return ReadinessResponse(status=overall, checks=checks)
