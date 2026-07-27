#!/usr/bin/env python3
"""
test_controlled_three_candidates.py — Controlled 3-candidate verification test.

Tests:
JD: Senior Python Data Engineer (Required: Python, SQL, Power BI, Docker, Kubernetes; Min Exp: 4 years)
Candidate A: 5 years, [Python, SQL, Power BI, Docker, Kubernetes]
Candidate B: 5 years, [Python, SQL]
Candidate C: 2 years, [Java, Spring Boot]

Verifies:
1. Candidate A score > Candidate B score > Candidate C score
2. Candidate A score != Candidate B score and Candidate B score != Candidate C score
3. Candidate A matching skills = [Python, SQL, Power BI, Docker, Kubernetes], missing = []
4. Candidate B matching skills = [Python, SQL], missing = [Power BI, Docker, Kubernetes]
5. Candidate C matching skills = [], missing = [Python, SQL, Power BI, Docker, Kubernetes]
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.match_engine import evaluate_match


def run_controlled_three_candidates_test():
    print("=" * 75)
    print("CONTROLLED 3-CANDIDATE MATCH VERIFICATION TEST")
    print("=" * 75)

    jd_req = {
        "job_title": "Senior Python Data Engineer",
        "mandatory_skills": ["Python", "SQL", "Power BI", "Docker", "Kubernetes"],
        "preferred_skills": [],
        "minimum_experience": 4.0,
    }

    cand_a = {
        "name": "Candidate A (Perfect Match)",
        "skills": ["Python", "SQL", "Power BI", "Docker", "Kubernetes"],
        "experience_years": 5.0,
        "current_designation": "Senior Python Data Engineer",
    }

    cand_b = {
        "name": "Candidate B (Partial Match)",
        "skills": ["Python", "SQL"],
        "experience_years": 5.0,
        "current_designation": "Data Engineer",
    }

    cand_c = {
        "name": "Candidate C (Zero Skill Match)",
        "skills": ["Java", "Spring Boot"],
        "experience_years": 2.0,
        "current_designation": "Junior Java Developer",
    }

    match_a = evaluate_match(jd_req, cand_a)
    match_b = evaluate_match(jd_req, cand_b)
    match_c = evaluate_match(jd_req, cand_c)

    print(f"\n[CANDIDATE A]")
    print(f"  Overall Score: {match_a.overall_score}%")
    print(f"  Skill Score:   {match_a.skill_score}%")
    print(f"  Exp Score:     {match_a.experience_score}%")
    print(f"  Role Score:    {match_a.role_score}%")
    print(f"  Matched:       {match_a.matching_skills}")
    print(f"  Missing:       {match_a.missing_mandatory_skills}")

    print(f"\n[CANDIDATE B]")
    print(f"  Overall Score: {match_b.overall_score}%")
    print(f"  Skill Score:   {match_b.skill_score}%")
    print(f"  Exp Score:     {match_b.experience_score}%")
    print(f"  Role Score:    {match_b.role_score}%")
    print(f"  Matched:       {match_b.matching_skills}")
    print(f"  Missing:       {match_b.missing_mandatory_skills}")

    print(f"\n[CANDIDATE C]")
    print(f"  Overall Score: {match_c.overall_score}%")
    print(f"  Skill Score:   {match_c.skill_score}%")
    print(f"  Exp Score:     {match_c.experience_score}%")
    print(f"  Role Score:    {match_c.role_score}%")
    print(f"  Matched:       {match_c.matching_skills}")
    print(f"  Missing:       {match_c.missing_mandatory_skills}")

    # ASSERTIONS
    assert match_a.overall_score > match_b.overall_score, f"Candidate A ({match_a.overall_score}%) must score higher than Candidate B ({match_b.overall_score}%)"
    assert match_b.overall_score > match_c.overall_score, f"Candidate B ({match_b.overall_score}%) must score higher than Candidate C ({match_c.overall_score}%)"
    assert match_a.overall_score != match_b.overall_score, "Score A and Score B must not be equal!"
    assert match_b.overall_score != match_c.overall_score, "Score B and Score C must not be equal!"

    # Skill match assertions
    assert len(match_a.matching_skills) == 5, "Candidate A must match all 5 JD skills"
    assert len(match_a.missing_mandatory_skills) == 0, "Candidate A must have 0 missing mandatory skills"

    assert len(match_b.matching_skills) == 2, "Candidate B must match exactly 2 JD skills"
    assert set(match_b.missing_mandatory_skills) == {"Power BI", "Docker", "Kubernetes"}, "Candidate B missing skills mismatch"

    assert len(match_c.matching_skills) == 0, "Candidate C must match 0 JD skills"
    assert len(match_c.missing_mandatory_skills) == 5, "Candidate C must miss all 5 JD skills"

    print("\n" + "=" * 75)
    print("ASSERTIONS VERIFIED: Candidate A Score > Candidate B Score > Candidate C Score!")
    print("CONTROLLED TEST RESULT: 100% PASSED")
    print("=" * 75)


if __name__ == "__main__":
    run_controlled_three_candidates_test()
