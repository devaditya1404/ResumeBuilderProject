"""
Structured resume extraction using a single Ollama LLM call.

Uses a compact internal transport format (CompactResumeExtraction) for fast,
token-efficient LLM responses, then maps back to canonical ResumeExtraction models.
"""
import json
import logging
import time
from typing import Optional, Dict, Any, Tuple
from app.ai.ollama_client import chat_completion
from app.ai.llm_provider import get_llm_provider
from app.core.config import settings
from app.ai.extraction_schemas import (
    CompactResumeExtraction,
    CompactExperience,
    CompactEducation,
    CompactProject,
    ResumeExtraction,
    compact_to_canonical,
)
from app.parsers.contact_parser import ContactInfo

logger = logging.getLogger(__name__)

import re

SYSTEM_PROMPT = """You are a precise compact JSON resume extractor.

RULES:
1. Extract ONLY facts explicitly stated in resume text. Do NOT infer or guess.
2. Employer (c) != Client (cl). "c" is employer paying salary.
3. COMPLETENESS: Extract EVERY single employment entry from top to bottom (including short-term, older, or contract roles). Do NOT omit any entry.
4. DATES: Copy start/end dates strictly from that specific entry (e.g. October 2022 -> "2022-10", July 2023 -> "2023-07", 2021 -> "2021"). Never invent a month if not explicitly stated in that entry.
5. SKILLS (sk): List individual atomic skills/tools ONLY (1-4 words each, e.g. "Java", "AWS", "Docker"). No category prefixes (e.g., "Web Technologies:"), no descriptions, no sentences.
6. Return valid JSON matching schema exactly. No prose."""


def count_probable_date_blocks(text: str) -> int:
    """Generic pre-LLM check: Count probable date ranges in experience text."""
    pattern = re.compile(
        r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\b20\d\d|\b19\d\d)\s*,?\s*(?:\b\d{4}\b)?\s*[-–—to\s]+\s*(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\b20\d\d|\b19\d\d|Present|Current)',
        re.IGNORECASE
    )
    return len(pattern.findall(text))


def build_extraction_prompt(
    resume_text: str,
    contacts: ContactInfo,
    section_hints: list,
) -> str:
    """
    Build a minimal token-efficient compact extraction prompt.
    """
    sections_block = ", ".join(section_hints) if section_hints else "None"
    date_blocks_count = count_probable_date_blocks(resume_text)
    hint_block = f"NOTICE: Text contains approximately {date_blocks_count} employment date intervals. Extract ALL employment entries from top to bottom." if date_blocks_count > 0 else ""

    prompt = f"""Extract semantic information from this resume into compact JSON.

SECTIONS: {sections_block}
{hint_block}

RESUME TEXT:
---
{resume_text[:7000]}
---

JSON SCHEMA:
{{
  "n": "Full Name or null",
  "loc": "City/State/Country or null",
  "exp": [
    {{
      "c": "Employer Company Name",
      "r": "Designation / Job Title",
      "s": "YYYY-MM or YYYY or null",
      "e": "YYYY-MM or YYYY or Present or null"
    }}
  ],
  "edu": [
    {{
      "i": "Institution Name",
      "d": "Degree",
      "f": "Field of Study"
    }}
  ],
  "cert": ["Certification Name"],
  "pr": [
    {{
      "n": "Project Name",
      "t": ["Technology Used"]
    }}
  ],
  "lang": ["Language"],
  "sk": ["AtomicSkill1", "AtomicSkill2"]
}}"""

    return prompt


async def extract_resume_with_llm(
    resume_text: str,
    contacts: ContactInfo,
    section_hints: list,
) -> Tuple[Optional[ResumeExtraction], Dict[str, Any]]:
    """
    Make a single compact structured extraction call to configured LLM provider.
    Returns canonical ResumeExtraction model and performance metadata.
    """
    metadata: Dict[str, Any] = {
        "model": None,
        "client_wall_time_ms": 0,
        "total_duration_ms": 0,
        "load_duration_ms": 0,
        "prompt_eval_count": 0,
        "prompt_eval_duration_ms": 0,
        "eval_count": 0,
        "eval_duration_ms": 0,
        "output_chars": 0,
        "error": None,
        "warnings": [],
        "raw_response": "",
        "compact_json": None,
    }

    # Resolve active provider & check provider health
    provider = get_llm_provider()
    logger.info(f"Resume AI provider active: {settings.LLM_PROVIDER}")

    is_healthy = await provider.check_health()
    if not is_healthy:
        err_msg = "LOCAL_OLLAMA_NOT_RUNNING" if settings.LLM_PROVIDER == "ollama" else "GROQ_API_KEY_NOT_CONFIGURED"
        metadata["error"] = err_msg
        logger.error(f"AI Provider '{settings.LLM_PROVIDER}' check failed: {err_msg}")
        return None, metadata

    # Build prompt
    prompt = build_extraction_prompt(resume_text, contacts, section_hints)

    # Make call
    start = time.time()
    result = await chat_completion(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        temperature=0.1,
        json_mode=True,
    )

    metadata["model"] = result.get("model")
    metadata["client_wall_time_ms"] = result.get("client_wall_time_ms", (time.time() - start) * 1000)
    metadata["total_duration_ms"] = result.get("total_duration_ms", 0)
    metadata["load_duration_ms"] = result.get("load_duration_ms", 0)
    metadata["prompt_eval_count"] = result.get("prompt_eval_count", 0)
    metadata["prompt_eval_duration_ms"] = result.get("prompt_eval_duration_ms", 0)
    metadata["eval_count"] = result.get("eval_count", 0)
    metadata["eval_duration_ms"] = result.get("eval_duration_ms", 0)
    
    raw_content = result.get("content", "")
    metadata["output_chars"] = len(raw_content)
    metadata["raw_response"] = raw_content[:2000]

    if result.get("error"):
        metadata["error"] = result["error"]
        logger.error(f"Ollama extraction failed: {result['error']}")
        return None, metadata

    content = raw_content.strip()
    if not content:
        metadata["error"] = "EMPTY_RESPONSE"
        return None, metadata

    try:
        if content.startswith("```"):
            lines = content.split("\n")
            json_lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(json_lines)

        parsed = json.loads(content)
        metadata["compact_json"] = parsed
    except json.JSONDecodeError as e:
        metadata["error"] = f"JSON_PARSE_ERROR: {str(e)}"
        logger.error(f"Failed to parse LLM JSON: {str(e)}")
        return None, metadata

    # Parse into compact transport schema
    try:
        compact = CompactResumeExtraction(**parsed)
    except Exception as e:
        logger.warning(f"Compact Pydantic validation warning: {str(e)}. Recovering fields...")
        metadata["warnings"].append("LLM_TYPE_NORMALIZED")
        compact = _fault_tolerant_compact_parse(parsed, metadata)

    # Convert compact transport -> canonical ResumeExtraction model
    canonical = compact_to_canonical(compact)
    return canonical, metadata


def _fault_tolerant_compact_parse(parsed: dict, metadata: dict) -> CompactResumeExtraction:
    """Safely parse compact JSON field-by-field."""
    kwargs = {}
    if "n" in parsed:
        kwargs["n"] = parsed["n"]
    if "loc" in parsed:
        kwargs["loc"] = parsed["loc"]
    for list_field in ["sk", "cert", "lang"]:
        if list_field in parsed:
            kwargs[list_field] = parsed[list_field]

    if "exp" in parsed and isinstance(parsed["exp"], list):
        valid_exp = []
        for item in parsed["exp"]:
            if isinstance(item, dict):
                try:
                    valid_exp.append(CompactExperience(**item))
                except Exception:
                    metadata["warnings"].append("LLM_EXP_ITEM_SKIPPED")
        kwargs["exp"] = valid_exp

    if "edu" in parsed and isinstance(parsed["edu"], list):
        valid_edu = []
        for item in parsed["edu"]:
            if isinstance(item, dict):
                try:
                    valid_edu.append(CompactEducation(**item))
                except Exception:
                    metadata["warnings"].append("LLM_EDU_ITEM_SKIPPED")
        kwargs["edu"] = valid_edu

    if "pr" in parsed and isinstance(parsed["pr"], list):
        valid_pr = []
        for item in parsed["pr"]:
            if isinstance(item, dict):
                try:
                    valid_pr.append(CompactProject(**item))
                except Exception:
                    metadata["warnings"].append("LLM_PROJ_ITEM_SKIPPED")
        kwargs["pr"] = valid_pr

    return CompactResumeExtraction(**kwargs)
