#!/usr/bin/env python3
"""
test_candidate_deletion.py — Verify CASCADE deletion of candidate and related records (Section 11).

CRITICAL SAFETY RULE:
Does NOT modify or delete real candidates (Sanika, Braulio, Aditya, Anju).
Creates a temporary candidate 'DELETE TEST CANDIDATE', attaches skills, experience, and match results,
verifies presence, calls deletion logic, and verifies 100% cascade cleanup.
"""
import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal, init_db
from app.models import (
    Candidate, CandidateSkill, CandidateExperience, CandidateEducation,
    MatchResult, Requirement, Skill, Resume, TimelineEvent
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def run_deletion_test():
    print("=" * 75)
    print("TEMPORARY CANDIDATE CASCADE DELETION TEST")
    print("=" * 75)

    await init_db()

    async with AsyncSessionLocal() as session:
        # 1. Count existing candidates before test
        stmt_initial = select(Candidate)
        initial_cands = (await session.execute(stmt_initial)).scalars().all()
        initial_count = len(initial_cands)
        print(f"Initial DB Candidate Count: {initial_count}")

        # 2. Create temporary test candidate
        temp_cand_id = str(uuid.uuid4())
        temp_cand = Candidate(
            id=temp_cand_id,
            name="DELETE TEST CANDIDATE",
            email="delete.test@example.com",
            current_designation="Temporary Test Engineer",
            experience_years=3.0,
        )
        session.add(temp_cand)
        await session.flush()

        # Add temporary Skill & CandidateSkill
        temp_skill = Skill(id=str(uuid.uuid4()), name=f"TempSkill_{uuid.uuid4().hex[:6]}")
        session.add(temp_skill)
        await session.flush()

        temp_cs = CandidateSkill(
            id=str(uuid.uuid4()),
            candidate_id=temp_cand_id,
            skill_id=temp_skill.id,
            source="test"
        )
        session.add(temp_cs)

        # Add temporary CandidateExperience
        temp_exp = CandidateExperience(
            id=str(uuid.uuid4()),
            candidate_id=temp_cand_id,
            company="Temp Test Company",
            designation="Tester"
        )
        session.add(temp_exp)

        # Add temporary MatchResult
        stmt_req = select(Requirement)
        res_req = await session.execute(stmt_req)
        first_req = res_req.scalars().first()

        if first_req:
            temp_match = MatchResult(
                id=str(uuid.uuid4()),
                candidate_id=temp_cand_id,
                requirement_id=first_req.id,
                overall_score=85.0
            )
            session.add(temp_match)

        await session.commit()
        print(f"Created Temporary Test Candidate ID: {temp_cand_id}")

        # Count after creation
        cands_after_create = (await session.execute(select(Candidate))).scalars().all()
        print(f"DB Candidate Count after creation: {len(cands_after_create)} (Expected {initial_count + 1})")
        assert len(cands_after_create) == initial_count + 1, "Candidate creation failed"

        # 3. Perform Deletion on Temporary Candidate ONLY
        stmt_del = select(Candidate).where(Candidate.id == temp_cand_id)
        cand_to_del = (await session.execute(stmt_del)).scalar_one_or_none()
        assert cand_to_del is not None, "Temporary candidate missing before deletion"

        await session.delete(cand_to_del)
        await session.commit()
        print(f"Executed Deletion for Candidate ID: {temp_cand_id}")

        # 4. Verify CASCADE Cleanup
        stmt_verify_cand = select(Candidate).where(Candidate.id == temp_cand_id)
        deleted_cand = (await session.execute(stmt_verify_cand)).scalar_one_or_none()
        assert deleted_cand is None, "VERIFICATION FAIL: Candidate record still exists in DB!"

        stmt_verify_cs = select(CandidateSkill).where(CandidateSkill.candidate_id == temp_cand_id)
        deleted_cs = (await session.execute(stmt_verify_cs)).scalars().all()
        assert len(deleted_cs) == 0, "VERIFICATION FAIL: CandidateSkill records still exist in DB!"

        stmt_verify_exp = select(CandidateExperience).where(CandidateExperience.candidate_id == temp_cand_id)
        deleted_exp = (await session.execute(stmt_verify_exp)).scalars().all()
        assert len(deleted_exp) == 0, "VERIFICATION FAIL: CandidateExperience records still exist in DB!"

        stmt_verify_match = select(MatchResult).where(MatchResult.candidate_id == temp_cand_id)
        deleted_match = (await session.execute(stmt_verify_match)).scalars().all()
        assert len(deleted_match) == 0, "VERIFICATION FAIL: MatchResult records still exist in DB!"

        # Final count check
        final_cands = (await session.execute(select(Candidate))).scalars().all()
        final_count = len(final_cands)
        print(f"Final DB Candidate Count: {final_count} (Matches initial count {initial_count})")
        assert final_count == initial_count, "Final candidate count does not match initial count"

        print("\n" + "=" * 75)
        print("CASCADE DELETION & SAFE CLEANUP TEST: 100% PASSED!")
        print("REAL EXISTING CANDIDATES PRESERVED: YES")
        print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_deletion_test())
