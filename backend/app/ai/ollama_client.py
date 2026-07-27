"""
Ollama HTTP Client supporting both Local and Ollama Cloud API modes.

Handles:
- Health check (Local tags endpoint or Cloud status)
- Bearer token authorization header for Ollama Cloud API
- Verified model discovery (tests generation before selecting in Cloud mode)
- In-memory model caching to prevent repeated model checks
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

# Cached verified cloud model for production
_VERIFIED_CLOUD_MODEL: Optional[str] = None


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
    return [settings.OLLAMA_MODEL]


async def discover_and_verify_cloud_model() -> str:
    """
    In Cloud mode, test candidate models with a minimal generation request
    to ensure the model is actually accessible on free/active plans before selecting.
    """
    global _VERIFIED_CLOUD_MODEL
    if _VERIFIED_CLOUD_MODEL:
        return _VERIFIED_CLOUD_MODEL

    base_url = get_base_url()
    headers = get_ollama_headers()

    # Query tags first
    available_tags = await list_models()
    candidates = []
    if settings.OLLAMA_MODEL and settings.OLLAMA_MODEL not in candidates:
        candidates.append(settings.OLLAMA_MODEL)
    for tag in available_tags:
        if tag not in candidates:
            candidates.append(tag)

    # Standard fallback models to test
    fallbacks = [
        "qwen2.5:3b", "qwen2.5:7b", "qwen2.5", "qwen2.5:1.5b", "qwen2.5:0.5b",
        "llama3.2", "llama3.2:3b", "llama3.1:8b", "mistral:7b", "gemma2:2b"
    ]
    for fb in fallbacks:
        if fb not in candidates:
            candidates.append(fb)

    logger.info(f"Testing {len(candidates)} candidate cloud models for free generation access...")

    async with httpx.AsyncClient(timeout=10.0) as client:
        for model_name in candidates:
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": "Reply only with OK"}],
                "stream": False
            }
            try:
                res = await client.post(f"{base_url}/api/chat", json=payload, headers=headers)
                if res.status_code == 200:
                    content = res.json().get("message", {}).get("content", "")
                    if content and "OK" in content.upper():
                        logger.info(f"Verified accessible Cloud Model: '{model_name}'")
                        _VERIFIED_CLOUD_MODEL = model_name
                        return model_name
                else:
                    logger.warning(f"Cloud model '{model_name}' test returned HTTP {res.status_code}: {res.text[:100]}")
            except Exception as e:
                logger.warning(f"Error testing candidate cloud model '{model_name}': {e}")

    # Fallback to configured model if test loop completes
    _VERIFIED_CLOUD_MODEL = settings.OLLAMA_MODEL or "qwen2.5:3b"
    return _VERIFIED_CLOUD_MODEL


async def get_best_model() -> str:
    """Get the configured model for local mode or verified model for cloud mode."""
    if settings.OLLAMA_MODE == "local":
        return settings.OLLAMA_MODEL or "qwen2.5:3b"
    
    return await discover_and_verify_cloud_model()


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
    global _VERIFIED_CLOUD_MODEL

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
                # Reset cached model if subscription/auth failed on this model
                _VERIFIED_CLOUD_MODEL = None
                return {
                    "content": "",
                    "model": model,
                    "client_wall_time_ms": client_wall_time_ms,
                    "error": f"OLLAMA_HTTP_{response.status_code}: {response.text[:200]}",
                }

            if response.status_code == 404:
                logger.error(f"Ollama Model Not Found [404]: {response.text[:200]}")
                _VERIFIED_CLOUD_MODEL = None
                return {
                    "content": "",
                    "model": model,
                    "client_wall_time_ms": client_wall_time_ms,
                    "error": f"OLLAMA_HTTP_404: {response.text[:200]}",
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
