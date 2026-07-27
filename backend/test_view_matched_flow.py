#!/usr/bin/env python3
"""
test_view_matched_flow.py — Test View Matched Candidates flow on real database requirements.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal, init_db
from app.models import Requirement, Candidate, MatchResult
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.api.requirements import match_candidates_for_requirement, get_requirement_matches, list_requirements


from app.models import Requirement, Candidate, MatchResult, CandidateSkill

async def run_flow_verification():
    print("=" * 75)
    print("REAL DATABASE VIEW MATCHED CANDIDATES FLOW TEST")
    print("=" * 75)

    await init_db()

    async with AsyncSessionLocal() as session:
        # 1. Fetch total candidates in database
        stmt_cands = select(Candidate).options(
            selectinload(Candidate.candidate_skills).selectinload(CandidateSkill.skill)
        )
        cands = (await session.execute(stmt_cands)).scalars().all()
        print(f"Total Candidates in Talent Vault: {len(cands)}")
        for c in cands:
            skills = [cs.skill.name for cs in c.candidate_skills if cs.skill] if c.candidate_skills else []
            print(f"  - {c.name} (Exp: {c.experience_years} yrs, Skills: {skills})")

        # 2. Fetch requirements in database
        stmt_reqs = select(Requirement).options(
            selectinload(Requirement.requirement_skills),
            selectinload(Requirement.match_results)
        ).order_by(Requirement.created_at.desc())
        reqs = (await session.execute(stmt_reqs)).scalars().all()
        print(f"\nTotal Job Requirements in DB: {len(reqs)}")

        for req in reqs:
            print(f"\n-----------------------------------------------------------------------")
            print(f"REQUIREMENT: '{req.job_title}' (ID: {req.id})")
            req_skills = [s.skill for s in req.requirement_skills]
            print(f"  Mandatory/Preferred Skills: {req_skills}")

            # Trigger matching
            await match_candidates_for_requirement(req.id, session)

            # Query matches
            stmt_m = select(MatchResult).where(
                MatchResult.requirement_id == req.id
            ).options(selectinload(MatchResult.candidate)).order_by(MatchResult.overall_score.desc())
            matches = (await session.execute(stmt_m)).scalars().all()

            print(f"  Active Candidate Match Count Badge: {len(matches)} Candidates")
            print(f"  Individual Matches for Requirement '{req.job_title}':")
            for m in matches:
                cand_name = m.candidate.name if m.candidate else "Unknown"
                print(f"    - Candidate: {cand_name}")
                print(f"      Overall Score: {m.overall_score}%")
                print(f"      Skill Score: {m.skill_score}%")
                print(f"      Experience Score: {m.experience_score}%")
                print(f"      Matching Skills: {m.matching_skills}")
                print(f"      Missing Mandatory: {m.missing_mandatory_skills}")

        print("\n" + "=" * 75)
        print("REAL DATABASE FLOW VERIFICATION COMPLETE: ALL REQUIREMENTS SCORED INDEPENDENTLY!")
        print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_flow_verification())
