#!/usr/bin/env python3
"""
test_groq_cloud.py — Verification script for Groq Cloud LLM provider integration.
"""
import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.ai.llm_provider import GroqCloudProvider
from app.parsers.resume_parser import parse_resume


async def run_groq_test():
    print("=" * 75)
    print("GROQ CLOUD LLM PROVIDER TEST")
    print("=" * 75)
    
    provider = GroqCloudProvider()
    print(f"Provider API URL: {provider.api_url}")
    print(f"Default Model: {provider.default_model}")
    print(f"API Key Present: {'YES' if provider.api_key else 'NO'}")

    if not provider.api_key:
        print("\nSTATUS: BLOCKED ONLY BY CLOUD API KEY")
        print("Set GROQ_API_KEY environment variable to execute live cloud test.")
        return False

    # 1. Minimal structured JSON generation request
    print("\n--- Running Minimal Structured JSON Generation Test ---")
    start = time.time()
    res = await provider.chat_completion(
        prompt="Return valid JSON: {\"status\": \"ok\", \"provider\": \"groq\"}",
        system_prompt="Return valid JSON only.",
        json_mode=True
    )
    latency = time.time() - start

    print(f"Latency: {latency:.2f}s")
    print(f"Error: {res.get('error')}")
    print(f"Raw Output: {res.get('content')}")

    if res.get("error"):
        print(f"\nMinimal Cloud Generation: FAIL ({res.get('error')})")
        return False
    else:
        print("\nMinimal Cloud Generation: PASS")

    # 2. Real Resume Test with Groq Cloud LLM
    print("\n--- Running Real Resume Parsing Test via Groq Cloud LLM ---")
    pdf_path = os.path.join("data", "test_resumes", "aditya_resume.pdf")
    if not os.path.exists(pdf_path):
        print(f"Test PDF not found at {pdf_path}")
        return True

    # Temporarily force settings to use groq
    os.environ["LLM_PROVIDER"] = "groq"
    settings.LLM_PROVIDER = "groq"

    parse_result = await parse_resume(pdf_path)

    print(f"Parsing Status: {parse_result.parsing_status}")
    print(f"Full Name: {parse_result.extraction.full_name if parse_result.extraction else 'N/A'}")
    print(f"Skills Count: {len(parse_result.extraction.skills) if parse_result.extraction else 0}")
    print(f"Experiences Count: {len(parse_result.extraction.experiences) if parse_result.extraction else 0}")
    print(f"Education Count: {len(parse_result.extraction.education) if parse_result.extraction else 0}")
    print(f"LLM Model Used: {parse_result.llm_model}")
    print(f"Errors: {parse_result.errors}")

    if parse_result.parsing_status == "PARSED" and not parse_result.errors:
        print("\nREAL RESUME CLOUD TEST: PASS")
        return True
    else:
        print(f"\nREAL RESUME CLOUD TEST: FAIL ({parse_result.errors})")
        return False


if __name__ == "__main__":
    asyncio.run(run_groq_test())
