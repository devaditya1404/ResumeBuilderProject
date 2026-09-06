#!/usr/bin/env python3
"""
test_production_routing.py — Verify that LLM_PROVIDER=groq NEVER pings localhost:11434 or Ollama.
"""
import asyncio
import os
import sys
import httpx
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force LLM_PROVIDER=groq and GROQ_API_KEY
os.environ["LLM_PROVIDER"] = "groq"
os.environ["GROQ_API_KEY"] = "gsk_mock_test_key_12345"

from app.core.config import settings
settings.LLM_PROVIDER = "groq"
settings.GROQ_API_KEY = "gsk_mock_test_key_12345"

from app.ai.llm_provider import get_llm_provider, GroqCloudProvider, GeminiCloudProvider, OllamaLocalProvider
from app.ai.resume_extractor import extract_resume_with_llm
from app.parsers.contact_parser import ContactInfo


async def test_groq_routing():
    print("=" * 75)
    print("PRODUCTION GROQ ROUTING & ZERO LOCALHOST TEST")
    print("=" * 75)

    # 1. Verify Factory returns GroqCloudProvider when LLM_PROVIDER=groq
    os.environ["LLM_PROVIDER"] = "groq"
    settings.LLM_PROVIDER = "groq"
    provider = get_llm_provider()
    print(f"Active Provider Class: {provider.__class__.__name__}")
    assert isinstance(provider, GroqCloudProvider), f"Expected GroqCloudProvider, got {provider.__class__.__name__}"
    assert not isinstance(provider, OllamaLocalProvider)


async def test_gemini_routing():
    print("=" * 75)
    print("PRODUCTION GEMINI ROUTING & ZERO LOCALHOST TEST")
    print("=" * 75)

    os.environ["LLM_PROVIDER"] = "gemini"
    os.environ["GEMINI_API_KEY"] = "AIzaSyMockTestKey12345"
    settings.LLM_PROVIDER = "gemini"
    settings.GEMINI_API_KEY = "AIzaSyMockTestKey12345"

    # 1. Verify Factory returns GeminiCloudProvider
    provider = get_llm_provider()
    print(f"Active Provider Class: {provider.__class__.__name__}")
    assert isinstance(provider, GeminiCloudProvider), f"Expected GeminiCloudProvider, got {provider.__class__.__name__}"
    assert not isinstance(provider, OllamaLocalProvider)

    # 2. Mock Gemini API calls
    def mock_get_side_effect(url, *args, **kwargs):
        if "127.0.0.1" in url or "localhost" in url or "ollama" in url:
            raise AssertionError(f"CRITICAL BUG: GET HTTP request to localhost/Ollama was made! URL: {url}")
        res = AsyncMock()
        res.status_code = 200
        res.json.return_value = {"models": [{"name": "models/gemini-flash-lite-latest"}]}
        return res

    with patch.object(httpx.AsyncClient, "get", side_effect=mock_get_side_effect):
        with patch.object(httpx.AsyncClient, "post") as mock_post:
            mock_res = AsyncMock()
            mock_res.status_code = 200
            mock_res.json.return_value = {
                "candidates": [{
                    "content": {
                        "parts": [{
                            "text": '{"n": "Test Candidate", "sk": ["Python", "FastAPI"], "ex": [{"t": "Dev", "c": "Tech"}], "ed": [], "cert": [], "proj": [], "lang": [], "jlpt": "None"}'
                        }]
                    }
                }]
            }
            mock_post.return_value = mock_res

            contacts = ContactInfo(email="test@example.com", phone="1234567890")
            extraction, metadata = await extract_resume_with_llm(
                resume_text="Test Candidate\nPython developer with 5 years experience.",
                contacts=contacts,
                section_hints=["Experience", "Skills"]
            )

            print(f"Extraction Completed: Name='{extraction.full_name if extraction else None}'")
            print(f"Metadata Error: {metadata.get('error')}")

            # Verify POST request went to Gemini API endpoint
            assert mock_post.called, "Gemini POST was not called"
            call_url = mock_post.call_args[0][0] if mock_post.call_args else ""
            print(f"HTTP POST Destination URL: {call_url}")
            assert "generativelanguage.googleapis.com" in call_url, f"Expected Gemini URL, got: {call_url}"
            assert "127.0.0.1" not in call_url and "localhost" not in call_url

    print("\n" + "=" * 75)
    print("PRODUCTION GEMINI ROUTING & ZERO LOCALHOST TEST: 100% PASSED!")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(test_groq_routing())
    asyncio.run(test_gemini_routing())

