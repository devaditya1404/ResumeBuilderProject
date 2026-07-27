#!/usr/bin/env python3
"""
check_cloud_models.py — Test available Ollama Cloud models and test generation.
"""
import asyncio
import os
import sys
import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.ai.ollama_client import get_ollama_headers, get_base_url


async def query_cloud_models():
    print("=" * 75)
    print("OLLAMA CLOUD MODEL AVAILABILITY TEST")
    print("=" * 75)
    
    url = f"{get_base_url()}/api/tags"
    headers = get_ollama_headers()
    
    print(f"Base URL: {url}")
    print(f"Has API Key: {'YES' if settings.OLLAMA_API_KEY else 'NO'}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url, headers=headers)
            print(f"/api/tags Status: {res.status_code}")
            if res.status_code == 200:
                models = [m["name"] for m in res.json().get("models", [])]
                print(f"Available Models from API: {models}")
            else:
                print(f"Tags Response: {res.text[:200]}")
    except Exception as e:
        print(f"Failed to query /api/tags: {e}")

    # Test candidate models with minimal generation payload
    candidates_to_test = [
        "qwen2.5",
        "qwen2.5:7b",
        "qwen2.5:3b",
        "qwen2.5:1.5b",
        "qwen2.5-coder",
        "llama3.2",
        "llama3.1",
        "mistral"
    ]

    print("\n--- Testing Model Candidates via POST /api/chat ---")
    for m in candidates_to_test:
        payload = {
            "model": m,
            "messages": [{"role": "user", "content": "Return valid JSON: {\"status\":\"ok\"}"}],
            "stream": False,
            "format": "json"
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(f"{get_base_url()}/api/chat", json=payload, headers=headers)
                print(f"Model [{m}]: HTTP {resp.status_code} -> {resp.text[:120]}")
        except Exception as ex:
            print(f"Model [{m}]: EXCEPTION -> {ex}")


if __name__ == "__main__":
    asyncio.run(query_cloud_models())
