#!/usr/bin/env python3
"""
test_production_routing.py — Verify that LLM_PROVIDER=groq NEVER pings localhost:11434 or Ollama.
"""
import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force LLM_PROVIDER=groq and GROQ_API_KEY
os.environ["LLM_PROVIDER"] = "groq"
os.environ["GROQ_API_KEY"] = "gsk_mock_test_key_12345"

from app.core.config import settings
settings.LLM_PROVIDER = "groq"
settings.GROQ_API_KEY = "gsk_mock_test_key_12345"

from app.ai.llm_provider import get_llm_provider, GroqCloudProvider, OllamaLocalProvider
from app.ai.resume_extractor import extract_resume_with_llm
from app.parsers.contact_parser import ContactInfo


async def test_groq_routing():
    print("=" * 75)
    print("PRODUCTION GROQ ROUTING & ZERO LOCALHOST TEST")
    print("=" * 75)

    # 1. Verify Factory returns GroqCloudProvider
    provider = get_llm_provider()
    print(f"Active Provider Class: {provider.__class__.__name__}")
    assert isinstance(provider, GroqCloudProvider), f"Expected GroqCloudProvider, got {provider.__class__.__name__}"
    assert not isinstance(provider, OllamaLocalProvider)

    # 2. Mock GroqCloudProvider.chat_completion to prevent network calls
    mock_json_res = {
        "content": '{"n": "Test Candidate", "exp": [], "edu": [], "sk": ["Python"]}',
        "model": "llama-3.1-8b-instant",
        "client_wall_time_ms": 150.0,
        "error": None
    }

    with patch.object(httpx.AsyncClient, "get", side_effect=AssertionError("CRITICAL BUG: GET HTTP request to localhost/Ollama was made!")) as mock_get:
        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = '{"choices": [{"message": {"content": "{\\"n\\": \\"Test Candidate\\", \\"sk\\": [\\"Python\\"]}"}}]}'
            mock_post.return_value.json.return_value = {
                "choices": [{"message": {"content": '{"n": "Test Candidate", "sk": ["Python"]}'}}]
            }

            contacts = ContactInfo(email="test@example.com", phone="1234567890")
            extraction, metadata = await extract_resume_with_llm(
                resume_text="Test Candidate\nPython developer with 5 years experience.",
                contacts=contacts,
                section_hints=["Experience", "Skills"]
            )

            print(f"Extraction Completed: Name='{extraction.full_name if extraction else None}'")
            print(f"Metadata Error: {metadata.get('error')}")

            # Verify POST request went to Groq API endpoint
            assert mock_post.called, "Groq POST was not called"
            call_url = mock_post.call_args[0][0] if mock_post.call_args else ""
            print(f"HTTP POST Destination URL: {call_url}")
            assert "api.groq.com" in call_url, f"Expected Groq URL, got: {call_url}"
            assert "127.0.0.1" not in call_url and "localhost" not in call_url

            # Assert GET (Ollama health check) was NEVER called
            assert not mock_get.called, "GET request to Ollama tags was called!"

    print("\n" + "=" * 75)
    print("PRODUCTION GROQ ROUTING & ZERO LOCALHOST TEST: 100% PASSED!")
    print("=" * 75)


if __name__ == "__main__":
    import httpx
    asyncio.run(test_groq_routing())
