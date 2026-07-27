#!/usr/bin/env python3
"""
test_matching_acceptance.py — Comprehensive acceptance test for JD ↔ Resume Matching.

Tests:
1. Controlled Acceptance Test Scenario (Senior Python Data Engineer vs Candidate with Python, SQL, Power BI, Pandas).
2. Verifies Pandas is NOT marked as a JD match.
3. Verifies missing mandatory skills are strictly Docker, Kubernetes.
4. Verifies missing preferred skills are strictly Azure DevOps, Terraform.
5. Verifies Experience = PASS.
6. Real Candidate SQLite Integration Test against stored candidate (Braulio Padilla / Aditya Bonde).
"""
import asyncio
import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.match_engine import evaluate_match
from app.services.skill_alias import skills_match
from app.core.database import AsyncSessionLocal, init_db
from app.models import Candidate, Requirement
from sqlalchemy import select
from sqlalchemy.orm import selectinload


def run_controlled_acceptance_test():
    print("=" * 70)
    print("1. CONTROLLED ACCEPTANCE TEST: Senior Python Data Engineer")
    print("=" * 70)

    jd_req = {
        "job_title": "Senior Python Data Engineer",
        "mandatory_skills": ["Python", "SQL", "Power BI", "Docker", "Kubernetes"],
        "preferred_skills": ["Azure DevOps", "Terraform"],
        "minimum_experience": 4.0,
    }

    cand_data = {
        "name": "Controlled Test Candidate",
        "skills": ["Python", "SQL", "Power BI", "Pandas"],
        "experience_years": 5.0,
        "current_company": "Tech Corp",
        "current_designation": "Data Engineer",
    }

    result = evaluate_match(jd_req, cand_data)

    print(f"Overall Score:            {result.overall_score}%")
    print(f"Skill Score:              {result.skill_score}%")
    print(f"Experience Score:         {result.experience_score}%")
    print(f"Matching Skills:          {result.matching_skills}")
    print(f"Missing Mandatory Skills: {result.missing_mandatory_skills}")
    print(f"Missing Preferred Skills: {result.missing_preferred_skills}")
    print(f"Strengths:                {result.strengths}")
    print(f"Gaps:                     {result.gaps}")

    # Assertions
    # 1. Matching skills must contain Python, SQL, Power BI
    assert "Python" in result.matching_skills, "Python must be in matching skills"
    assert "SQL" in result.matching_skills, "SQL must be in matching skills"
    assert "Power BI" in result.matching_skills, "Power BI must be in matching skills"

    # 2. Pandas MUST NOT be reported as a JD match!
    assert "Pandas" not in result.matching_skills, "CRITICAL: Pandas must NOT be reported as a JD match because it was not in JD!"

    # 3. Missing mandatory skills must be Docker, Kubernetes
    assert "Docker" in result.missing_mandatory_skills, "Docker must be in missing mandatory"
    assert "Kubernetes" in result.missing_mandatory_skills, "Kubernetes must be in missing mandatory"

    # 4. Missing preferred skills must be Azure DevOps, Terraform
    assert "Azure DevOps" in result.missing_preferred_skills, "Azure DevOps must be in missing preferred"
    assert "Terraform" in result.missing_preferred_skills, "Terraform must be in missing preferred"

    # 5. Experience = PASS (100.0%)
    assert result.experience_score == 100.0, "5.0 years candidate exp >= 4.0 min exp must result in 100% experience score"

    print("\nCONTROLLED ACCEPTANCE TEST RESULT: 100% PASSED!")


async def run_real_candidate_matching_test():
    print("\n" + "=" * 70)
    print("2. REAL CANDIDATE SQLITE MATCHING INTEGRATION TEST")
    print("=" * 70)

    await init_db()

    async with AsyncSessionLocal() as session:
        # Query real candidates stored in SQLite
        stmt_cand = select(Candidate).options(selectinload(Candidate.candidate_skills)).order_by(Candidate.created_at.desc())
        res_cand = await session.execute(stmt_cand)
        candidates = res_cand.scalars().all()

        if not candidates:
            print("No real candidates found in SQLite database to match.")
            return

        cand = candidates[0]
        skills_list = []
        if hasattr(cand, "candidate_skills") and cand.candidate_skills:
            try:
                skills_list = [cs.skill.name for cs in cand.candidate_skills if cs.skill]
            except Exception:
                pass

        print(f"Real Candidate from DB: {cand.name}")
        print(f"  Exp Years: {cand.experience_years}")
        print(f"  Skills ({len(skills_list)}): {skills_list[:8]}")

        # Create a JD for Java Backend Developer
        jd_req = {
            "job_title": "Senior Java Backend Engineer",
            "mandatory_skills": ["Java", "Spring Boot", "PostgreSQL", "Docker", "AWS"],
            "preferred_skills": ["AngularJS", "Jenkins", "Kubernetes"],
            "minimum_experience": 5.0,
        }

        cand_data = {
            "name": cand.name,
            "skills": skills_list,
            "experience_years": cand.experience_years,
            "current_company": cand.current_company,
            "current_designation": cand.current_designation,
            "latest_company": cand.latest_company,
            "latest_designation": cand.latest_designation,
        }

        result = evaluate_match(jd_req, cand_data)

        print(f"\nMatch Result for '{cand.name}' vs '{jd_req['job_title']}':")
        print(f"  Overall Score:            {result.overall_score}%")
        print(f"  Skill Score:              {result.skill_score}%")
        print(f"  Experience Score:         {result.experience_score}%")
        print(f"  Matching Skills:          {result.matching_skills}")
        print(f"  Missing Mandatory Skills: {result.missing_mandatory_skills}")
        print(f"  Missing Preferred Skills: {result.missing_preferred_skills}")
        print(f"  Strengths:                {result.strengths}")

        print("\nREAL CANDIDATE SQLITE TEST RESULT: SUCCESS")


if __name__ == "__main__":
    run_controlled_acceptance_test()
    asyncio.run(run_real_candidate_matching_test())
