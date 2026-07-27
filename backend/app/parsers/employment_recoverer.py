"""
Generic hybrid employment recoverer module.

Detects date-range blocks in the resume experience text, checks if any date block
was missed by the primary LLM pass, and executes a targeted micro-LLM call
(num_predict=128) to recover the missing employment entry.
"""
import re
import logging
from typing import List, Dict, Any, Optional
from app.ai.ollama_client import chat_completion
from app.ai.extraction_schemas import ExtractedExperience, _coerce_str

logger = logging.getLogger(__name__)

# Date range pattern matching employment dates in source text
DATE_BLOCK_PATTERN = re.compile(
    r'((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\b20\d\d|\b19\d\d)\s*,?\s*(?:\b\d{4}\b)?\s*[-–—to\s]+\s*(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\b20\d\d|\b19\d\d|Present|Current))',
    re.IGNORECASE
)


def find_unmatched_date_snippets(
    resume_text: str,
    extracted_experiences: List[ExtractedExperience],
) -> List[str]:
    """
    Find snippets in resume_text surrounding date ranges that were NOT covered
    by any extracted experience in extracted_experiences.
    """
    unmatched_snippets: List[str] = []

    # Build set of exact start/end date pairs extracted by LLM
    extracted_start_dates = set()
    for e in extracted_experiences:
        if e.start_date:
            extracted_start_dates.add(e.start_date.lower())

    # Search for all date matches in full text
    for match in DATE_BLOCK_PATTERN.finditer(resume_text):
        start_char, end_char = match.span()
        date_str = match.group(1).strip()
        
        years = re.findall(r'\b20\d\d|\b19\d\d', date_str)
        months = re.findall(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*', date_str, re.IGNORECASE)
        
        is_matched = False
        if years and months:
            for y in years:
                for m in months:
                    m_norm = m[:3].lower()
                    for ext_s in extracted_start_dates:
                        if y in ext_s and m_norm in ext_s.lower():
                            is_matched = True
                            break

        if not is_matched:
            ctx_start = max(0, start_char - 150)
            ctx_end = min(len(resume_text), end_char + 150)
            snippet = resume_text[ctx_start:ctx_end].strip()
            if snippet not in unmatched_snippets:
                unmatched_snippets.append(snippet)

    return unmatched_snippets


async def recover_missing_employment(
    resume_text: str,
    extracted_experiences: List[ExtractedExperience],
) -> List[ExtractedExperience]:
    """
    Identify missing employment entries and execute targeted micro-LLM calls to recover them.
    Returns the complete merged list of ExtractedExperience items.
    """
    snippets = find_unmatched_date_snippets(resume_text, extracted_experiences)
    if not snippets:
        return extracted_experiences

    logger.info(f"Hybrid Recovery: Found {len(snippets)} un-matched date snippets. Recovering...")
    recovered: List[ExtractedExperience] = list(extracted_experiences)

    for snippet in snippets:
        prompt = f"""Extract company name, designation, start_date, end_date from this snippet into compact JSON:

SNIPPET:
{snippet}

JSON:
{{"c":"Company","r":"Title","s":"YYYY-MM or YYYY","e":"YYYY-MM or YYYY or Present"}}"""

        result = await chat_completion(
            prompt=prompt,
            system_prompt="You are a compact resume JSON extractor. Extract facts strictly from snippet.",
            temperature=0.1,
            json_mode=True,
        )

        content = (result.get("content") or "").strip()
        if content:
            try:
                import json
                if content.startswith("```"):
                    lines = content.split("\n")
                    content = "\n".join([l for l in lines if not l.strip().startswith("```")])
                parsed = json.loads(content)
                comp = _coerce_str(parsed.get("c"))
                role = _coerce_str(parsed.get("r"))
                s_date = _coerce_str(parsed.get("s"))
                e_date = _coerce_str(parsed.get("e"))

                if comp or role:
                    new_exp = ExtractedExperience(
                        company=comp,
                        title=role,
                        start_date=s_date,
                        end_date=e_date,
                    )
                    # Deduplicate against existing company names
                    comp_clean = (comp or "").lower().strip()
                    already_exists = any(
                        e.company and comp_clean in e.company.lower().strip()
                        for e in recovered
                    )
                    if not already_exists:
                        recovered.append(new_exp)
            except Exception as ex:
                logger.warning(f"Failed to parse micro-recovery JSON: {str(ex)}")

    return recovered
