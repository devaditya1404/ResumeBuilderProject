"""
Match Explainer Service.

Generates human-readable Strengths and Resume Improvements strictly grounded in
deterministic match evaluation data using local Ollama qwen2.5:3b.

Anti-hallucination rules enforced:
- Strengths must be backed by candidate facts.
- Missing skills come strictly from the JD.
- Improvements must NEVER encourage fabricating missing experience.
"""
import json
import logging
from typing import Dict, Any, List, Tuple
from app.services.match_engine import DeterministicMatchOutput
from app.ai.ollama_client import chat_completion

logger = logging.getLogger(__name__)


async def generate_match_explanation(
    match_result: DeterministicMatchOutput,
    jd_title: str,
    candidate_name: str,
) -> Tuple[List[str], List[str], str]:
    """
    Generate grounded Strengths, Resume Improvements, and concise summary explanation.
    Returns (strengths, resume_improvements, explanation_summary).
    """
    matched_skills = ", ".join(match_result.matching_skills) or "None"
    missing_mandatory = ", ".join(match_result.missing_mandatory_skills) or "None"
    missing_preferred = ", ".join(match_result.missing_preferred_skills) or "None"

    prompt = f"""Generate match strengths and honest resume improvement tips for candidate '{candidate_name}' matching for '{jd_title}'.

DETERMINISTIC EVALUATION:
- Overall Score: {match_result.overall_score}%
- Matched JD Skills: {matched_skills}
- Missing Mandatory Skills: {missing_mandatory}
- Missing Preferred Skills: {missing_preferred}

RULES:
1. Strengths: 3-5 bullet points highlighting matched skills & background facts.
2. Improvements: 2-3 honest tips. NEVER tell candidate to falsely claim missing skills. Use phrasing like "If you have professional X experience, make it more visible in your resume."
3. Return valid JSON only.

JSON SCHEMA:
{{
  "strengths": [
    "Strong Python and SQL experience matching JD requirements"
  ],
  "improvements": [
    "If you have experience with Docker or Kubernetes, highlight relevant projects clearly in your resume."
  ],
  "summary": "Candidate scores {match_result.overall_score}% with strong alignment in core skills."
}}"""

    system_prompt = "You are a recruitment match analyst. Generate honest grounded insights. No prose outside JSON."

    try:
        res = await chat_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            json_mode=True,
        )
        content = (res.get("content") or "").strip()
        if content:
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join([l for l in lines if not l.strip().startswith("```")])
            parsed = json.loads(content)
            strengths = parsed.get("strengths") or match_result.strengths
            
            # Post-filter strengths to eliminate any contradiction with missing skills
            missing_set = set((match_result.missing_mandatory_skills or []) + (match_result.missing_preferred_skills or []))
            filtered_strengths = []
            for st in strengths:
                contains_missing = any(ms.lower() in st.lower() for ms in missing_set)
                if not contains_missing:
                    filtered_strengths.append(st)

            if not filtered_strengths:
                filtered_strengths = match_result.strengths or [f"Matching skills: {matched_skills}"]

            improvements = parsed.get("improvements") or [
                f"If you have experience with {s}, highlight it more prominently."
                for s in match_result.missing_mandatory_skills[:3]
            ]
            summary = parsed.get("summary") or f"Overall match score is {match_result.overall_score}%."
            return filtered_strengths, improvements, summary
    except Exception as e:
        logger.warning(f"Ollama match explanation failed fallback to deterministic: {str(e)}")

    # Fallback to pure deterministic strengths & improvements
    fallback_strengths = match_result.strengths or [f"Matching skills: {matched_skills}"]
    fallback_improvements = [
        f"If you have professional {s} experience, make it more visible on your resume."
        for s in match_result.missing_mandatory_skills[:3]
    ] or ["Quantify key achievements and impact in your work experience section."]

    summary = f"Candidate achieves {match_result.overall_score}% match score against {jd_title}."
    return fallback_strengths, fallback_improvements, summary
