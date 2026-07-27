#!/usr/bin/env python3
"""
test_controlled_skill_tests.py — Controlled skill normalization tests (Step 9).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.match_engine import evaluate_match
from app.services.skill_alias import skills_match, extract_atomic_skills


def run_controlled_skill_tests():
    print("=" * 75)
    print("STEP 9 — CONTROLLED SKILL NORMALIZATION TESTS")
    print("=" * 75)

    # TEST A: Excel vs Microsoft Excel
    jd_a = {"job_title": "Data Analyst", "mandatory_skills": ["Excel", "Power BI", "SQL"]}
    cand_a = {"name": "Candidate A", "skills": extract_atomic_skills("Microsoft Excel, SQL, Tableau")}
    res_a = evaluate_match(jd_a, cand_a)
    
    print("\nTEST A (Excel vs Microsoft Excel):")
    print(f"  Candidate Skills: {cand_a['skills']}")
    print(f"  Matched: {res_a.matching_skills}")
    print(f"  Missing: {res_a.missing_mandatory_skills}")
    print(f"  Skill Score: {res_a.skill_score}%")
    assert "Excel" in res_a.matching_skills, "TEST A FAIL: Excel must match Microsoft Excel"
    assert "SQL" in res_a.matching_skills, "TEST A FAIL: SQL must match SQL"
    assert "Power BI" in res_a.missing_mandatory_skills, "TEST A FAIL: Power BI must be missing"
    assert res_a.skill_score > 0, "TEST A FAIL: Skill score must be > 0"
    print("  RESULT: PASS")

    # TEST B: Java vs JavaScript
    jd_b = {"job_title": "Backend Dev", "mandatory_skills": ["Java"]}
    cand_b = {"name": "Candidate B", "skills": ["JavaScript"]}
    res_b = evaluate_match(jd_b, cand_b)

    print("\nTEST B (Java vs JavaScript):")
    print(f"  Matched: {res_b.matching_skills}")
    print(f"  Missing: {res_b.missing_mandatory_skills}")
    assert "Java" not in res_b.matching_skills, "TEST B FAIL: Java must NOT match JavaScript"
    assert "Java" in res_b.missing_mandatory_skills, "TEST B FAIL: Java must be in missing"
    print("  RESULT: PASS")

    # TEST C: Power BI vs PowerBI
    jd_c = {"job_title": "BI Dev", "mandatory_skills": ["Power BI"]}
    cand_c = {"name": "Candidate C", "skills": ["PowerBI"]}
    res_c = evaluate_match(jd_c, cand_c)

    print("\nTEST C (Power BI vs PowerBI):")
    print(f"  Matched: {res_c.matching_skills}")
    print(f"  Missing: {res_c.missing_mandatory_skills}")
    assert "Power BI" in res_c.matching_skills, "TEST C FAIL: Power BI must match PowerBI"
    assert len(res_c.missing_mandatory_skills) == 0, "TEST C FAIL: Missing must be empty"
    print("  RESULT: PASS")

    print("\n" + "=" * 75)
    print("ALL CONTROLLED SKILL TESTS PASSED 100%!")
    print("=" * 75)


if __name__ == "__main__":
    run_controlled_skill_tests()
