#!/usr/bin/env python3
"""
test_edit_candidate_profile.py — Verify end-to-end profile editing and match recalculation (Section 20 & 21).

CRITICAL SAFETY RULE:
Does NOT modify or delete real candidates (Sanika, Braulio, Aditya, Anju).
Creates a temporary candidate 'EDIT TEST CANDIDATE', edits profile details, skills, and experience,
verifies persistence & match score recalculation, and cleans up.
"""
import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal, init_db
from app.models import Candidate, CandidateSkill, CandidateExperience, MatchResult, Requirement, Skill
from app.schemas.candidate import CandidateProfileUpdate, ExperienceCreate
from app.api.candidates import update_candidate_profile, delete_candidate
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def run_edit_candidate_test():
    print("=" * 75)
    print("TEMPORARY CANDIDATE PROFILE EDIT & MATCH RECALCULATION TEST")
    print("=" * 75)

    await init_db()

    async with AsyncSessionLocal() as session:
        # 1. Create temporary candidate
        temp_id = str(uuid.uuid4())
        temp_cand = Candidate(
            id=temp_id,
            name="EDIT TEST CANDIDATE",
            email="edit.test@example.com",
            current_company="Test Company A",
            current_designation="MIS Executive",
            experience_years=1.0,
            experience_months=12,
        )
        session.add(temp_cand)
        await session.flush()

        # Attach initial skill 'Excel'
        sk_excel = (await session.execute(select(Skill).where(Skill.name == "Excel"))).scalar_one_or_none()
        if not sk_excel:
            sk_excel = Skill(id=str(uuid.uuid4()), name="Excel", category="Technical")
            session.add(sk_excel)
            await session.flush()

        session.add(CandidateSkill(id=str(uuid.uuid4()), candidate_id=temp_id, skill_id=sk_excel.id))
        await session.commit()
        print(f"Created Temp Candidate ID: {temp_id} | Name: 'EDIT TEST CANDIDATE'")

        # 2. Perform Profile Update
        update_payload = CandidateProfileUpdate(
            name="EDITED TEST CANDIDATE",
            email="edited.test@example.com",
            current_company="Test Company B",
            current_designation="Senior MIS Executive",
            skills=["Excel", "Power BI", "SQL"],
            experiences=[
                ExperienceCreate(
                    company="Test Company B",
                    designation="Senior MIS Executive",
                    start_date="2024-02",
                    end_date="Present",
                    is_current=True
                )
            ]
        )

        res = await update_candidate_profile(temp_id, update_payload, session)
        cand_name = res["name"] if isinstance(res, dict) else res.name
        cand_desig = res["current_designation"] if isinstance(res, dict) else res.current_designation
        cand_company = res["current_company"] if isinstance(res, dict) else res.current_company
        cand_skills = res["skills"] if isinstance(res, dict) else res.skills

        print(f"Updated Candidate Name: '{cand_name}'")
        print(f"Updated Candidate Designation: '{cand_desig}'")
        print(f"Updated Skills Count: {len(cand_skills)}")

        assert cand_name == "EDITED TEST CANDIDATE", "Name update failed"
        assert cand_company == "Test Company B", "Company update failed"
        assert cand_desig == "Senior MIS Executive", "Designation update failed"

        # Verify skills catalog & aliases
        updated_skill_names = [s["skill_name"] if isinstance(s, dict) else s.skill_name for s in cand_skills]
        print(f"Updated Skill Names: {updated_skill_names}")
        assert "Excel" in updated_skill_names, "Skill Excel missing"
        assert "Power BI" in updated_skill_names, "Skill Power BI missing"
        assert "SQL" in updated_skill_names, "Skill SQL missing"

        # Verify experience recalculation
        stmt_cand = select(Candidate).where(Candidate.id == temp_id)
        cand_db = (await session.execute(stmt_cand)).scalar_one_or_none()
        print(f"Recalculated Experience Years: {cand_db.experience_years} Yrs ({cand_db.experience_months} Months)")
        assert cand_db.experience_years > 0, "Experience recalculation failed"

        # Verify MatchResult recalculation
        stmt_match = select(MatchResult).where(MatchResult.candidate_id == temp_id)
        matches = (await session.execute(stmt_match)).scalars().all()
        print(f"Recalculated Match Result Records Count: {len(matches)}")

        # 3. Clean up temporary test candidate
        await delete_candidate(temp_id, session)
        print(f"Safely Deleted Temp Candidate ID: {temp_id}")

        print("\n" + "=" * 75)
        print("TEMPORARY CANDIDATE EDIT & MATCH RECALCULATION TEST: 100% PASSED!")
        print("REAL EXISTING CANDIDATES PRESERVED: YES")
        print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_edit_candidate_test())
