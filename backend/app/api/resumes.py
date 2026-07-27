"""
Resume Upload API.

POST /api/resumes/upload — Accepts PDF/DOCX files, parses them, and creates candidates.

Supports multiple file upload. Each file goes through the full pipeline:
validate → save → extract → parse → ground → persist → respond.
"""
import os
import uuid
import json
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.database import get_db
from app.core.config import settings
from app.models import (
    Candidate, Resume, CandidateExperience, Skill, CandidateSkill,
    CandidateEducation, CandidateCertification, CandidateProject, TimelineEvent,
)
from app.parsers.resume_parser import parse_resume
from app.parsers.experience_calculator import parse_date_range, calculate_months_between, PRESENT_PATTERNS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["Resumes"])

# ── Constants ──
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ── Utility functions ──

def _sanitize_filename(filename: str) -> str:
    """Remove path separators and unsafe characters from filenames."""
    safe = os.path.basename(filename)
    safe = "".join(c for c in safe if c.isalnum() or c in ".-_ ")
    return safe.strip() or "unnamed"


def _generate_stored_name(original: str) -> str:
    """Generate a unique stored filename: UUID_sanitized."""
    ext = os.path.splitext(original)[1].lower()
    sanitized = _sanitize_filename(os.path.splitext(original)[0])
    return f"{uuid.uuid4().hex[:12]}_{sanitized}{ext}"


# ── LIST endpoint (existing) ──

@router.get("", response_model=List[dict])
async def list_resumes(db: AsyncSession = Depends(get_db)):
    stmt = select(Resume).order_by(Resume.uploaded_at.desc())
    res = await db.execute(stmt)
    resumes = res.scalars().all()

    return [
        {
            "id": r.id,
            "candidate_id": r.candidate_id,
            "original_filename": r.original_filename,
            "stored_filename": r.stored_filename,
            "local_path": r.local_path,
            "file_type": r.file_type,
            "file_size": r.file_size,
            "version": r.version,
            "uploaded_at": r.uploaded_at,
            "parsing_status": r.parsing_status,
        }
        for r in resumes
    ]


# ── UPLOAD endpoint ──

@router.post("/upload")
async def upload_resumes(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload one or more resume files.
    Each file is parsed and a candidate profile is created or updated.
    """
    results = []

    for file in files:
        result = await _process_single_file(file, db)
        results.append(result)

    # Summary
    success_count = sum(1 for r in results if r.get("success"))
    failed_count = len(results) - success_count

    return {
        "total": len(results),
        "success": success_count,
        "failed": failed_count,
        "results": results,
    }


async def _process_single_file(file: UploadFile, db: AsyncSession) -> dict:
    """Process a single uploaded resume file through the full pipeline."""

    response = {
        "filename": file.filename,
        "success": False,
        "candidate_id": None,
        "candidate_name": None,
        "errors": [],
        "warnings": [],
        "timings": {},
    }

    # ── 1. Validate file ──
    if not file.filename:
        response["errors"].append("NO_FILENAME")
        return response

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        response["errors"].append(f"UNSUPPORTED_FORMAT: {ext}. Allowed: {ALLOWED_EXTENSIONS}")
        return response

    # Read file content
    content = await file.read()
    if not content:
        response["errors"].append("EMPTY_FILE")
        return response

    if len(content) > MAX_FILE_SIZE:
        response["errors"].append(f"FILE_TOO_LARGE: {len(content)} bytes (max {MAX_FILE_SIZE})")
        return response

    # ── 2. Save file locally ──
    stored_name = _generate_stored_name(file.filename)
    storage_dir = os.path.abspath(settings.RESUME_STORAGE_PATH)
    os.makedirs(storage_dir, exist_ok=True)
    file_path = os.path.join(storage_dir, stored_name)

    try:
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"Saved resume to: {file_path}")
    except Exception as e:
        response["errors"].append(f"FILE_SAVE_FAILED: {str(e)}")
        return response

    # ── 3. Parse resume (full pipeline) ──
    try:
        parse_result = await parse_resume(file_path)
    except Exception as e:
        logger.exception(f"Parse failed for {file.filename}")
        response["errors"].append(f"PARSE_EXCEPTION: {str(e)}")
        return response

    response["warnings"] = parse_result.warnings
    response["timings"] = {
        "extraction_ms": round(parse_result.timings.extraction_ms, 1),
        "llm_ms": round(parse_result.timings.llm_ms, 1),
        "total_ms": round(parse_result.timings.total_ms, 1),
    }

    if not parse_result.success:
        response["errors"] = parse_result.errors
        return response

    extraction = parse_result.extraction
    if not extraction:
        response["errors"].append("NO_EXTRACTION")
        return response

    # ── 4. Check for duplicate candidate (by email or phone) ──
    candidate = None
    if extraction.email:
        stmt = select(Candidate).where(
            func.lower(Candidate.email) == extraction.email.lower()
        )
        res = await db.execute(stmt)
        candidate = res.scalar_one_or_none()

    if not candidate and extraction.phone:
        stmt = select(Candidate).where(Candidate.phone == extraction.phone)
        res = await db.execute(stmt)
        candidate = res.scalar_one_or_none()

    is_update = candidate is not None

    # ── 5. Create or update candidate (atomic transaction) ──
    try:
        if is_update:
            # Update existing candidate
            candidate = await _update_candidate(candidate, extraction, parse_result, db)
        else:
            # Create new candidate
            candidate = await _create_candidate(extraction, parse_result)
            db.add(candidate)

        await db.flush()  # Ensure candidate.id is populated

        # ── 6. Create resume record ──
        resume = Resume(
            candidate_id=candidate.id,
            original_filename=file.filename,
            stored_filename=stored_name,
            local_path=file_path,
            file_type=ext.lstrip("."),
            file_size=len(content),
            version=1,
            raw_text=parse_result.raw_text[:50000] if parse_result.raw_text else None,
            parsing_status=parse_result.parsing_status,
            parsing_confidence=parse_result.text_quality_score,
            parsing_warnings=json.dumps(parse_result.warnings[:20]) if parse_result.warnings else None,
        )
        db.add(resume)
        await db.flush()  # Get resume.id

        # ── 7. Create experience records ──
        if extraction.experiences:
            for idx, exp in enumerate(extraction.experiences):
                if not exp.company and not exp.title:
                    continue

                # Calculate duration for this experience
                dr = parse_date_range(exp.start_date or "", exp.end_date or "")
                duration = calculate_months_between(dr.start_date, dr.end_date) if dr.start_date else 0

                db_exp = CandidateExperience(
                    candidate_id=candidate.id,
                    resume_id=resume.id,
                    company=exp.company or "Unknown",
                    designation=exp.title or "Unknown",
                    start_date=exp.start_date,
                    end_date=exp.end_date,
                    is_current=dr.is_current,
                    duration_months=duration,
                    responsibilities=[exp.description] if exp.description else [],
                    clients=[exp.client] if exp.client else [],
                    display_order=idx,
                )
                db.add(db_exp)

        # ── 8. Create skill records ──
        if extraction.skills:
            for skill_name in extraction.skills:
                skill_name = skill_name.strip()
                if not skill_name:
                    continue

                # Find or create skill in catalog
                stmt = select(Skill).where(func.lower(Skill.name) == skill_name.lower())
                res = await db.execute(stmt)
                skill = res.scalar_one_or_none()

                if not skill:
                    skill = Skill(name=skill_name)
                    db.add(skill)
                    await db.flush()

                # Create candidate-skill link (skip if already exists)
                stmt = select(CandidateSkill).where(
                    CandidateSkill.candidate_id == candidate.id,
                    CandidateSkill.skill_id == skill.id,
                )
                res = await db.execute(stmt)
                existing = res.scalar_one_or_none()

                if not existing:
                    db.add(CandidateSkill(
                        candidate_id=candidate.id,
                        skill_id=skill.id,
                        source="resume",
                        confidence=1.0,
                    ))

        # ── 9. Create education records ──
        if extraction.education:
            for edu in extraction.education:
                if not edu.institution and not edu.degree:
                    continue
                db.add(CandidateEducation(
                    candidate_id=candidate.id,
                    institution=edu.institution or "Unknown",
                    degree=edu.degree or "Unknown",
                    field=edu.field_of_study,
                    start_date=edu.start_year,
                    end_date=edu.end_year,
                ))

        # ── 10. Create certification records ──
        if extraction.certifications:
            for cert in extraction.certifications:
                if not cert.name:
                    continue
                db.add(CandidateCertification(
                    candidate_id=candidate.id,
                    name=cert.name,
                    issuer=cert.issuer,
                    issue_date=cert.date,
                ))

        # ── 11. Create project records ──
        if extraction.projects:
            for proj in extraction.projects:
                if not proj.name:
                    continue
                db.add(CandidateProject(
                    candidate_id=candidate.id,
                    name=proj.name,
                    description=proj.description,
                    technologies=[proj.technologies] if proj.technologies else [],
                ))

        # ── 12. Create timeline event ──
        event_title = f"Resume {'updated' if is_update else 'uploaded'}: {file.filename}"
        db.add(TimelineEvent(
            candidate_id=candidate.id,
            event_type="UPLOAD",
            title=event_title,
            description=f"Parsed via {parse_result.extraction_method} | "
                        f"LLM: {parse_result.llm_model or 'none'} | "
                        f"Quality: {parse_result.text_quality_score:.2f}",
        ))

        # ── Commit all ──
        await db.commit()
        await db.refresh(candidate)

        response["success"] = True
        response["upload_status"] = "SUCCESS"
        response["parsing_status"] = parse_result.parsing_status
        response["warnings"] = parse_result.warnings
        response["candidate_id"] = candidate.id
        response["candidate_name"] = candidate.name
        response["is_update"] = is_update
        response["extraction_summary"] = {
            "name": extraction.full_name,
            "email": extraction.email,
            "phone": extraction.phone,
            "current_employer": extraction.current_employer,
            "current_title": extraction.current_title,
            "skills_count": len(extraction.skills),
            "experience_count": len(extraction.experiences),
            "education_count": len(extraction.education),
            "certifications_count": len(extraction.certifications),
            "total_experience_months": parse_result.total_experience_months,
            "extraction_method": parse_result.extraction_method,
            "llm_model": parse_result.llm_model,
        }

    except Exception as e:
        await db.rollback()
        logger.exception(f"Database persistence failed for {file.filename}")
        response["errors"].append(f"DB_PERSIST_FAILED: {str(e)}")

    return response


async def _create_candidate(extraction, parse_result) -> Candidate:
    """Create a new Candidate model from extraction results."""
    return Candidate(
        name=extraction.full_name or "Unknown Candidate",
        email=extraction.email,
        phone=extraction.phone,
        linkedin_url=extraction.linkedin_url,
        github_url=extraction.github_url,
        portfolio_url=extraction.portfolio_url,
        current_location=extraction.location,
        current_company=parse_result.current_employer,
        current_designation=parse_result.current_title,
        latest_company=parse_result.current_employer,
        latest_designation=parse_result.current_title,
        experience_months=parse_result.total_experience_months,
        experience_years=round(parse_result.total_experience_months / 12, 1) if parse_result.total_experience_months else None,
        notice_period=extraction.notice_period,  # NULL if not stated
        expected_salary=extraction.expected_ctc,  # NULL if not stated
        professional_summary=extraction.summary,
    )


async def _update_candidate(candidate, extraction, parse_result, db) -> Candidate:
    """Update existing candidate with new resume data."""
    if extraction.full_name and extraction.full_name != "Unknown Candidate":
        candidate.name = extraction.full_name
    if extraction.phone:
        candidate.phone = extraction.phone
    if extraction.linkedin_url:
        candidate.linkedin_url = extraction.linkedin_url
    if extraction.github_url:
        candidate.github_url = extraction.github_url
    if extraction.portfolio_url:
        candidate.portfolio_url = extraction.portfolio_url
    if extraction.location:
        candidate.current_location = extraction.location

    candidate.current_company = parse_result.current_employer or candidate.current_company
    candidate.current_designation = parse_result.current_title or candidate.current_designation
    candidate.latest_company = parse_result.current_employer or candidate.latest_company
    candidate.latest_designation = parse_result.current_title or candidate.latest_designation

    if parse_result.total_experience_months:
        candidate.experience_months = parse_result.total_experience_months
        candidate.experience_years = round(parse_result.total_experience_months / 12, 1)

    # Only update notice_period / salary if explicitly stated in NEW resume
    if extraction.notice_period:
        candidate.notice_period = extraction.notice_period
    if extraction.expected_ctc:
        candidate.expected_salary = extraction.expected_ctc

    if extraction.summary:
        candidate.professional_summary = extraction.summary

    candidate.updated_at = datetime.utcnow()

    return candidate


def get_settings():
    return settings
