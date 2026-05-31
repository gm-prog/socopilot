"""Health probe tasks for Celery connectivity verification."""

import httpx

from app.core.config import get_settings
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.health.ping")
def ping() -> dict:
    return {"status": "pong", "service": "socopilot-worker"}


@celery_app.task(name="app.workers.tasks.health.check_ollama")
def check_ollama() -> dict:
    settings = get_settings()
    try:
        resp = httpx.get(f"{settings.ollama_host.rstrip('/')}/api/tags", timeout=10.0)
        resp.raise_for_status()
        models = [m.get("name", "") for m in resp.json().get("models", [])]
        return {"status": "ok", "models": models}
    except Exception as exc:
        return {"status": "fail", "error": str(exc)}
