import asyncio
from app.services.ollama_client import OllamaClient

async def get_embedding_async(text: str) -> list[float]:
    """Generate 768-dimensional embedding asynchronously."""
    cleaned_text = text.replace("\n", " ") if text else ""
    async with OllamaClient() as client:
        return await client.get_embedding(cleaned_text)

def get_embedding(text: str) -> list[float]:
    """Synchronous fallback wrapper for background tasks."""
    try:
        return asyncio.run(get_embedding_async(text))
    except Exception:
        return [0.0] * 768
