from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import Requirement, RequirementSkill, Candidate, CandidateSkill, MatchResult
from app.schemas.requirement import (
    RequirementCreate, RequirementUpdate, RequirementResponse, RequirementSkillResponse
)
from app.services.jd_parser import parse_jd
from app.services.skill_alias import extract_atomic_skills
from app.services.match_engine import evaluate_match
from app.services.match_explainer import generate_match_explanation

router = APIRouter(prefix="/requirements", tags=["Requirements"])


def map_requirement_to_response(req: Requirement) -> dict:
    return {
        "id": req.id,
        "job_title": req.job_title,
        "job_description": req.job_description,
        "minimum_experience": req.minimum_experience,
        "maximum_experience": req.maximum_experience,
        "location": req.location,
        "employment_type": req.employment_type,
        "education_requirement": req.education_requirement,
        "status": req.status,
        "created_at": req.created_at,
        "active_candidate_matches_count": len(req.match_results) if req.match_results else 0,
        "skills": [
            RequirementSkillResponse.model_validate(s) for s in req.requirement_skills
        ] if req.requirement_skills else []
    }


@router.get("", response_model=List[RequirementResponse])
async def list_requirements(db: AsyncSession = Depends(get_db)):
    stmt_cands = select(Candidate.id)
    res_cands = await db.execute(stmt_cands)
    cand_ids = res_cands.scalars().all()
    total_cand_count = len(cand_ids)

    stmt = (
        select(Requirement)
        .options(
            selectinload(Requirement.requirement_skills),
            selectinload(Requirement.match_results)
        )
        .order_by(Requirement.created_at.desc())
    )
    res = await db.execute(stmt)
    requirements = res.scalars().all()

    # Sync missing matches for any requirement where match count < total candidates
    updated = False
    for req in requirements:
        existing_matched_cand_ids = {m.candidate_id for m in req.match_results} if req.match_results else set()
        if len(existing_matched_cand_ids) < total_cand_count:
            await match_candidates_for_requirement(req.id, db)
            updated = True

    if updated:
        res = await db.execute(stmt)
        requirements = res.scalars().all()

    return [map_requirement_to_response(r) for r in requirements]


@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(requirement_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Requirement)
        .where(Requirement.id == requirement_id)
        .options(
            selectinload(Requirement.requirement_skills),
            selectinload(Requirement.match_results)
        )
    )
    res = await db.execute(stmt)
    req = res.scalar_one_or_none()

    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    stmt_cands = select(Candidate.id)
    res_cands = await db.execute(stmt_cands)
    cand_ids = res_cands.scalars().all()

    existing_matched_cand_ids = {m.candidate_id for m in req.match_results} if req.match_results else set()
    if len(existing_matched_cand_ids) < len(cand_ids):
        await match_candidates_for_requirement(req.id, db)
        res = await db.execute(stmt)
        req = res.scalar_one_or_none()

    return map_requirement_to_response(req)


@router.post("", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(payload: RequirementCreate, db: AsyncSession = Depends(get_db)):
    req = Requirement(
        job_title=payload.job_title,
        job_description=payload.job_description,
        minimum_experience=payload.minimum_experience,
        maximum_experience=payload.maximum_experience,
        location=payload.location,
        employment_type=payload.employment_type or "Full-time",
        education_requirement=payload.education_requirement,
        status=payload.status or "ACTIVE"
    )
    db.add(req)
    await db.flush()

    # Parse JD text if skills not provided explicitly
    skills_to_add = []
    if payload.skills:
        for s in payload.skills:
            skills_to_add.append((s.skill, s.importance))
    elif payload.job_description:
        parsed_jd = await parse_jd(payload.job_description, payload.job_title)
        for s in parsed_jd.mandatory_skills:
            skills_to_add.append((s, "MANDATORY"))
        for s in parsed_jd.preferred_skills:
            skills_to_add.append((s, "PREFERRED"))

    for skill_name, imp in skills_to_add:
        req_skill = RequirementSkill(
            requirement_id=req.id,
            skill=skill_name,
            importance=imp
        )
        db.add(req_skill)

    await db.commit()

    # Auto-trigger matching against existing candidates
    await match_candidates_for_requirement(req.id, db)

    return await get_requirement(req.id, db)


# ── MATCHING ENDPOINTS ────────────────────────────────────────────────

async def recalculate_candidate_matches(candidate_id: str, db: AsyncSession):
    """Recalculate match results across all requirements for a specific candidate after profile edits."""
    stmt_c = (
        select(Candidate)
        .where(Candidate.id == candidate_id)
        .options(
            selectinload(Candidate.candidate_skills).selectinload(CandidateSkill.skill),
            selectinload(Candidate.education),
        )
    )
    res_c = await db.execute(stmt_c)
    cand = res_c.scalar_one_or_none()
    if not cand:
        return

    stmt_r = select(Requirement).options(selectinload(Requirement.requirement_skills))
    res_r = await db.execute(stmt_r)
    reqs = res_r.scalars().all()

    for req in reqs:
        await _match_single_candidate(req, cand, db, skip_llm=True)

    await db.commit()

async def _match_single_candidate(
    requirement: Requirement,
    candidate: Candidate,
    db: AsyncSession,
    skip_llm: bool = False
) -> MatchResult:
    """Internal helper to match single candidate against requirement."""
    # Build JD requirement dict
    mandatory_skills = [
        s.skill for s in requirement.requirement_skills if s.importance == "MANDATORY"
    ]
    preferred_skills = [
        s.skill for s in requirement.requirement_skills if s.importance == "PREFERRED"
    ]
    if not mandatory_skills and not preferred_skills and requirement.job_description:
        parsed_jd = parse_jd_deterministically(requirement.job_description, requirement.job_title)
        mandatory_skills = parsed_jd.mandatory_skills
        preferred_skills = parsed_jd.preferred_skills

    jd_data = {
        "job_title": requirement.job_title,
        "mandatory_skills": mandatory_skills,
        "preferred_skills": preferred_skills,
        "minimum_experience": requirement.minimum_experience,
        "education_requirement": requirement.education_requirement,
        "location": requirement.location,
    }

    raw_cand_skills = []
    if hasattr(candidate, "candidate_skills") and candidate.candidate_skills:
        for cs in candidate.candidate_skills:
            if hasattr(cs, "skill") and cs.skill:
                raw_cand_skills.append(cs.skill.name)
    
    if not raw_cand_skills:
        # Explicit query for candidate_skills
        stmt_skills = (
            select(CandidateSkill)
            .where(CandidateSkill.candidate_id == candidate.id)
            .options(selectinload(CandidateSkill.skill))
        )
        res_sk = await db.execute(stmt_skills)
        for cs in res_sk.scalars().all():
            if cs.skill and cs.skill.name:
                raw_cand_skills.append(cs.skill.name)

    cand_skills = []
    for raw_s in raw_cand_skills:
        for atomic_s in extract_atomic_skills(raw_s):
            if atomic_s and atomic_s not in cand_skills:
                cand_skills.append(atomic_s)

    cand_data = {
        "name": candidate.name,
        "skills": cand_skills,
        "experience_years": candidate.experience_years,
        "experience_months": candidate.experience_months,
        "current_company": candidate.current_company,
        "current_designation": candidate.current_designation,
        "latest_company": candidate.latest_company,
        "latest_designation": candidate.latest_designation,
        "education": [e.institution for e in candidate.education] if candidate.education else [],
        "location": candidate.current_location,
    }

    det_output = evaluate_match(jd_data, cand_data)

    if skip_llm:
        strengths = det_output.strengths or [f"Matching skills: {', '.join(det_output.matching_skills)}"]
        improvements = [f"If you have professional {s} experience, make it more visible on your resume." for s in det_output.missing_mandatory_skills[:3]] or ["Highlight relevant project impact."]
        explanation = f"Match score is {det_output.overall_score}%."
    else:
        strengths, improvements, explanation = await generate_match_explanation(
            match_result=det_output,
            jd_title=requirement.job_title,
            candidate_name=candidate.name,
        )

    # Check for existing match result record
    stmt = select(MatchResult).where(
        MatchResult.requirement_id == requirement.id,
        MatchResult.candidate_id == candidate.id
    )
    res = await db.execute(stmt)
    existing_match = res.scalar_one_or_none()

    if existing_match:
        match_rec = existing_match
    else:
        match_rec = MatchResult(
            requirement_id=requirement.id,
            candidate_id=candidate.id,
        )
        db.add(match_rec)

    match_rec.overall_score = det_output.overall_score
    match_rec.skill_score = det_output.skill_score
    match_rec.experience_score = det_output.experience_score
    match_rec.education_score = det_output.education_score
    match_rec.role_score = det_output.role_score
    match_rec.location_score = det_output.location_score
    match_rec.matching_skills = det_output.matching_skills
    match_rec.missing_mandatory_skills = det_output.missing_mandatory_skills
    match_rec.missing_preferred_skills = det_output.missing_preferred_skills
    match_rec.strengths = strengths
    match_rec.gaps = improvements
    match_rec.explanation = explanation

    return match_rec


@router.post("/{requirement_id}/match")
async def match_candidates_for_requirement(requirement_id: str, db: AsyncSession = Depends(get_db)):
    """Compare every parsed candidate resume against the given Requirement."""
    stmt_req = select(Requirement).where(Requirement.id == requirement_id).options(
        selectinload(Requirement.requirement_skills)
    )
    res_req = await db.execute(stmt_req)
    req = res_req.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    stmt_cands = select(Candidate).options(
        selectinload(Candidate.candidate_skills).selectinload(CandidateSkill.skill),
        selectinload(Candidate.education)
    )
    res_cands = await db.execute(stmt_cands)
    candidates = res_cands.scalars().all()

    matches = []
    for cand in candidates:
        match_rec = await _match_single_candidate(req, cand, db)
        matches.append(match_rec)

    await db.commit()
    return {"status": "SUCCESS", "matched_candidates_count": len(matches)}


@router.get("/{requirement_id}/matches")
async def get_requirement_matches(requirement_id: str, db: AsyncSession = Depends(get_db)):
    """List all candidate match results for a requirement, sorted by highest match score -> lowest."""
    stmt_req = select(Requirement).where(Requirement.id == requirement_id).options(
        selectinload(Requirement.requirement_skills)
    )
    res_req = await db.execute(stmt_req)
    req = res_req.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    stmt = (
        select(MatchResult)
        .where(MatchResult.requirement_id == requirement_id)
        .options(selectinload(MatchResult.candidate))
        .order_by(MatchResult.overall_score.desc())
    )
    res = await db.execute(stmt)
    match_results = res.scalars().all()

    results = []
    for m in match_results:
        cand = m.candidate
        results.append({
            "id": m.id,
            "requirement_id": m.requirement_id,
            "candidate_id": m.candidate_id,
            "candidate_name": cand.name if cand else "Unknown",
            "candidate_email": cand.email if cand else None,
            "current_company": cand.current_company if cand else None,
            "current_designation": cand.current_designation if cand else None,
            "experience_years": cand.experience_years if cand else None,
            "location": cand.current_location if cand else None,
            "overall_score": m.overall_score,
            "skill_score": m.skill_score,
            "experience_score": m.experience_score,
            "education_score": m.education_score,
            "role_score": m.role_score,
            "location_score": m.location_score,
            "matching_skills": m.matching_skills or [],
            "missing_mandatory_skills": m.missing_mandatory_skills or [],
            "missing_preferred_skills": m.missing_preferred_skills or [],
            "strengths": m.strengths or [],
            "gaps": m.gaps or [],
            "explanation": m.explanation,
            "created_at": m.created_at,
        })

    return results


@router.get("/{requirement_id}/matches/{candidate_id}")
async def get_candidate_match_details(requirement_id: str, candidate_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed Resume Match Report for specific candidate and requirement."""
    stmt = (
        select(MatchResult)
        .where(MatchResult.requirement_id == requirement_id, MatchResult.candidate_id == candidate_id)
        .options(selectinload(MatchResult.candidate), selectinload(MatchResult.requirement))
    )
    res = await db.execute(stmt)
    m = res.scalar_one_or_none()

    if not m:
        # Generate match on demand if not existing
        stmt_req = select(Requirement).where(Requirement.id == requirement_id).options(selectinload(Requirement.requirement_skills))
        stmt_cand = select(Candidate).where(Candidate.id == candidate_id).options(selectinload(Candidate.education))

        req = (await db.execute(stmt_req)).scalar_one_or_none()
        cand = (await db.execute(stmt_cand)).scalar_one_or_none()

        if not req or not cand:
            raise HTTPException(status_code=404, detail="Requirement or Candidate not found")

        m = await _match_single_candidate(req, cand, db)
        await db.commit()

    cand = m.candidate
    return {
        "id": m.id,
        "requirement_id": m.requirement_id,
        "candidate_id": m.candidate_id,
        "candidate_name": cand.name if cand else "Unknown",
        "candidate_email": cand.email if cand else None,
        "candidate_phone": cand.phone if cand else None,
        "current_company": cand.current_company if cand else None,
        "current_designation": cand.current_designation if cand else None,
        "experience_years": cand.experience_years if cand else None,
        "location": cand.current_location if cand else None,
        "overall_score": m.overall_score,
        "skill_score": m.skill_score,
        "experience_score": m.experience_score,
        "education_score": m.education_score,
        "role_score": m.role_score,
        "location_score": m.location_score,
        "matching_skills": m.matching_skills or [],
        "missing_mandatory_skills": m.missing_mandatory_skills or [],
        "missing_preferred_skills": m.missing_preferred_skills or [],
        "strengths": m.strengths or [],
        "gaps": m.gaps or [],
        "explanation": m.explanation,
        "created_at": m.created_at,
    }


@router.post("/{requirement_id}/match/{candidate_id}")
async def match_single_candidate_endpoint(requirement_id: str, candidate_id: str, db: AsyncSession = Depends(get_db)):
    """Run/rematch single candidate against requirement."""
    return await get_candidate_match_details(requirement_id, candidate_id, db)
