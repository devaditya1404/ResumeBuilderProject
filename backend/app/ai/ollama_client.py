"""
Local Ollama HTTP client.

Handles:
- Health check (is Ollama running?)
- Model availability check
- Chat completion with JSON mode
- Timeout and error handling
"""
import json
import time
import logging
import httpx
from typing import Optional, Dict, Any

import asyncio
from app.core.config import settings

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = settings.OLLAMA_BASE_URL
OLLAMA_TIMEOUT_SECONDS = float(getattr(settings, "OLLAMA_TIMEOUT_SECONDS", 120.0))
REQUEST_TIMEOUT = OLLAMA_TIMEOUT_SECONDS  # 120 seconds max

# Global lock: maximum 1 concurrent Ollama LLM call allowed at a time
OLLAMA_LOCK = asyncio.Lock()


async def check_ollama_health() -> bool:
    """Check if Ollama is running and reachable."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


async def list_models() -> list:
    """List available models in Ollama."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
    return []


async def get_best_model() -> Optional[str]:
    """
    Get the configured model or best available model in Ollama.
    """
    models = await list_models()
    if not models:
        return None

    # First check if configured model exists
    target = settings.OLLAMA_MODEL.lower()
    for available in models:
        if target in available.lower():
            return available

    # Fall back to first available model
    return models[0]


async def chat_completion(
    prompt: str,
    system_prompt: str = "",
    model: Optional[str] = None,
    temperature: float = 0.1,
    json_mode: bool = True,
) -> Dict[str, Any]:
    """
    Send a chat completion request to Ollama.

    Returns a dict with:
    - "content": the raw text response
    - "model": model used
    - "total_duration_ms": processing time
    - "error": error message if failed
    """
    if model is None:
        model = await get_best_model()
        if model is None:
            return {"content": "", "model": "", "error": "NO_MODEL_AVAILABLE"}

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    start_wall = time.time()
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": getattr(settings, "OLLAMA_NUM_PREDICT", 1536),
        },
    }

    if json_mode:
        payload["format"] = "json"

    try:
        async with OLLAMA_LOCK:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/chat",
                    json=payload,
                )

            client_wall_time_ms = (time.time() - start_wall) * 1000

            if response.status_code != 200:
                return {
                    "content": "",
                    "model": model,
                    "client_wall_time_ms": client_wall_time_ms,
                    "error": f"OLLAMA_HTTP_{response.status_code}: {response.text[:200]}",
                }

            data = response.json()
            content = data.get("message", {}).get("content", "")

            return {
                "content": content,
                "model": model,
                "client_wall_time_ms": client_wall_time_ms,
                "total_duration_ms": (data.get("total_duration") or 0) / 1_000_000,
                "load_duration_ms": (data.get("load_duration") or 0) / 1_000_000,
                "prompt_eval_count": data.get("prompt_eval_count", 0),
                "prompt_eval_duration_ms": (data.get("prompt_eval_duration") or 0) / 1_000_000,
                "eval_count": data.get("eval_count", 0),
                "eval_duration_ms": (data.get("eval_duration") or 0) / 1_000_000,
                "error": None,
            }

    except httpx.TimeoutException:
        return {"content": "", "model": model, "client_wall_time_ms": (time.time() - start_wall) * 1000, "error": "OLLAMA_TIMEOUT"}
    except httpx.ConnectError:
        return {"content": "", "model": model, "client_wall_time_ms": (time.time() - start_wall) * 1000, "error": "OLLAMA_CONNECTION_REFUSED"}
    except Exception as e:
        return {"content": "", "model": model, "client_wall_time_ms": (time.time() - start_wall) * 1000, "error": f"OLLAMA_ERROR: {str(e)}"}
