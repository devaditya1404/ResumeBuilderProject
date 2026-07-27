"""
Ollama & Provider Compatibility Adapter for TalentVault AI.

Routes requests through `get_llm_provider()` factory while maintaining exact
function signatures for backward compatibility across existing services.
"""
import json
import time
import logging
import httpx
from typing import Optional, Dict, Any, List
import asyncio

from app.core.config import settings
from app.ai.llm_provider import get_llm_provider, OllamaLocalProvider, GroqCloudProvider

logger = logging.getLogger(__name__)


async def check_ollama_health() -> bool:
    """Check if AI Provider (Local Ollama or Cloud API) is reachable."""
    provider = get_llm_provider()
    if isinstance(provider, OllamaLocalProvider):
        try:
            url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                return response.status_code in (200, 204)
        except Exception:
            return False
    else:
        # Cloud API check
        return bool(settings.GROQ_API_KEY or settings.CLOUD_LLM_API_KEY)


async def list_models() -> List[str]:
    """List available models for current active provider."""
    provider = get_llm_provider()
    if isinstance(provider, OllamaLocalProvider):
        try:
            url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return [settings.OLLAMA_MODEL or "qwen2.5:3b"]
    else:
        return [settings.GROQ_MODEL or "llama-3.1-8b-instant"]


async def get_best_model() -> str:
    """Get default model for active provider."""
    provider = get_llm_provider()
    if isinstance(provider, OllamaLocalProvider):
        return settings.OLLAMA_MODEL or "qwen2.5:3b"
    return settings.GROQ_MODEL or "llama-3.1-8b-instant"


async def chat_completion(
    prompt: str,
    system_prompt: str = "",
    model: Optional[str] = None,
    temperature: float = 0.1,
    json_mode: bool = True,
) -> Dict[str, Any]:
    """
    Send chat completion request to active LLMProvider.
    """
    provider = get_llm_provider()
    return await provider.chat_completion(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
        temperature=temperature,
        json_mode=json_mode,
    )
