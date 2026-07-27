import asyncio
import os
import sys
import traceback
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal, init_db
from app.models import (
    Candidate, Resume, CandidateExperience, CandidateSkill, CandidateEducation,
    CandidateCertification, CandidateProject, MatchResult, RecruiterNote,
    CandidateContactEvent, TimelineEvent, Requirement, Skill
)
from sqlalchemy import select, delete


async def diagnose_deletion():
    print("=" * 75)
    print("DIAGNOSING BACKEND 500 ERROR ON CANDIDATE DELETION")
    print("=" * 75)

    await init_db()

    async with AsyncSessionLocal() as session:
        # Create temp candidate with full set of related records
        cand_id = str(uuid.uuid4())
        cand = Candidate(id=cand_id, name="500 DIAGNOSTIC TEST CANDIDATE")
        session.add(cand)
        await session.flush()

        res_id = str(uuid.uuid4())
        res = Resume(
            id=res_id,
            candidate_id=cand_id,
            original_filename="test.pdf",
            stored_filename=f"test_{uuid.uuid4().hex[:6]}.pdf",
            local_path="/tmp/test.pdf",
            file_type="pdf",
            file_size=1024
        )
        session.add(res)

        exp = CandidateExperience(
            id=str(uuid.uuid4()),
            candidate_id=cand_id,
            resume_id=res_id,
            company="TestCo",
            designation="Developer"
        )
        session.add(exp)

        sk_obj = Skill(id=str(uuid.uuid4()), name=f"DiagSkill_{uuid.uuid4().hex[:4]}")
        session.add(sk_obj)
        await session.flush()

        c_sk = CandidateSkill(id=str(uuid.uuid4()), candidate_id=cand_id, skill_id=sk_obj.id)
        session.add(c_sk)

        edu = CandidateEducation(id=str(uuid.uuid4()), candidate_id=cand_id, institution="TestUni", degree="B.S.")
        session.add(edu)

        cert = CandidateCertification(id=str(uuid.uuid4()), candidate_id=cand_id, name="TestCert")
        session.add(cert)

        proj = CandidateProject(id=str(uuid.uuid4()), candidate_id=cand_id, name="TestProj")
        session.add(proj)

        note = RecruiterNote(id=str(uuid.uuid4()), candidate_id=cand_id, content="Test Note")
        session.add(note)

        event = CandidateContactEvent(id=str(uuid.uuid4()), candidate_id=cand_id, event_type="EMAIL", date="2026-07-26")
        session.add(event)

        timeline = TimelineEvent(id=str(uuid.uuid4()), candidate_id=cand_id, event_type="NOTE", title="Test Event")
        session.add(timeline)

        req = (await session.execute(select(Requirement))).scalars().first()
        if req:
            match = MatchResult(id=str(uuid.uuid4()), candidate_id=cand_id, requirement_id=req.id, overall_score=80.0)
            session.add(match)

        await session.commit()
        print(f"Created candidate {cand_id} with full set of related records.")

        # Try db.delete(cand) inside async session to catch exact exception
        try:
            stmt = select(Candidate).where(Candidate.id == cand_id)
            cand_to_del = (await session.execute(stmt)).scalar_one_or_none()
            await session.delete(cand_to_del)
            await session.commit()
            print("Deletion succeeded without error!")
        except Exception as e:
            print("\nEXCEPTION CAUGHT DURING DELETION:")
            print(f"Exception type: {type(e).__name__}")
            print(f"Exception message: {str(e)}")
            print("\nFULL TRACEBACK:")
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(diagnose_deletion())
