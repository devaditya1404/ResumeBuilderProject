#!/usr/bin/env python3
"""
test_ollama_cloud_conn.py — Tiny connectivity and latency test for Ollama API (Local / Cloud).
"""
import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.ai.ollama_client import chat_completion, check_ollama_health


async def run_conn_test():
    print("=" * 75)
    print("OLLAMA PROVIDER CONNECTIVITY TEST")
    print("=" * 75)
    print(f"OLLAMA_MODE: {settings.OLLAMA_MODE}")
    print(f"OLLAMA_BASE_URL: {settings.OLLAMA_BASE_URL}")
    print(f"OLLAMA_MODEL: {settings.OLLAMA_MODEL}")
    print(f"API KEY PRESENT: {'YES' if settings.OLLAMA_API_KEY else 'NO'}")

    # Health check
    health = await check_ollama_health()
    print(f"HEALTH CHECK STATUS: {'PASS' if health else 'FAIL'}")

    # Tiny JSON chat completion
    start = time.time()
    res = await chat_completion(
        prompt="Return valid JSON with key status='ok'.",
        system_prompt="Return valid JSON only.",
        json_mode=True
    )
    latency = time.time() - start

    print(f"\nLATENCY: {latency:.2f}s")
    print(f"MODEL USED: {res.get('model')}")
    print(f"RAW CONTENT: {res.get('content')}")
    print(f"ERROR STATUS: {res.get('error')}")

    if res.get("error") is None and "ok" in (res.get("content") or "").lower():
        print("\nOLLAMA CLOUD CONNECTION: PASS")
    else:
        print(f"\nOLLAMA CLOUD CONNECTION: FAIL ({res.get('error')})")


if __name__ == "__main__":
    asyncio.run(run_conn_test())
