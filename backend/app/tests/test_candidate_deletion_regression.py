import pytest
import uuid
import os
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, init_db
from app.models import (
    Candidate, Resume, CandidateExperience, CandidateSkill, CandidateEducation,
    MatchResult, Requirement, Skill
)
from app.api.candidates import delete_candidate


@pytest.mark.asyncio
async def test_delete_candidate_with_related_records():
    await init_db()

    async with AsyncSessionLocal() as session:
        cand_id = str(uuid.uuid4())
        cand = Candidate(id=cand_id, name="REGRESSION TEST CANDIDATE")
        session.add(cand)
        await session.flush()

        res_id = str(uuid.uuid4())
        res = Resume(
            id=res_id,
            candidate_id=cand_id,
            original_filename="reg_test.pdf",
            stored_filename=f"reg_{uuid.uuid4().hex[:6]}.pdf",
            local_path="/tmp/non_existent_reg_test.pdf",
            file_type="pdf",
            file_size=512
        )
        session.add(res)

        exp = CandidateExperience(
            id=str(uuid.uuid4()),
            candidate_id=cand_id,
            resume_id=res_id,
            company="RegCo",
            designation="Developer"
        )
        session.add(exp)

        sk_obj = Skill(id=str(uuid.uuid4()), name=f"RegSkill_{uuid.uuid4().hex[:4]}")
        session.add(sk_obj)
        await session.flush()

        c_sk = CandidateSkill(id=str(uuid.uuid4()), candidate_id=cand_id, skill_id=sk_obj.id)
        session.add(c_sk)

        req = (await session.execute(select(Requirement))).scalars().first()
        if req:
            match = MatchResult(id=str(uuid.uuid4()), candidate_id=cand_id, requirement_id=req.id, overall_score=90.0)
            session.add(match)

        await session.commit()

        # Call delete_candidate endpoint logic
        response = await delete_candidate(cand_id, session)

        assert response["status"] == "success"
        assert response["candidate_id"] == cand_id

        # Verify candidate is gone
        stmt_cand = select(Candidate).where(Candidate.id == cand_id)
        cand_check = (await session.execute(stmt_cand)).scalar_one_or_none()
        assert cand_check is None

        # Verify related records are gone
        stmt_exp = select(CandidateExperience).where(CandidateExperience.candidate_id == cand_id)
        assert len((await session.execute(stmt_exp)).scalars().all()) == 0

        stmt_sk = select(CandidateSkill).where(CandidateSkill.candidate_id == cand_id)
        assert len((await session.execute(stmt_sk)).scalars().all()) == 0

        stmt_res = select(Resume).where(Resume.candidate_id == cand_id)
        assert len((await session.execute(stmt_res)).scalars().all()) == 0

        stmt_match = select(MatchResult).where(MatchResult.candidate_id == cand_id)
        assert len((await session.execute(stmt_match)).scalars().all()) == 0
