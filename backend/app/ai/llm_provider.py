"""
LLM Provider Abstraction Layer for TalentVault AI.

Defines the abstract base class `LLMProvider` and concrete implementations:
- OllamaLocalProvider (for local development using Ollama qwen2.5:3b)
- GroqCloudProvider (for fast production cloud inference using OpenAI-compatible Groq API)

Exposes `get_llm_provider()` factory and `chat_completion()` wrapper.
"""
from abc import ABC, abstractmethod
import json
import time
import logging
import httpx
from typing import Optional, Dict, Any, List
import asyncio

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global lock to limit concurrent calls if needed
PROVIDER_LOCK = asyncio.Lock()


class LLMProvider(ABC):
    """Abstract Base Class for all LLM providers."""

    @abstractmethod
    async def chat_completion(
        self,
        prompt: str,
        system_prompt: str = "",
        model: Optional[str] = None,
        temperature: float = 0.1,
        json_mode: bool = True,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to the provider.

        Returns dict:
        - "content": str (text or JSON output)
        - "model": str (model name used)
        - "client_wall_time_ms": float (duration)
        - "error": Optional[str] (error tag/message or None)
        """
        pass


class OllamaLocalProvider(LLMProvider):
    """Local Ollama provider implementation (http://127.0.0.1:11434)."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.default_model = settings.OLLAMA_MODEL or "qwen2.5:3b"
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS

    async def chat_completion(
        self,
        prompt: str,
        system_prompt: str = "",
        model: Optional[str] = None,
        temperature: float = 0.1,
        json_mode: bool = True,
    ) -> Dict[str, Any]:
        target_model = model or self.default_model
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": settings.OLLAMA_NUM_PREDICT,
            },
        }
        if json_mode:
            payload["format"] = "json"

        start_wall = time.time()
        url = f"{self.base_url}/api/chat"

        try:
            async with PROVIDER_LOCK:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload)
                client_wall_time_ms = (time.time() - start_wall) * 1000

                if response.status_code != 200:
                    return {
                        "content": "",
                        "model": target_model,
                        "client_wall_time_ms": client_wall_time_ms,
                        "error": f"OLLAMA_HTTP_{response.status_code}: {response.text[:200]}",
                    }

                data = response.json()
                content = data.get("message", {}).get("content", "")
                return {
                    "content": content,
                    "model": target_model,
                    "client_wall_time_ms": client_wall_time_ms,
                    "error": None,
                }
        except httpx.TimeoutException:
            return {"content": "", "model": target_model, "client_wall_time_ms": (time.time() - start_wall) * 1000, "error": "OLLAMA_TIMEOUT"}
        except httpx.ConnectError:
            return {"content": "", "model": target_model, "client_wall_time_ms": (time.time() - start_wall) * 1000, "error": "OLLAMA_CONNECTION_REFUSED"}
        except Exception as e:
            return {"content": "", "model": target_model, "client_wall_time_ms": (time.time() - start_wall) * 1000, "error": f"OLLAMA_ERROR: {str(e)}"}


class GroqCloudProvider(LLMProvider):
    """Production Cloud LLM Provider using Groq API (OpenAI-compatible API format)."""

    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.api_key = settings.GROQ_API_KEY or settings.CLOUD_LLM_API_KEY
        self.default_model = settings.GROQ_MODEL or "llama-3.1-8b-instant"
        self.timeout = 30.0  # Fast cloud inference timeout

    async def chat_completion(
        self,
        prompt: str,
        system_prompt: str = "",
        model: Optional[str] = None,
        temperature: float = 0.1,
        json_mode: bool = True,
    ) -> Dict[str, Any]:
        target_model = model or self.default_model
        start_wall = time.time()

        if not self.api_key or not self.api_key.strip():
            logger.error("GROQ_API_KEY / CLOUD_LLM_API_KEY is not set in environment variables.")
            return {
                "content": "",
                "model": target_model,
                "client_wall_time_ms": 0.0,
                "error": "GROQ_AUTH_ERROR: GROQ_API_KEY environment variable is not set",
            }

        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1536,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.api_url, json=payload, headers=headers)

            client_wall_time_ms = (time.time() - start_wall) * 1000

            if response.status_code in (401, 403):
                logger.error(f"Groq API Auth Error [{response.status_code}]: {response.text[:200]}")
                return {
                    "content": "",
                    "model": target_model,
                    "client_wall_time_ms": client_wall_time_ms,
                    "error": f"GROQ_AUTH_ERROR ({response.status_code}): Invalid API Key",
                }

            if response.status_code == 429:
                logger.warning(f"Groq API Rate Limit Exceeded [429]: {response.text[:200]}")
                return {
                    "content": "",
                    "model": target_model,
                    "client_wall_time_ms": client_wall_time_ms,
                    "error": "GROQ_RATE_LIMIT",
                }

            if response.status_code != 200:
                logger.error(f"Groq API Error [{response.status_code}]: {response.text[:200]}")
                return {
                    "content": "",
                    "model": target_model,
                    "client_wall_time_ms": client_wall_time_ms,
                    "error": f"GROQ_HTTP_{response.status_code}: {response.text[:200]}",
                }

            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            return {
                "content": content,
                "model": target_model,
                "client_wall_time_ms": client_wall_time_ms,
                "error": None,
            }

        except httpx.TimeoutException:
            return {"content": "", "model": target_model, "client_wall_time_ms": (time.time() - start_wall) * 1000, "error": "GROQ_TIMEOUT"}
        except Exception as e:
            return {"content": "", "model": target_model, "client_wall_time_ms": (time.time() - start_wall) * 1000, "error": f"GROQ_ERROR: {str(e)}"}


def get_llm_provider() -> LLMProvider:
    """
    Factory function to resolve active LLM provider.
    - If LLM_PROVIDER is 'ollama' or OLLAMA_MODE is 'local' -> OllamaLocalProvider
    - Otherwise -> GroqCloudProvider (Cloud Production LLM)
    """
    provider_name = settings.LLM_PROVIDER.lower()
    ollama_mode = settings.OLLAMA_MODE.lower()

    if provider_name == "ollama" or ollama_mode == "local":
        return OllamaLocalProvider()
    
    return GroqCloudProvider()
