"""
Ollama HTTP Client supporting both Local and Ollama Cloud API modes.

Handles:
- Health check (Local tags endpoint or Cloud status)
- Bearer token authorization header for Ollama Cloud API
- Chat completion with JSON mode & compact extraction
- Specific error taxonomy: OLLAMA_AUTH_ERROR, OLLAMA_RATE_LIMIT, OLLAMA_TIMEOUT, OLLAMA_CLOUD_ERROR
"""
import json
import time
import logging
import httpx
from typing import Optional, Dict, Any, List

import asyncio
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global lock: maximum 1 concurrent Ollama LLM call allowed at a time
OLLAMA_LOCK = asyncio.Lock()


def get_ollama_headers() -> Dict[str, str]:
    """Build request headers for Local vs Ollama Cloud API mode."""
    headers = {"Content-Type": "application/json"}
    if settings.OLLAMA_MODE == "cloud" or settings.OLLAMA_API_KEY:
        if settings.OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {settings.OLLAMA_API_KEY}"
    return headers


def get_base_url() -> str:
    """Return configured Ollama base URL cleanly without trailing slash."""
    url = settings.OLLAMA_BASE_URL.rstrip("/")
    return url


async def check_ollama_health() -> bool:
    """Check if Ollama (Local or Cloud API) is reachable."""
    try:
        url = f"{get_base_url()}/api/tags"
        headers = get_ollama_headers()
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=headers)
            return response.status_code in (200, 204)
    except Exception:
        # In cloud mode with API key, assume reachable if key is provided
        if settings.OLLAMA_MODE == "cloud" and settings.OLLAMA_API_KEY:
            return True
        return False


async def list_models() -> List[str]:
    """List available models in Ollama."""
    try:
        url = f"{get_base_url()}/api/tags"
        headers = get_ollama_headers()
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
    # If list models endpoint fails or returns empty, fallback to configured settings.OLLAMA_MODEL
    return [settings.OLLAMA_MODEL]


async def get_best_model() -> str:
    """Get the configured model or best available model in Ollama."""
    if settings.OLLAMA_MODEL:
        return settings.OLLAMA_MODEL

    models = await list_models()
    return models[0] if models else "qwen2.5:3b"


async def chat_completion(
    prompt: str,
    system_prompt: str = "",
    model: Optional[str] = None,
    temperature: float = 0.1,
    json_mode: bool = True,
) -> Dict[str, Any]:
    """
    Send a chat completion request to Ollama (Local or Cloud API).

    Returns a dict with:
    - "content": the raw text response
    - "model": model used
    - "client_wall_time_ms": processing time in ms
    - "error": error code/message if failed (or None if success)
    """
    if model is None:
        model = await get_best_model()

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
            "num_predict": settings.OLLAMA_NUM_PREDICT,
        },
    }

    if json_mode:
        payload["format"] = "json"

    headers = get_ollama_headers()
    api_url = f"{get_base_url()}/api/chat"
    timeout_seconds = settings.OLLAMA_TIMEOUT_SECONDS

    try:
        async with OLLAMA_LOCK:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(
                    api_url,
                    json=payload,
                    headers=headers,
                )

            client_wall_time_ms = (time.time() - start_wall) * 1000

            # Error taxonomy handling
            if response.status_code in (401, 403):
                logger.error(f"Ollama Auth Error [{response.status_code}]: {response.text[:200]}")
                return {
                    "content": "",
                    "model": model,
                    "client_wall_time_ms": client_wall_time_ms,
                    "error": "OLLAMA_AUTH_ERROR",
                }

            if response.status_code == 429:
                logger.warning(f"Ollama Rate Limit Exceeded: {response.text[:200]}")
                return {
                    "content": "",
                    "model": model,
                    "client_wall_time_ms": client_wall_time_ms,
                    "error": "OLLAMA_RATE_LIMIT",
                }

            if response.status_code >= 500:
                logger.error(f"Ollama Cloud Server Error [{response.status_code}]: {response.text[:200]}")
                return {
                    "content": "",
                    "model": model,
                    "client_wall_time_ms": client_wall_time_ms,
                    "error": f"OLLAMA_CLOUD_ERROR ({response.status_code})",
                }

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
        return {
            "content": "",
            "model": model,
            "client_wall_time_ms": (time.time() - start_wall) * 1000,
            "error": "OLLAMA_TIMEOUT",
        }
    except httpx.ConnectError:
        return {
            "content": "",
            "model": model,
            "client_wall_time_ms": (time.time() - start_wall) * 1000,
            "error": "OLLAMA_CONNECTION_REFUSED",
        }
    except Exception as e:
        return {
            "content": "",
            "model": model,
            "client_wall_time_ms": (time.time() - start_wall) * 1000,
            "error": f"OLLAMA_ERROR: {str(e)}",
        }
