"""
JD Requirement Parser Service.

Extracts structured job requirements (mandatory skills, preferred skills, min/max experience,
education, location, domain) from raw Job Description text.
"""
import re
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.services.skill_alias import normalize_skill_name
from app.ai.ollama_client import chat_completion

logger = logging.getLogger(__name__)


class ParsedRequirementSchema(BaseModel):
    job_title: Optional[str] = None
    mandatory_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    minimum_experience: Optional[float] = None
    maximum_experience: Optional[float] = None
    education_requirement: Optional[str] = None
    location: Optional[str] = None
    domain_requirements: List[str] = Field(default_factory=list)
    role_requirements: List[str] = Field(default_factory=list)


def parse_jd_deterministically(jd_text: str, title: str = "") -> ParsedRequirementSchema:
    """
    Fast deterministic regex extraction of JD requirements.
    """
    req = ParsedRequirementSchema()
    req.job_title = title.strip() or "Software Engineer"

    # Extract min experience
    exp_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:\+|-|\s*to\s*\d+)?\s*(?:years?|yrs?)\b', jd_text, re.IGNORECASE)
    if exp_match:
        try:
            req.minimum_experience = float(exp_match.group(1))
        except ValueError:
            pass

    # Extract Mandatory / Required skills section
    req_sec = re.search(r'(?:Required|Mandatory|Must Have|Essential)\s*[:\n]([\s\S]*?)(?:Preferred|Nice to Have|Education|Location|Responsibilities|$)', jd_text, re.IGNORECASE)
    if req_sec:
        skills = [normalize_skill_name(s) for s in re.findall(r'[\w\s\.\+#-]+', req_sec.group(1)) if len(s.strip()) > 1]
        req.mandatory_skills = [s for s in skills if s]

    # Extract Preferred skills section
    pref_sec = re.search(r'(?:Preferred|Nice to Have|Desired)\s*[:\n]([\s\S]*?)(?:Education|Location|Responsibilities|$)', jd_text, re.IGNORECASE)
    if pref_sec:
        skills = [normalize_skill_name(s) for s in re.findall(r'[\w\s\.\+#-]+', pref_sec.group(1)) if len(s.strip()) > 1]
        req.preferred_skills = [s for s in skills if s]

    return req


async def parse_jd(jd_text: str, job_title: str = "") -> ParsedRequirementSchema:
    """
    Parses JD text using deterministic regex + Ollama fallback for semantic precision.
    """
    if not jd_text or not jd_text.strip():
        return ParsedRequirementSchema(job_title=job_title or "Job Requirement")

    prompt = f"""Extract structured requirements from this Job Description into JSON.

JOB DESCRIPTION:
---
{jd_text[:4000]}
---

JSON SCHEMA:
{{
  "job_title": "{job_title or 'Job Title'}",
  "mandatory_skills": ["Skill1", "Skill2"],
  "preferred_skills": ["Skill3"],
  "minimum_experience": 4,
  "maximum_experience": null,
  "education_requirement": "Bachelor's or null",
  "location": "City/Remote or null",
  "domain_requirements": ["Domain1"],
  "role_requirements": ["Requirement1"]
}}"""

    system_prompt = "You are a compact JSON JD parser. Extract explicit requirement facts only. No markdown prose."

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

            mandatory = [normalize_skill_name(s) for s in parsed.get("mandatory_skills", []) if s]
            preferred = [normalize_skill_name(s) for s in parsed.get("preferred_skills", []) if s]

            return ParsedRequirementSchema(
                job_title=parsed.get("job_title") or job_title or "Job Requirement",
                mandatory_skills=mandatory,
                preferred_skills=preferred,
                minimum_experience=parsed.get("minimum_experience"),
                maximum_experience=parsed.get("maximum_experience"),
                education_requirement=parsed.get("education_requirement"),
                location=parsed.get("location"),
                domain_requirements=parsed.get("domain_requirements", []),
                role_requirements=parsed.get("role_requirements", []),
            )
    except Exception as e:
        logger.warning(f"Ollama JD parsing failed fallback to regex: {str(e)}")

    return parse_jd_deterministically(jd_text, job_title)
