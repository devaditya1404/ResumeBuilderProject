"""
Deterministic Match Engine Service.

Calculates match scores, matching skills, missing mandatory skills, missing preferred skills,
and component breakdowns deterministically using candidate structured data from SQLite.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from app.services.skill_alias import skills_match, normalize_skill_name


class DeterministicMatchOutput(BaseModel):
    overall_score: float
    skill_score: Optional[float] = None
    experience_score: Optional[float] = None
    role_score: Optional[float] = None
    education_score: Optional[float] = None
    location_score: Optional[float] = None
    domain_score: Optional[float] = None

    matching_skills: List[str] = Field(default_factory=list)
    missing_mandatory_skills: List[str] = Field(default_factory=list)
    missing_preferred_skills: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)


def evaluate_match(
    jd_requirement: Dict[str, Any],
    candidate_data: Dict[str, Any],
) -> DeterministicMatchOutput:
    """
    Perform deterministic JD ↔ Candidate match evaluation.

    Strict Rules:
    - NO default fake fallback scores (e.g. 70%, 50%).
    - Unspecified/unavailable categories return None and are excluded from dynamic weight sum.
    - Missing skills MUST be traceable directly to the JD.
    - Matching skills MUST exist in JD AND candidate skills.
    """
    cand_skills = candidate_data.get("skills") or []
    mandatory_skills = jd_requirement.get("mandatory_skills") or []
    preferred_skills = jd_requirement.get("preferred_skills") or []

    matching_skills: List[str] = []
    missing_mandatory: List[str] = []
    missing_preferred: List[str] = []
    strengths: List[str] = []
    gaps: List[str] = []

    # ── 1. SKILL MATCHING ──
    skill_score: Optional[float] = None
    if mandatory_skills or preferred_skills:
        matched_mandatory_count = 0
        for req_skill in mandatory_skills:
            has_skill = any(skills_match(cand_s, req_skill) for cand_s in cand_skills)
            if has_skill:
                matched_mandatory_count += 1
                norm_name = normalize_skill_name(req_skill)
                if norm_name not in matching_skills:
                    matching_skills.append(norm_name)
            else:
                norm_name = normalize_skill_name(req_skill)
                if norm_name not in missing_mandatory:
                    missing_mandatory.append(norm_name)

        matched_pref_count = 0
        for req_skill in preferred_skills:
            has_skill = any(skills_match(cand_s, req_skill) for cand_s in cand_skills)
            if has_skill:
                matched_pref_count += 1
                norm_name = normalize_skill_name(req_skill)
                if norm_name not in matching_skills:
                    matching_skills.append(norm_name)
            else:
                norm_name = normalize_skill_name(req_skill)
                if norm_name not in missing_preferred:
                    missing_preferred.append(norm_name)

        # Calculate skill score
        mandatory_cov = (matched_mandatory_count / len(mandatory_skills)) if mandatory_skills else 1.0
        if preferred_skills:
            pref_cov = matched_pref_count / len(preferred_skills)
            raw_skill_score = ((mandatory_cov * 0.8) + (pref_cov * 0.2)) * 100.0
        else:
            raw_skill_score = mandatory_cov * 100.0
        
        skill_score = round(raw_skill_score, 1)

        if matching_skills:
            strengths.append(f"Matches required skills: {', '.join(matching_skills[:5])}")

    # ── 2. EXPERIENCE MATCHING ──
    min_exp = jd_requirement.get("minimum_experience")
    cand_exp = candidate_data.get("experience_years")
    if cand_exp is None and candidate_data.get("experience_months") is not None:
        cand_exp = candidate_data["experience_months"] / 12.0

    experience_score: Optional[float] = None
    if min_exp is not None and min_exp > 0:
        if cand_exp is not None:
            if cand_exp >= min_exp:
                experience_score = 100.0
                strengths.append(f"Meets required experience: {cand_exp:.1f} years (Requires {min_exp} years)")
            else:
                experience_score = round(max(0.0, (cand_exp / min_exp) * 100.0), 1)
                gaps.append(f"Requires {min_exp} years experience; candidate has {cand_exp:.1f} years.")
        else:
            experience_score = None
            gaps.append(f"Requires {min_exp} years experience; candidate experience unavailable.")

    # ── 3. ROLE MATCHING ──
    jd_title = (jd_requirement.get("job_title") or "").lower()
    cand_title = (candidate_data.get("current_designation") or candidate_data.get("latest_designation") or "").lower()

    role_score: Optional[float] = None
    if jd_title and cand_title:
        jd_tokens = set(re.findall(r'\b\w+\b', jd_title))
        cand_tokens = set(re.findall(r'\b\w+\b', cand_title))
        overlap = len(jd_tokens.intersection(cand_tokens))
        if overlap > 0:
            role_score = round(min(100.0, (overlap / len(jd_tokens)) * 100.0), 1)
            strengths.append(f"Background as {candidate_data.get('current_designation') or candidate_data.get('latest_designation')} aligns with role")
        else:
            role_score = 0.0

    # ── 4. EDUCATION MATCHING ──
    jd_edu = jd_requirement.get("education_requirement")
    education_score: Optional[float] = None
    if jd_edu and str(jd_edu).strip():
        cand_edu = candidate_data.get("education") or []
        if cand_edu:
            education_score = 100.0
            strengths.append("Education criteria satisfied.")
        else:
            education_score = 0.0

    # ── 5. LOCATION MATCHING ──
    jd_loc = jd_requirement.get("location")
    cand_loc = candidate_data.get("location")
    location_score: Optional[float] = None
    if jd_loc and str(jd_loc).strip() and cand_loc and str(cand_loc).strip():
        if jd_loc.lower() in cand_loc.lower() or cand_loc.lower() in jd_loc.lower() or "remote" in jd_loc.lower():
            location_score = 100.0
        else:
            location_score = 0.0

    # ── 6. DYNAMIC WEIGHT NORMALIZATION ──
    # Base weights: Skills (55%), Experience (20%), Role (10%), Education (5%), Location (5%)
    base_weights = {
        "skill": (55.0, skill_score),
        "experience": (20.0, experience_score),
        "role": (10.0, role_score),
        "education": (5.0, education_score),
        "location": (5.0, location_score),
    }

    active_weight_sum = 0.0
    weighted_score_sum = 0.0

    for cat, (weight, val) in base_weights.items():
        if val is not None:
            active_weight_sum += weight
            weighted_score_sum += (weight * val)

    if active_weight_sum > 0:
        overall_score = round(weighted_score_sum / active_weight_sum, 1)
    elif skill_score is not None:
        overall_score = skill_score
    else:
        overall_score = 0.0

    return DeterministicMatchOutput(
        overall_score=overall_score,
        skill_score=skill_score,
        experience_score=experience_score,
        role_score=role_score,
        education_score=education_score,
        location_score=location_score,
        matching_skills=matching_skills,
        missing_mandatory_skills=missing_mandatory,
        missing_preferred_skills=missing_preferred,
        strengths=strengths,
        gaps=gaps,
    )
