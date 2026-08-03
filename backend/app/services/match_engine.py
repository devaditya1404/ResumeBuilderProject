"""
Deterministic Match Engine Service.

Calculates match scores, matching skills, missing mandatory skills, missing preferred skills,
domain alignment, evidence map, and component breakdowns using structured candidate profile data from database.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from app.services.skill_alias import (
    skills_match,
    normalize_skill_name,
    extract_atomic_skills,
    DISTINCT_PAIRS
)
from app.services.industry_mapper import infer_industries_from_candidate


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
    inferred_domains: List[str] = Field(default_factory=list)
    evidence_map: Dict[str, Any] = Field(default_factory=dict)
    score_breakdown: Dict[str, Any] = Field(default_factory=dict)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)


def build_skill_regex(target_skill: str) -> Optional[re.Pattern]:
    """Build safe, regex-bounded search pattern for a skill."""
    norm = normalize_skill_name(target_skill)
    lower = norm.lower()

    if lower == "java":
        return re.compile(r'\bjava\b', re.IGNORECASE)
    elif lower == "spring boot":
        return re.compile(r'\bspring\s*boot\b', re.IGNORECASE)
    elif lower == "sql":
        return re.compile(r'\b(sql|pl/sql|plsql|t-sql|mysql|postgresql)\b', re.IGNORECASE)
    elif lower == "sdlc":
        return re.compile(r'\b(sdlc|software\s+development\s+life\s+cycle)\b', re.IGNORECASE)
    elif lower == "git":
        return re.compile(r'\b(git|github|gitlab)\b', re.IGNORECASE)
    elif lower == "jira":
        return re.compile(r'\b(jira|atlassian\s+jira)\b', re.IGNORECASE)
    elif lower == "rest api":
        return re.compile(r'\b(rest(ful)?\s*(api|apis|webservices)?|rest)\b', re.IGNORECASE)
    elif lower == "kubernetes":
        return re.compile(r'\b(k8s|kubernetes)\b', re.IGNORECASE)
    elif lower == "aws":
        return re.compile(r'\b(aws|amazon\s+web\s+services)\b', re.IGNORECASE)
    elif lower == "react":
        return re.compile(r'\b(react|reactjs|react\.js)\b', re.IGNORECASE)
    elif lower == "excel":
        return re.compile(r'\b(excel|vlookup|xlookup|pivot\s+tables?)\b', re.IGNORECASE)
    elif lower == "power bi":
        return re.compile(r'\b(power\s*bi|powerbi)\b', re.IGNORECASE)
    elif lower.startswith("sap"):
        escaped = re.escape(lower)
        return re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)

    escaped = re.escape(target_skill.strip())
    if escaped:
        return re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)
    return None


def search_text_snippet_for_skill(text: str, target_skill: str) -> Optional[str]:
    """Check text snippet for skill match safely enforcing DISTINCT_PAIRS."""
    if not text or not isinstance(text, str):
        return None

    pattern = build_skill_regex(target_skill)
    if not pattern:
        return None

    match = pattern.search(text)
    if not match:
        return None

    matched_word = match.group(0).lower()
    target_lower = target_skill.lower()

    if (matched_word, target_lower) in DISTINCT_PAIRS or (target_lower, matched_word) in DISTINCT_PAIRS:
        return None

    start = max(0, match.start() - 30)
    end = min(len(text), match.end() + 50)
    snippet = text[start:end].replace('\n', ' ').strip()
    return snippet


def find_skill_evidence_in_candidate(req_skill: str, candidate_data: Dict[str, Any]) -> Tuple[str, Optional[str], str]:
    """
    Search for evidence of a skill across candidate structured DB profile:
    1. Skills list
    2. Experiences (company, designation, responsibilities)
    3. Projects (name, description, technologies)
    4. Certifications
    5. Summary

    Returns (status: "MATCH"|"PARTIAL_MATCH"|"NOT_FOUND", evidence_text: Optional[str], canonical_name: str)
    """
    atomic_targets = extract_atomic_skills(req_skill)
    if not atomic_targets:
        atomic_targets = [req_skill]

    cand_skills = candidate_data.get("skills") or []
    experiences = candidate_data.get("experiences") or []
    projects = candidate_data.get("projects") or []
    certifications = candidate_data.get("certifications") or []
    summary = candidate_data.get("summary") or candidate_data.get("professional_summary") or ""

    for target in atomic_targets:
        canon_name = normalize_skill_name(target)

        # 1. Dedicated Skills section
        for cs in cand_skills:
            if skills_match(cs, target):
                return "MATCH", f"Skills Section: '{cs}'", canon_name

        # 2. Employment History
        for exp in experiences:
            comp = exp.get("company") or "Company"
            desig = exp.get("designation") or "Role"

            if skills_match(desig, target) or search_text_snippet_for_skill(desig, target):
                return "MATCH", f"{comp} | Title: {desig}", canon_name

            resps = exp.get("responsibilities") or []
            if isinstance(resps, str):
                resps = [resps]
            for r in resps:
                snippet = search_text_snippet_for_skill(r, target)
                if snippet:
                    return "MATCH", f"{comp} ({desig}): \"...{snippet}...\"", canon_name

        # 3. Projects
        for proj in projects:
            p_name = proj.get("name") or "Project"
            techs = proj.get("technologies") or []
            techs_str = ", ".join(str(t) for t in techs) if isinstance(techs, list) else str(techs)

            if search_text_snippet_for_skill(techs_str, target):
                return "MATCH", f"Project '{p_name}' Tech: '{techs_str}'", canon_name

            p_desc = proj.get("description") or ""
            snippet = search_text_snippet_for_skill(p_desc, target)
            if snippet:
                return "MATCH", f"Project '{p_name}': \"...{snippet}...\"", canon_name

        # 4. Certifications
        for cert in certifications:
            cert_name = cert.get("name") or ""
            if search_text_snippet_for_skill(cert_name, target):
                return "MATCH", f"Certification: '{cert_name}'", canon_name

        # 5. Professional Summary
        if summary:
            snippet = search_text_snippet_for_skill(summary, target)
            if snippet:
                return "MATCH", f"Professional Summary: \"...{snippet}...\"", canon_name

    # Check for partial domain / module match (e.g. SAP ERP vs candidate SAP SD/MM)
    first_canon = normalize_skill_name(req_skill)
    if "sap" in first_canon.lower():
        for cs in cand_skills:
            if "sap" in cs.lower():
                return "PARTIAL_MATCH", f"Partial match: Candidate has '{cs}' for required '{first_canon}'", first_canon

    return "NOT_FOUND", None, first_canon


def evaluate_match(
    jd_requirement: Dict[str, Any],
    candidate_data: Dict[str, Any],
) -> DeterministicMatchOutput:
    """
    Perform deterministic JD ↔ Candidate match evaluation using structured candidate data from DB.
    Enforces soft weighted scoring (skills, experience, domain, role, education, location).
    """
    mandatory_skills = jd_requirement.get("mandatory_skills") or []
    preferred_skills = jd_requirement.get("preferred_skills") or []

    matching_skills: List[str] = []
    missing_mandatory: List[str] = []
    missing_preferred: List[str] = []
    evidence_map: Dict[str, Any] = {}
    strengths: List[str] = []
    gaps: List[str] = []

    # Infer domain / industry from employers and projects
    inferred_domains = infer_industries_from_candidate(candidate_data)

    # ── 1. SKILL MATCHING ──
    skill_score: Optional[float] = None
    if mandatory_skills or preferred_skills:
        mandatory_weighted_points = 0.0
        for req_skill in mandatory_skills:
            status, evidence, canon_name = find_skill_evidence_in_candidate(req_skill, candidate_data)
            if status == "MATCH":
                mandatory_weighted_points += 1.0
                if canon_name not in matching_skills:
                    matching_skills.append(canon_name)
                evidence_map[req_skill] = {
                    "status": "MATCH",
                    "canonical_name": canon_name,
                    "evidence": evidence,
                    "importance": "MANDATORY"
                }
            elif status == "PARTIAL_MATCH":
                mandatory_weighted_points += 0.6
                if canon_name not in matching_skills:
                    matching_skills.append(canon_name)
                evidence_map[req_skill] = {
                    "status": "PARTIAL_MATCH",
                    "canonical_name": canon_name,
                    "evidence": evidence,
                    "importance": "MANDATORY"
                }
            else:
                if canon_name not in missing_mandatory:
                    missing_mandatory.append(canon_name)
                evidence_map[req_skill] = {
                    "status": "NOT_FOUND",
                    "canonical_name": canon_name,
                    "evidence": "No evidence found across structured skills, experiences, or projects.",
                    "importance": "MANDATORY"
                }

        pref_weighted_points = 0.0
        for req_skill in preferred_skills:
            status, evidence, canon_name = find_skill_evidence_in_candidate(req_skill, candidate_data)
            if status in ["MATCH", "PARTIAL_MATCH"]:
                pref_weighted_points += 1.0 if status == "MATCH" else 0.6
                if canon_name not in matching_skills:
                    matching_skills.append(canon_name)
                evidence_map[req_skill] = {
                    "status": status,
                    "canonical_name": canon_name,
                    "evidence": evidence,
                    "importance": "PREFERRED"
                }
            else:
                if canon_name not in missing_preferred:
                    missing_preferred.append(canon_name)
                evidence_map[req_skill] = {
                    "status": "NOT_FOUND",
                    "canonical_name": canon_name,
                    "evidence": "No evidence found across structured skills, experiences, or projects.",
                    "importance": "PREFERRED"
                }

        mandatory_cov = (mandatory_weighted_points / len(mandatory_skills)) if mandatory_skills else 1.0
        if preferred_skills:
            pref_cov = pref_weighted_points / len(preferred_skills)
            raw_skill_score = ((mandatory_cov * 0.8) + (pref_cov * 0.2)) * 100.0
        else:
            raw_skill_score = mandatory_cov * 100.0

        skill_score = round(raw_skill_score, 1)

        if matching_skills:
            strengths.append(f"Demonstrates key required skills: {', '.join(matching_skills[:6])}")

    # ── 2. EXPERIENCE MATCHING ──
    min_exp = jd_requirement.get("minimum_experience")
    cand_exp = candidate_data.get("experience_years")
    if cand_exp is None and candidate_data.get("experience_months") is not None:
        cand_exp = candidate_data["experience_months"] / 12.0

    experience_score: Optional[float] = None
    if min_exp is not None and min_exp > 0:
        if cand_exp is not None and cand_exp > 0:
            if cand_exp >= min_exp:
                experience_score = 100.0
                strengths.append(f"Meets required experience: {cand_exp:.1f} years (Requires {min_exp} years)")
            else:
                experience_score = round(max(0.0, (cand_exp / min_exp) * 100.0), 1)
                gaps.append(f"Requires {min_exp} years experience; candidate has {cand_exp:.1f} years (PARTIAL MATCH).")
        else:
            exps = candidate_data.get("experiences") or []
            if exps:
                experience_score = 80.0
                strengths.append(f"Demonstrates work experience across {len(exps)} employment roles.")
            else:
                experience_score = 50.0
                gaps.append(f"Requires {min_exp} years experience; candidate experience details incomplete.")

    # ── 3. DOMAIN / INDUSTRY MATCHING ──
    jd_domains = jd_requirement.get("domain_requirements") or []
    domain_score: Optional[float] = None
    if jd_domains:
        matched_domains = [d for d in jd_domains if any(d.lower() in ind.lower() or ind.lower() in d.lower() for ind in inferred_domains)]
        if matched_domains:
            domain_score = 100.0
            strengths.append(f"Industry domain match demonstrated: {', '.join(matched_domains)}")
        elif inferred_domains:
            domain_score = 70.0
            strengths.append(f"Inferred industry background: {', '.join(inferred_domains[:2])}")
        else:
            domain_score = 50.0
    elif inferred_domains:
        domain_score = 100.0
        strengths.append(f"Inferred industry domain: {', '.join(inferred_domains[:2])}")

    # ── 4. ROLE MATCHING ──
    jd_title = (jd_requirement.get("job_title") or "").lower()
    cand_title = (candidate_data.get("current_designation") or candidate_data.get("latest_designation") or "").lower()

    role_score: Optional[float] = None
    if jd_title and cand_title:
        jd_tokens = set(re.findall(r'\b\w+\b', jd_title))
        cand_tokens = set(re.findall(r'\b\w+\b', cand_title))
        overlap = len(jd_tokens.intersection(cand_tokens))
        if overlap > 0:
            role_score = round(min(100.0, (overlap / len(jd_tokens)) * 100.0), 1)
            strengths.append(f"Background as '{candidate_data.get('current_designation') or candidate_data.get('latest_designation')}' aligns with role.")
        else:
            role_score = 60.0
    elif candidate_data.get("experiences"):
        role_score = 75.0

    # ── 5. EDUCATION MATCHING ──
    jd_edu = jd_requirement.get("education_requirement")
    education_score: Optional[float] = None
    if jd_edu and str(jd_edu).strip():
        cand_edu = candidate_data.get("education") or []
        if cand_edu:
            education_score = 100.0
        else:
            education_score = 60.0
    else:
        education_score = 100.0

    # ── 6. LOCATION MATCHING ──
    jd_loc = jd_requirement.get("location")
    cand_loc = candidate_data.get("location")
    location_score: Optional[float] = None
    if jd_loc and str(jd_loc).strip() and cand_loc and str(cand_loc).strip():
        if jd_loc.lower() in cand_loc.lower() or cand_loc.lower() in jd_loc.lower() or "remote" in jd_loc.lower():
            location_score = 100.0
        else:
            location_score = 70.0
    else:
        location_score = 100.0

    # ── 7. WEIGHTED SCORING MODEL ──
    base_weights = {
        "skill": (45.0, skill_score),
        "experience": (20.0, experience_score),
        "domain": (15.0, domain_score),
        "role": (10.0, role_score),
        "education": (5.0, education_score),
        "location": (5.0, location_score),
    }

    active_weight_sum = 0.0
    weighted_score_sum = 0.0
    score_breakdown = {}

    for cat, (weight, val) in base_weights.items():
        if val is not None:
            active_weight_sum += weight
            weighted_score_sum += (weight * val)
            score_breakdown[cat] = {
                "score": val,
                "weight": weight
            }

    if active_weight_sum > 0:
        overall_score = round(weighted_score_sum / active_weight_sum, 1)
    elif skill_score is not None:
        overall_score = skill_score
    else:
        overall_score = 50.0

    return DeterministicMatchOutput(
        overall_score=overall_score,
        skill_score=skill_score,
        experience_score=experience_score,
        role_score=role_score,
        education_score=education_score,
        location_score=location_score,
        domain_score=domain_score,
        matching_skills=matching_skills,
        missing_mandatory_skills=missing_mandatory,
        missing_preferred_skills=missing_preferred,
        inferred_domains=inferred_domains,
        evidence_map=evidence_map,
        score_breakdown=score_breakdown,
        strengths=strengths,
        gaps=gaps,
    )
