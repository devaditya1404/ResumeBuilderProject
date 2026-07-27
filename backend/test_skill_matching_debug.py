import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal, init_db
from app.models import Candidate, CandidateSkill, Requirement
from app.services.skill_alias import skills_match, normalize_skill_name, extract_atomic_skills
from app.services.match_engine import evaluate_match
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def inspect_sanika():
    await init_db()
    async with AsyncSessionLocal() as session:
        # Find Sanika
        stmt = select(Candidate).where(Candidate.name.like("%Sanika%")).options(
            selectinload(Candidate.candidate_skills).selectinload(CandidateSkill.skill)
        )
        res = await session.execute(stmt)
        cand = res.scalar_one_or_none()

        if not cand:
            print("Sanika Vavhal not found!")
            return

        raw_skills = [cs.skill.name for cs in cand.candidate_skills if cs.skill] if cand.candidate_skills else []
        print(f"CANDIDATE: {cand.name}")
        print(f"RAW DB SKILLS: {raw_skills}")

        atomic = []
        for s in raw_skills:
            atomic.extend(extract_atomic_skills(s))
        print(f"ATOMIC NORMALIZED SKILLS: {atomic}")

        # Find MIS Executive requirement
        stmt_req = select(Requirement).where(Requirement.job_title.like("%MIS Executive%")).options(
            selectinload(Requirement.requirement_skills)
        )
        res_req = await session.execute(stmt_req)
        reqs = res_req.scalars().all()

        for req in reqs:
            print(f"\nJD: {req.job_title} (ID: {req.id})")
            mandatory = [s.skill for s in req.requirement_skills if s.importance == "MANDATORY"]
            preferred = [s.skill for s in req.requirement_skills if s.importance == "PREFERRED"]
            print(f"MANDATORY: {mandatory}")
            print(f"PREFERRED: {preferred}")

            jd_data = {
                "job_title": req.job_title,
                "mandatory_skills": mandatory,
                "preferred_skills": preferred,
                "minimum_experience": req.minimum_experience,
            }
            cand_data = {
                "name": cand.name,
                "skills": atomic,
                "experience_years": cand.experience_years,
            }

            match_res = evaluate_match(jd_data, cand_data)
            print(f"MATCHED: {match_res.matching_skills}")
            print(f"MISSING MANDATORY: {match_res.missing_mandatory_skills}")
            print(f"MISSING PREFERRED: {match_res.missing_preferred_skills}")
            print(f"SKILL SCORE: {match_res.skill_score}%")
            print(f"EXPERIENCE SCORE: {match_res.experience_score}%")
            print(f"OVERALL SCORE: {match_res.overall_score}%")


if __name__ == "__main__":
    asyncio.run(inspect_sanika())
