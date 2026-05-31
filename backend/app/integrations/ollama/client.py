"""Ollama HTTP client — connectivity and model listing (Phase 0)."""

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OllamaClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.ollama_host.rstrip("/")
        self.llm_model = settings.ollama_llm_model
        self.embed_model = settings.ollama_embed_model

    async def health_check(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                tags_resp = await client.get(f"{self.base_url}/api/tags")
                tags_resp.raise_for_status()
                models = [m.get("name", m.get("model", "")) for m in tags_resp.json().get("models", [])]
                return {
                    "status": "ok",
                    "host": self.base_url,
                    "models_available": models,
                    "expected_llm": self.llm_model,
                    "expected_embed": self.embed_model,
                    "llm_ready": any(self.llm_model in m for m in models),
                    "embed_ready": any(self.embed_model in m for m in models),
                }
        except Exception as exc:
            logger.warning("ollama_health_failed", error=str(exc))
            return {
                "status": "fail",
                "host": self.base_url,
                "error": str(exc),
            }

    async def list_models(self) -> list[str]:
        result = await self.health_check()
        return result.get("models_available", [])
