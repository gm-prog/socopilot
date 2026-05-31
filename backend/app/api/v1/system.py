"""System info and integration status endpoints."""

from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings
from app.integrations.ollama.client import OllamaClient
from app.integrations.opensearch.client import get_search_backend

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info")
async def system_info() -> dict:
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "app_env": settings.app_env,
        "version": __version__,
        "build_version": settings.build_version,
        "features": {
            "opensearch": settings.opensearch_enabled,
            "elasticsearch": settings.elasticsearch_enabled,
            "ollama_llm_model": settings.ollama_llm_model,
            "ollama_embed_model": settings.ollama_embed_model,
            "abuseipdb": bool(settings.abuseipdb_api_key),
        },
    }


@router.get("/ollama/status")
async def ollama_status() -> dict:
    client = OllamaClient()
    return await client.health_check()


@router.get("/search/backend")
async def search_backend_status() -> dict:
    backend = get_search_backend()
    return await backend.status()


@router.get("/build")
async def build_info() -> dict:
    settings = get_settings()
    return {"version": __version__, "build_version": settings.build_version}
