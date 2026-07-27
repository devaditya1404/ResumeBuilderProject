from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete, func

from app.core.database import get_db
from app.models import (
    Candidate, CandidateExperience, Skill, CandidateSkill, 
    CandidateEducation, CandidateCertification, CandidateProject, RecruiterNote, CandidateContactEvent, TimelineEvent
)
from app.schemas.candidate import (
    CandidateCreate, CandidateUpdate, CandidateProfileUpdate, CandidateResponse,
    CandidateSkillResponse, ExperienceResponse, EducationResponse, CertificationResponse
)
from app.services.skill_alias import extract_atomic_skills, normalize_skill_name
from app.services.experience_calculator import calculate_experience_from_records

router = APIRouter(prefix="/candidates", tags=["Candidates"])

def map_candidate_to_response(cand: Candidate) -> dict:
    skills_list = []
    if cand.candidate_skills:
        for cs in cand.candidate_skills:
            if cs.skill:
                skills_list.append(CandidateSkillResponse(
                    skill_name=cs.skill.name,
                    category=cs.skill.category or "Technical",
                    source=cs.source or "resume",
                    confidence=cs.confidence or 1.0
                ))

    return {
        "id": cand.id,
        "name": cand.name,
        "email": cand.email,
        "phone": cand.phone,
        "linkedin_url": cand.linkedin_url,
        "github_url": cand.github_url,
        "portfolio_url": cand.portfolio_url,
        "current_location": cand.current_location,
        "current_company": cand.current_company,
        "current_designation": cand.current_designation,
        "latest_company": cand.latest_company,
        "latest_designation": cand.latest_designation,
        "experience_months": cand.experience_months or 0,
        "experience_years": cand.experience_years or 0.0,
        "notice_period": cand.notice_period,
        "preferred_location": cand.preferred_location,
        "expected_salary": cand.expected_salary,
        "professional_summary": cand.professional_summary,
        "created_at": cand.created_at,
        "updated_at": cand.updated_at,
        "experiences": [
            ExperienceResponse.model_validate(e) for e in cand.experiences
        ] if cand.experiences else [],
        "skills": skills_list,
        "education": [
            EducationResponse.model_validate(ed) for ed in cand.education
        ] if cand.education else [],
        "certifications": [
            CertificationResponse.model_validate(c) for c in cand.certifications
        ] if cand.certifications else []
    }

@router.get("", response_model=List[CandidateResponse])
async def list_candidates(
    search: Optional[str] = None,
    skill: Optional[str] = None,
    location: Optional[str] = None,
    min_exp: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Candidate)
        .options(
            selectinload(Candidate.experiences),
            selectinload(Candidate.candidate_skills).selectinload(CandidateSkill.skill),
            selectinload(Candidate.education),
            selectinload(Candidate.certifications),
            selectinload(Candidate.resumes)
        )
        .order_by(Candidate.created_at.desc())
    )

    result = await db.execute(stmt)
    candidates = result.scalars().all()

    filtered = []
    for cand in candidates:
        if search:
            q = search.lower()
            matches_name = q in cand.name.lower()
            matches_desig = cand.current_designation and q in cand.current_designation.lower()
            matches_company = cand.current_company and q in cand.current_company.lower()
            matches_summary = cand.professional_summary and q in cand.professional_summary.lower()
            if not (matches_name or matches_desig or matches_company or matches_summary):
                continue

        if min_exp and (cand.experience_years or 0.0) < min_exp:
            continue

        if location and cand.current_location:
            if location.lower() not in cand.current_location.lower():
                continue

        if skill and cand.candidate_skills:
            skill_names = [cs.skill.name.lower() for cs in cand.candidate_skills if cs.skill]
            if skill.lower() not in skill_names:
                continue

        filtered.append(map_candidate_to_response(cand))

    return filtered

@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Candidate)
        .where(Candidate.id == candidate_id)
        .options(
            selectinload(Candidate.experiences),
            selectinload(Candidate.candidate_skills).selectinload(CandidateSkill.skill),
            selectinload(Candidate.education),
            selectinload(Candidate.certifications),
            selectinload(Candidate.resumes)
        )
    )
    result = await db.execute(stmt)
    cand = result.scalar_one_or_none()

    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return map_candidate_to_response(cand)

@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate(payload: CandidateCreate, db: AsyncSession = Depends(get_db)):
    # Explicitly preserve NULL for missing fields
    cand = Candidate(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        linkedin_url=payload.linkedin_url,
        github_url=payload.github_url,
        portfolio_url=payload.portfolio_url,
        current_location=payload.current_location,
        current_company=payload.current_company,
        current_designation=payload.current_designation,
        latest_company=payload.latest_company,
        latest_designation=payload.latest_designation,
        experience_months=payload.experience_months or 0,
        experience_years=payload.experience_years or 0.0,
        notice_period=payload.notice_period,      # NULL if not provided
        preferred_location=payload.preferred_location, # NULL if not provided
        expected_salary=payload.expected_salary,  # NULL if not provided
        professional_summary=payload.professional_summary
    )
    db.add(cand)
    await db.flush()

    # Experiences
    if payload.experiences:
        for idx, exp in enumerate(payload.experiences):
            exp_obj = CandidateExperience(
                candidate_id=cand.id,
                company=exp.company,
                designation=exp.designation,
                start_date=exp.start_date,
                end_date=exp.end_date,
                is_current=exp.is_current,
                duration_months=exp.duration_months or 0,
                responsibilities=exp.responsibilities or [],
                clients=exp.clients or [],
                display_order=idx
            )
            db.add(exp_obj)

    # Skills
    if payload.skills:
        for s_name in payload.skills:
            # Check or create skill catalog entry
            s_stmt = select(Skill).where(Skill.name == s_name)
            s_res = await db.execute(s_stmt)
            skill_obj = s_res.scalar_one_or_none()
            if not skill_obj:
                skill_obj = Skill(name=s_name, category="Technical")
                db.add(skill_obj)
                await db.flush()

            cs_obj = CandidateSkill(
                candidate_id=cand.id,
                skill_id=skill_obj.id,
                source="resume",
                confidence=1.0
            )
            db.add(cs_obj)

    # Education
    if payload.education:
        for ed in payload.education:
            ed_obj = CandidateEducation(
                candidate_id=cand.id,
                institution=ed.institution,
                degree=ed.degree,
                field=ed.field,
                start_date=ed.start_date,
                end_date=ed.end_date
            )
            db.add(ed_obj)

    # Certifications
    if payload.certifications:
        for cert in payload.certifications:
            cert_obj = CandidateCertification(
                candidate_id=cand.id,
                name=cert.name,
                issuer=cert.issuer,
                issue_date=cert.issue_date,
                expiry_date=cert.expiry_date
            )
            db.add(cert_obj)

    # Log Creation Timeline Event
    t_evt = TimelineEvent(
        candidate_id=cand.id,
        event_type="UPLOAD",
        title="Candidate Profile Created",
        description="Profile registered in local Talent Vault"
    )
    db.add(t_evt)

    await db.commit()
    return await get_candidate(cand.id, db)

@router.put("/{candidate_id}/profile", response_model=CandidateResponse)
@router.patch("/{candidate_id}/profile", response_model=CandidateResponse)
async def update_candidate_profile(
    candidate_id: str,
    payload: CandidateProfileUpdate,
    db: AsyncSession = Depends(get_db)
):
    from app.api.requirements import recalculate_candidate_matches

    stmt = select(Candidate).where(Candidate.id == candidate_id)
    res = await db.execute(stmt)
    cand = res.scalar_one_or_none()

    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Basic Candidate Fields
    update_data = payload.model_dump(exclude_unset=True)
    basic_fields = [
        "name", "email", "phone", "linkedin_url", "github_url", "portfolio_url",
        "current_location", "preferred_location", "current_company", "current_designation",
        "latest_company", "latest_designation", "notice_period", "expected_salary",
        "professional_summary"
    ]
    for field in basic_fields:
        if field in update_data and update_data[field] is not None:
            setattr(cand, field, update_data[field])

    # Experiences
    if payload.experiences is not None:
        await db.execute(delete(CandidateExperience).where(CandidateExperience.candidate_id == candidate_id))
        for idx, exp in enumerate(payload.experiences):
            db_exp = CandidateExperience(
                candidate_id=candidate_id,
                company=exp.company,
                designation=exp.designation,
                start_date=exp.start_date,
                end_date=exp.end_date,
                is_current=exp.is_current,
                duration_months=exp.duration_months or 0,
                responsibilities=exp.responsibilities or [],
                clients=exp.clients or [],
                display_order=idx
            )
            db.add(db_exp)

        # Recalculate total experience automatically from employment history
        tot_m, tot_y = calculate_experience_from_records(payload.experiences)
        cand.experience_months = tot_m
        cand.experience_years = tot_y

    # Skills
    if payload.skills is not None:
        await db.execute(delete(CandidateSkill).where(CandidateSkill.candidate_id == candidate_id))
        seen_skills = set()
        for raw_s in payload.skills:
            for atomic_s in extract_atomic_skills(raw_s):
                if not atomic_s:
                    continue
                canon_s = normalize_skill_name(atomic_s)
                if canon_s.lower() in seen_skills:
                    continue
                seen_skills.add(canon_s.lower())

                # Catalog lookup / insert
                s_stmt = select(Skill).where(func.lower(Skill.name) == canon_s.lower())
                s_res = await db.execute(s_stmt)
                skill_obj = s_res.scalar_one_or_none()
                if not skill_obj:
                    skill_obj = Skill(name=canon_s, category="Technical")
                    db.add(skill_obj)
                    await db.flush()

                cs_obj = CandidateSkill(
                    candidate_id=candidate_id,
                    skill_id=skill_obj.id,
                    source="manual_edit",
                    confidence=1.0
                )
                db.add(cs_obj)

    # Education
    if payload.education is not None:
        await db.execute(delete(CandidateEducation).where(CandidateEducation.candidate_id == candidate_id))
        for ed in payload.education:
            db_edu = CandidateEducation(
                candidate_id=candidate_id,
                institution=ed.institution,
                degree=ed.degree,
                field=ed.field,
                start_date=ed.start_date,
                end_date=ed.end_date
            )
            db.add(db_edu)

    # Certifications
    if payload.certifications is not None:
        await db.execute(delete(CandidateCertification).where(CandidateCertification.candidate_id == candidate_id))
        for cert in payload.certifications:
            db_cert = CandidateCertification(
                candidate_id=candidate_id,
                name=cert.name,
                issuer=cert.issuer,
                issue_date=cert.issue_date,
                expiry_date=cert.expiry_date
            )
            db.add(db_cert)

    # Projects
    if payload.projects is not None:
        await db.execute(delete(CandidateProject).where(CandidateProject.candidate_id == candidate_id))
        for proj in payload.projects:
            db_proj = CandidateProject(
                candidate_id=candidate_id,
                name=proj.name,
                description=proj.description,
                technologies=proj.technologies or [],
                start_date=proj.start_date,
                end_date=proj.end_date
            )
            db.add(db_proj)

    # Timeline event
    db.add(TimelineEvent(
        candidate_id=candidate_id,
        event_type="MANUAL_EDIT",
        title="Candidate Profile Manually Updated",
        description="Profile details, skills, or employment history updated by recruiter."
    ))

    await db.commit()

    # Recalculate matches across all requirements for this candidate
    await recalculate_candidate_matches(candidate_id, db)

    return await get_candidate(candidate_id, db)


@router.patch("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(candidate_id: str, payload: CandidateUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(Candidate).where(Candidate.id == candidate_id)
    res = await db.execute(stmt)
    cand = res.scalar_one_or_none()

    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(cand, field, val)

    await db.commit()
    return await get_candidate(candidate_id, db)

@router.delete("/{candidate_id}")
async def delete_candidate(candidate_id: str, db: AsyncSession = Depends(get_db)):
    import os
    from app.models import (
        CandidateExperience, CandidateSkill, CandidateEducation,
        CandidateCertification, CandidateProject, RecruiterNote,
        CandidateContactEvent, TimelineEvent, MatchResult, Resume
    )

    print(f"DELETE candidate request received: {candidate_id}")
    stmt = select(Candidate).where(Candidate.id == candidate_id).options(
        selectinload(Candidate.resumes)
    )
    res = await db.execute(stmt)
    cand = res.scalar_one_or_none()

    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Collect physical resume local_path values before DB deletion
    file_paths_to_delete = [
        r.local_path for r in cand.resumes if hasattr(r, 'local_path') and r.local_path and os.path.exists(r.local_path)
    ]

    try:
        # Explicitly delete dependent records in safe foreign-key order
        await db.execute(delete(MatchResult).where(MatchResult.candidate_id == candidate_id))
        await db.execute(delete(RecruiterNote).where(RecruiterNote.candidate_id == candidate_id))
        await db.execute(delete(CandidateContactEvent).where(CandidateContactEvent.candidate_id == candidate_id))
        await db.execute(delete(TimelineEvent).where(TimelineEvent.candidate_id == candidate_id))

        await db.execute(delete(CandidateProject).where(CandidateProject.candidate_id == candidate_id))
        await db.execute(delete(CandidateCertification).where(CandidateCertification.candidate_id == candidate_id))
        await db.execute(delete(CandidateEducation).where(CandidateEducation.candidate_id == candidate_id))
        await db.execute(delete(CandidateSkill).where(CandidateSkill.candidate_id == candidate_id))
        await db.execute(delete(CandidateExperience).where(CandidateExperience.candidate_id == candidate_id))

        await db.execute(delete(Resume).where(Resume.candidate_id == candidate_id))
        await db.execute(delete(Candidate).where(Candidate.id == candidate_id))

        await db.commit()
    except Exception as ex:
        await db.rollback()
        print(f"Backend DELETE Exception: {str(ex)}")
        raise HTTPException(status_code=500, detail=f"Database deletion failed: {str(ex)}")

    # Clean up physical resume files safely after successful DB commit
    for fpath in file_paths_to_delete:
        try:
            os.remove(fpath)
        except Exception:
            pass

    return {
        "status": "success",
        "candidate_id": candidate_id,
        "message": "Candidate deleted successfully"
    }
