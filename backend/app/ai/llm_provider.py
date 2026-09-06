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
    async def check_health(self) -> bool:
        """Check if provider service / API key configuration is healthy."""
        pass

    @abstractmethod
    async def check_health_details(self) -> Dict[str, Any]:
        """Return detailed health status dict: available, provider, model, error."""
        pass

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

    async def check_health(self) -> bool:
        details = await self.check_health_details()
        return details["available"]

    async def check_health_details(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url)
                if res.status_code in (200, 204):
                    data = res.json() if res.status_code == 200 else {}
                    models = [m.get("name") for m in data.get("models", []) if isinstance(m, dict)]
                    return {
                        "available": True,
                        "provider": "ollama",
                        "model": self.default_model,
                        "installed_models": models,
                        "error": None,
                    }
                err_msg = f"HTTP_{res.status_code}: {res.text[:150]}"
                logger.error(f"AI Health Check failed for Ollama at {url}: {err_msg}")
                return {
                    "available": False,
                    "provider": "ollama",
                    "model": self.default_model,
                    "error": f"Cannot connect to Ollama at {self.base_url} ({err_msg})",
                }
        except httpx.ConnectError as e:
            err_msg = f"ConnectionError: Cannot connect to Ollama at {self.base_url}"
            logger.error(f"AI extraction health check failed: {err_msg}")
            return {
                "available": False,
                "provider": "ollama",
                "model": self.default_model,
                "error": err_msg,
            }
        except Exception as e:
            logger.exception(f"AI extraction health check exception for Ollama: {str(e)}")
            return {
                "available": False,
                "provider": "ollama",
                "model": self.default_model,
                "error": f"Ollama health check error: {str(e)}",
            }

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
                    err_text = f"OLLAMA_HTTP_{response.status_code}: {response.text[:200]}"
                    logger.error(f"AI extraction failed: {err_text}")
                    return {
                        "content": "",
                        "model": target_model,
                        "client_wall_time_ms": client_wall_time_ms,
                        "error": err_text,
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
            logger.error(f"AI extraction failed: Timeout after {self.timeout}s calling Ollama at {url}")
            return {"content": "", "model": target_model, "client_wall_time_ms": (time.time() - start_wall) * 1000, "error": "OLLAMA_TIMEOUT: Request timed out"}
        except httpx.ConnectError:
            err_msg = f"ConnectionError: Cannot connect to Ollama at {self.base_url}"
            logger.error(f"AI extraction failed:\n{err_msg}")
            return {"content": "", "model": target_model, "client_wall_time_ms": (time.time() - start_wall) * 1000, "error": f"OLLAMA_CONNECTION_REFUSED: {err_msg}"}
        except Exception as e:
            logger.exception(f"AI extraction failed:\n{str(e)}")
            return {"content": "", "model": target_model, "client_wall_time_ms": (time.time() - start_wall) * 1000, "error": f"OLLAMA_ERROR: {str(e)}"}


def clean_api_key(key_str: Optional[str]) -> Optional[str]:
    if not key_str:
        return None
    k = key_str.strip().strip("'").strip('"')
    if k.lower().startswith("bearer "):
        k = k[7:].strip().strip("'").strip('"')
    return k if k else None


class GroqCloudProvider(LLMProvider):
    """Production Cloud LLM Provider using Groq API (OpenAI-compatible API format)."""

    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        raw_key = settings.GROQ_API_KEY or settings.CLOUD_LLM_API_KEY or os.getenv("GROQ_KEY") or os.getenv("LLM_API_KEY")
        self.api_key = clean_api_key(raw_key)
        self.default_model = settings.GROQ_MODEL or "llama-3.1-8b-instant"
        self.timeout = 30.0  # Fast cloud inference timeout

    async def check_health(self) -> bool:
        details = await self.check_health_details()
        return details["available"]

    async def check_health_details(self) -> Dict[str, Any]:
        has_key = bool(self.api_key and self.api_key.strip())
        if not has_key:
            logger.error("AI extraction health check failed: GROQ_API_KEY / CLOUD_LLM_API_KEY is not configured")
            return {
                "available": False,
                "provider": "groq",
                "model": self.default_model,
                "error": "GROQ_API_KEY environment variable is not configured",
            }
        
        # Verify API key validity against Groq Cloud API
        try:
            headers = {"Authorization": f"Bearer {self.api_key.strip()}"}
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get("https://api.groq.com/openai/v1/models", headers=headers)
                if res.status_code == 200:
                    return {
                        "available": True,
                        "provider": "groq",
                        "model": self.default_model,
                        "error": None,
                    }
                elif res.status_code in (401, 403):
                    return {
                        "available": False,
                        "provider": "groq",
                        "model": self.default_model,
                        "error": f"GROQ_AUTH_ERROR ({res.status_code}): Invalid API Key",
                    }
                else:
                    return {
                        "available": False,
                        "provider": "groq",
                        "model": self.default_model,
                        "error": f"GROQ_HTTP_{res.status_code}: {res.text[:100]}",
                    }
        except Exception as e:
            return {
                "available": False,
                "provider": "groq",
                "model": self.default_model,
                "error": f"GROQ_CONNECT_ERROR: {str(e)}",
            }

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


class GeminiCloudProvider(LLMProvider):
    """Production Free Cloud LLM Provider using Google Gemini API."""

    def __init__(self):
        raw_key = settings.GEMINI_API_KEY or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_KEY") or settings.CLOUD_LLM_API_KEY
        self.api_key = clean_api_key(raw_key)
        self.default_model = settings.GEMINI_MODEL or "gemini-flash-lite-latest"
        self.timeout = 30.0

    async def check_health(self) -> bool:
        details = await self.check_health_details()
        return details["available"]

    async def check_health_details(self) -> Dict[str, Any]:
        has_key = bool(self.api_key and self.api_key.strip())
        if not has_key:
            logger.error("AI extraction health check failed: GEMINI_API_KEY / GOOGLE_API_KEY is not configured")
            return {
                "available": False,
                "provider": "gemini",
                "model": self.default_model,
                "error": "GEMINI_API_KEY environment variable is not configured",
            }

        # Verify API key validity against Gemini API models endpoint
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key.strip()}"
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    return {
                        "available": True,
                        "provider": "gemini",
                        "model": self.default_model,
                        "error": None,
                    }
                elif res.status_code in (400, 401, 403):
                    return {
                        "available": False,
                        "provider": "gemini",
                        "model": self.default_model,
                        "error": f"GEMINI_AUTH_ERROR ({res.status_code}): Invalid API Key",
                    }
                else:
                    return {
                        "available": False,
                        "provider": "gemini",
                        "model": self.default_model,
                        "error": f"GEMINI_HTTP_{res.status_code}: {res.text[:100]}",
                    }
        except Exception as e:
            return {
                "available": False,
                "provider": "gemini",
                "model": self.default_model,
                "error": f"GEMINI_CONNECT_ERROR: {str(e)}",
            }

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
            logger.error("GEMINI_API_KEY is not set in environment variables.")
            return {
                "content": "",
                "model": target_model,
                "client_wall_time_ms": 0.0,
                "error": "GEMINI_AUTH_ERROR: GEMINI_API_KEY environment variable is not set",
            }

        model_name = target_model.strip()
        if not model_name.startswith("models/"):
            model_path = f"models/{model_name}"
        else:
            model_path = model_name

        candidate_models = []
        for m in [model_path, "models/gemini-flash-lite-latest", "models/gemini-flash-latest", "models/gemma-4-31b-it"]:
            if m not in candidate_models:
                candidate_models.append(m)

        combined_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": combined_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
            }
        }
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        last_error = None
        for m_path in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/{m_path}:generateContent?key={self.api_key.strip()}"
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.post(url, json=payload)

                client_wall_time_ms = (time.time() - start_wall) * 1000

                if res.status_code == 200:
                    data = res.json()
                    candidates_list = data.get("candidates", [])
                    if candidates_list:
                        parts = candidates_list[0].get("content", {}).get("parts", [])
                        content = ""
                        for part in parts:
                            if isinstance(part, dict) and "text" in part and not part.get("thought"):
                                content += part["text"]
                        if not content and parts:
                            content = parts[-1].get("text", "")

                        return {
                            "content": content,
                            "model": m_path.replace("models/", ""),
                            "client_wall_time_ms": client_wall_time_ms,
                            "error": None,
                        }
                elif res.status_code in (401, 403):
                    return {
                        "content": "",
                        "model": target_model,
                        "client_wall_time_ms": client_wall_time_ms,
                        "error": f"GEMINI_AUTH_ERROR ({res.status_code}): Invalid API Key",
                    }
                else:
                    last_error = f"GEMINI_HTTP_{res.status_code}: {res.text[:150]}"
                    logger.warning(f"Gemini API model {m_path} returned {res.status_code}, trying fallback...")
            except Exception as e:
                last_error = f"GEMINI_ERROR: {str(e)}"
                logger.warning(f"Gemini API model {m_path} exception: {str(e)}, trying fallback...")

        return {
            "content": "",
            "model": target_model,
            "client_wall_time_ms": (time.time() - start_wall) * 1000,
            "error": last_error or "GEMINI_REQUEST_FAILED",
        }


def get_llm_provider() -> LLMProvider:
    """
    Factory function to resolve active LLM provider.
    - If LLM_PROVIDER is 'gemini' -> GeminiCloudProvider (Default Free Cloud Tier)
    - If LLM_PROVIDER is 'groq' -> GroqCloudProvider
    - If LLM_PROVIDER is 'ollama' or OLLAMA_MODE is 'local' -> OllamaLocalProvider
    - Otherwise -> GeminiCloudProvider
    """
    provider_name = (settings.LLM_PROVIDER or "").lower().strip()
    ollama_mode = (settings.OLLAMA_MODE or "").lower().strip()

    if provider_name == "gemini":
        return GeminiCloudProvider()

    if provider_name == "groq":
        return GroqCloudProvider()

    if provider_name == "ollama" or ollama_mode == "local":
        return OllamaLocalProvider()

    return GeminiCloudProvider()
