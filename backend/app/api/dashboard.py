from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.database import get_db
from app.models import Candidate, Resume, Requirement, MatchResult, CandidateContactEvent, CandidateSkill, Skill
from app.schemas.dashboard import (
    DashboardStatsResponse, SkillDistributionItem, ExperienceDistributionItem, UploadActivityItem
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # Total candidates count
    tot_cand_res = await db.execute(select(func.count(Candidate.id)))
    total_candidates = tot_cand_res.scalar() or 0

    # New resumes (uploaded in last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    new_res_stmt = select(func.count(Resume.id)).where(Resume.uploaded_at >= seven_days_ago)
    new_res_res = await db.execute(new_res_stmt)
    new_resumes = new_res_res.scalar() or 0

    # Active requirements count
    act_req_stmt = select(func.count(Requirement.id)).where(Requirement.status == "ACTIVE")
    act_req_res = await db.execute(act_req_stmt)
    active_requirements = act_req_res.scalar() or 0

    # Top matches (> 80% score)
    top_m_stmt = select(func.count(MatchResult.id)).where(MatchResult.overall_score >= 80.0)
    top_m_res = await db.execute(top_m_stmt)
    top_matches = top_m_res.scalar() or 0

    # Candidates contacted
    contact_stmt = select(func.count(func.distinct(CandidateContactEvent.candidate_id)))
    contact_res = await db.execute(contact_stmt)
    candidates_contacted = contact_res.scalar() or 0

    # Average match score
    avg_m_stmt = select(func.avg(MatchResult.overall_score))
    avg_m_res = await db.execute(avg_m_stmt)
    avg_score_raw = avg_m_res.scalar()
    average_match_score = round(float(avg_score_raw), 1) if avg_score_raw is not None else 0.0

    # Skills distribution from database
    skill_dist = []
    if total_candidates > 0:
        skill_stmt = (
            select(Skill.name, func.count(CandidateSkill.candidate_id))
            .join(CandidateSkill, Skill.id == CandidateSkill.skill_id)
            .group_by(Skill.name)
            .order_by(func.count(CandidateSkill.candidate_id).desc())
            .limit(7)
        )
        s_res = await db.execute(skill_stmt)
        for s_name, count in s_res.all():
            skill_dist.append(SkillDistributionItem(name=s_name, count=count))

    # Experience distribution from database
    exp_dist = []
    if total_candidates > 0:
        r1 = await db.execute(select(func.count(Candidate.id)).where(Candidate.experience_years < 2.0))
        r2 = await db.execute(select(func.count(Candidate.id)).where(Candidate.experience_years >= 2.0, Candidate.experience_years < 5.0))
        r3 = await db.execute(select(func.count(Candidate.id)).where(Candidate.experience_years >= 5.0, Candidate.experience_years < 8.0))
        r4 = await db.execute(select(func.count(Candidate.id)).where(Candidate.experience_years >= 8.0))

        exp_dist = [
            ExperienceDistributionItem(range="0-2 Years", count=r1.scalar() or 0),
            ExperienceDistributionItem(range="2-5 Years", count=r2.scalar() or 0),
            ExperienceDistributionItem(range="5-8 Years", count=r3.scalar() or 0),
            ExperienceDistributionItem(range="8+ Years", count=r4.scalar() or 0),
        ]

    return DashboardStatsResponse(
        total_candidates=total_candidates,
        new_resumes=new_resumes,
        active_requirements=active_requirements,
        top_matches=top_matches,
        candidates_contacted=candidates_contacted,
        average_match_score=average_match_score,
        skills_distribution=skill_dist,
        experience_distribution=exp_dist,
        upload_activity=[]
    )
