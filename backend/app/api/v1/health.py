"""Health and readiness endpoints."""

import httpx
import redis.asyncio as aioredis
from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.schemas.health import HealthResponse, ReadinessCheck, ReadinessResponse
from app.workers.celery_app import celery_app

router = APIRouter(tags=["health"])


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
        checks.append(ReadinessCheck(name="postgresql", status="fail", detail=str(exc)))

    # Redis
    try:
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await client.ping()
        await client.aclose()
        checks.append(ReadinessCheck(name="redis", status="ok"))
    except Exception as exc:
        checks.append(ReadinessCheck(name="redis", status="fail", detail=str(exc)))

    # Celery broker reachability
    try:
        conn = celery_app.connection()
        conn.ensure_connection(max_retries=1)
        conn.release()
        checks.append(ReadinessCheck(name="celery_broker", status="ok"))
    except Exception as exc:
        checks.append(ReadinessCheck(name="celery_broker", status="fail", detail=str(exc)))

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
        checks.append(ReadinessCheck(name="ollama", status="fail", detail=str(exc)))

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
            checks.append(ReadinessCheck(name="opensearch", status="degraded", detail=str(exc)))

    overall = "ok" if all(c.status == "ok" for c in checks) else "degraded"
    if any(c.status == "fail" for c in checks):
        overall = "fail"

    return ReadinessResponse(status=overall, checks=checks)
