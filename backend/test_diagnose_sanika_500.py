import asyncio
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal, init_db
from app.models import Candidate, CandidateExperience, Resume, CandidateSkill, MatchResult
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def diagnose_sanika():
    print("=" * 75)
    print("DIAGNOSING REAL CANDIDATE DELETION (SANIKA VAVHAL)")
    print("=" * 75)

    await init_db()

    async with AsyncSessionLocal() as session:
        cand_id = "e1613919-3e78-409b-b731-dbdebf65f92e"
        stmt = select(Candidate).where(Candidate.id == cand_id).options(
            selectinload(Candidate.resumes),
            selectinload(Candidate.experiences),
            selectinload(Candidate.candidate_skills),
            selectinload(Candidate.match_results)
        )
        cand = (await session.execute(stmt)).scalar_one_or_none()

        if not cand:
            print(f"Sanika candidate ID {cand_id} not found!")
            return

        print(f"Found Candidate: {cand.name}")
        print(f"  Resumes: {len(cand.resumes)}")
        print(f"  Experiences: {len(cand.experiences)}")
        print(f"  Skills: {len(cand.candidate_skills)}")
        print(f"  Match Results: {len(cand.match_results)}")

        # Print experience resume_id values
        for exp in cand.experiences:
            print(f"  Experience ID: {exp.id}, company: {exp.company}, resume_id: {exp.resume_id}")

        # Try deletion in a nested transaction and catch exact exception
        try:
            # We will use savepoint/rollback so real data is preserved!
            async with session.begin_nested():
                await session.delete(cand)
                await session.flush()
                print("Flush succeeded!")
            print("Nested transaction deletion check completed without error!")
        except Exception as e:
            print("\n" + "=" * 75)
            print("EXACT EXCEPTION CAPTURED:")
            print(f"Exception type: {type(e).__name__}")
            print(f"Exception message: {str(e)}")
            print("FULL TRACEBACK:")
            traceback.print_exc()
            print("=" * 75)


if __name__ == "__main__":
    asyncio.run(diagnose_sanika())
