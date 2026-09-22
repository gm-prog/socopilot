"""Async HTTP client for Ollama embeddings and LLM inference."""

import json
from typing import Any

import httpx
from app.core.logging import get_logger

logger = get_logger(__name__)

OLLAMA_BASE_URL = "http://ollama:11434"
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "mistral:7b-instruct"


class OllamaClient:
    """Async HTTP wrapper for Ollama API calls."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, timeout: float = 120.0):
        self.base_url = base_url
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "OllamaClient":
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def get_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for text using nomic-embed-text model.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector as list of floats.

        Raises:
            ValueError: If Ollama API call fails.
        """
        if not self._client:
            raise RuntimeError("OllamaClient not initialized. Use async context manager.")

        payload = {"model": EMBEDDING_MODEL, "prompt": text}

        try:
            response = await self._client.post("/api/embeddings", json=payload)
            response.raise_for_status()
            data = response.json()
            embedding = data.get("embedding", [])
            if not embedding:
                logger.warning("ollama_empty_embedding", text_len=len(text))
            return embedding
        except httpx.HTTPError as exc:
            logger.error(
                "ollama_embedding_failed",
                error=str(exc),
                status=exc.response.status_code if hasattr(exc, "response") else None,
            )
            raise ValueError(f"Ollama embedding failed: {exc}") from exc

    async def generate_insights(self, prompt: str) -> str:
        """
        Generate structured insights using Mistral 7B Instruct.

        Args:
            prompt: Prompt for the LLM.

        Returns:
            Generated text response.

        Raises:
            ValueError: If Ollama API call fails.
        """
        if not self._client:
            raise RuntimeError("OllamaClient not initialized. Use async context manager.")

        payload = {
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.3,
        }

        try:
            response = await self._client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            text = data.get("response", "").strip()
            if not text:
                logger.warning("ollama_empty_response", prompt_len=len(prompt))
            return text
        except httpx.HTTPError as exc:
            logger.error("ollama_generate_failed", error=str(exc))
            raise ValueError(f"Ollama LLM generation failed: {exc}") from exc

    async def batch_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts (sequential).

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        embeddings = []
        for text in texts:
            try:
                emb = await self.get_embedding(text)
                embeddings.append(emb)
            except ValueError as exc:
                logger.warning("batch_embedding_skip", error=str(exc))
                embeddings.append([])
        return embeddings
