#!/usr/bin/env python3
"""
discover_free_models.py — Discover and verify free-accessible Ollama Cloud models.
"""
import asyncio
import os
import sys
import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.ai.ollama_client import get_ollama_headers, get_base_url


async def discover_free_models():
    print("=" * 75)
    print("OLLAMA CLOUD FREE MODEL DISCOVERY")
    print("=" * 75)

    headers = get_ollama_headers()
    base_url = get_base_url()
    print(f"Base URL: {base_url}")
    print(f"API Key Present: {'YES' if settings.OLLAMA_API_KEY else 'NO'}")

    # Step 1: Query /api/tags
    candidate_models = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{base_url}/api/tags", headers=headers)
            print(f"/api/tags Status: {res.status_code}")
            if res.status_code == 200:
                models = [m["name"] for m in res.json().get("models", [])]
                print(f"/api/tags returned {len(models)} models: {models[:10]}")
                candidate_models.extend(models)
    except Exception as e:
        print(f"Error querying /api/tags: {e}")

    # Additional standard Ollama model names to test
    known_defaults = [
        "qwen2.5:3b", "qwen2.5:7b", "qwen2.5", "qwen2.5:1.5b", "qwen2.5:0.5b",
        "llama3.2", "llama3.2:1b", "llama3.2:3b", "llama3.1:8b", "llama3.1",
        "mistral:7b", "mistral", "gemma2:2b", "gemma2:9b", "phi3:mini", "qwen2.5-coder"
    ]
    for m in known_defaults:
        if m not in candidate_models:
            candidate_models.append(m)

    print(f"\nTotal candidate models to test generation for: {len(candidate_models)}")

    verified_free_models = []
    
    # Step 2: Perform real generation test for each model
    async with httpx.AsyncClient(timeout=15.0) as client:
        for model in candidate_models:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Reply only with OK"}],
                "stream": False
            }
            try:
                response = await client.post(f"{base_url}/api/chat", json=payload, headers=headers)
                status = response.status_code
                body_snippet = response.text[:120].replace("\n", " ")
                
                if status == 200:
                    text_content = response.json().get("message", {}).get("content", "")
                    if text_content and "OK" in text_content.upper():
                        print(f"✅ MODEL [{model}]: HTTP 200 SUCCESS -> '{text_content.strip()}'")
                        verified_free_models.append(model)
                    else:
                        print(f"⚠️ MODEL [{model}]: HTTP 200 empty/unexpected text -> '{text_content}'")
                elif status in (401, 403):
                    print(f"❌ MODEL [{model}]: HTTP {status} (Subscription/Auth required) -> {body_snippet}")
                elif status == 404:
                    print(f"❌ MODEL [{model}]: HTTP 404 (Model not found) -> {body_snippet}")
                else:
                    print(f"❌ MODEL [{model}]: HTTP {status} -> {body_snippet}")
            except Exception as ex:
                print(f"❌ MODEL [{model}]: EXCEPTION -> {ex}")

    print("\n" + "=" * 75)
    print(f"VERIFIED FREE ACCESSIBLE MODELS COUNT: {len(verified_free_models)}")
    print(f"VERIFIED FREE MODELS: {verified_free_models}")
    print("=" * 75)
    return verified_free_models


if __name__ == "__main__":
    asyncio.run(discover_free_models())
