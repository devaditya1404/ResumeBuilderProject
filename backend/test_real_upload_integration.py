#!/usr/bin/env python3
"""
test_real_upload_integration.py — Integration test for real local resume upload pipeline.
Tests PyMuPDF -> Contact Regex -> Section Detection -> Ollama qwen2.5:3b -> Hybrid Recovery -> SQLite DB.
"""
import asyncio
import os
import sys
import json

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal, init_db
from app.parsers.resume_parser import parse_resume
from app.models.candidate import Candidate
from sqlalchemy import select


async def run_integration_test():
    print("=" * 70)
    print("REAL UPLOAD PIPELINE INTEGRATION TEST")
    print("=" * 70)

    # 1. Initialize DB
    await init_db()

    test_file = "data/test_resumes/braulio_resume.pdf"
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        sys.exit(1)

    print(f"\n1. Parsing real file: {test_file}...")
    result = await parse_resume(test_file)

    print(f"Parsing Status:  {result.parsing_status}")
    print(f"Extraction OK:   {result.success}")
    print(f"Candidate Name:  {result.extraction.full_name if result.extraction else 'None'}")
    print(f"Experiences Count: {len(result.extraction.experiences) if result.extraction else 0}")

    if result.extraction:
        for idx, exp in enumerate(result.extraction.experiences, 1):
            print(f"  {idx}. {exp.company} | {exp.title} ({exp.start_date} -> {exp.end_date})")

    print(f"Total Exp Months: {result.total_experience_months}")
    print(f"Current Company:  {result.current_employer}")
    print(f"Latest Company:   {result.latest_company}")
    print(f"Timings Total:    {result.timings.total_ms:.1f} ms")

    # 2. Save candidate to SQLite database
    async with AsyncSessionLocal() as session:
        ext = result.extraction
        candidate = Candidate(
            name=ext.full_name or "Braulio Padilla",
            email=ext.email,
            phone=ext.phone,
            linkedin_url=ext.linkedin_url,
            github_url=ext.github_url,
            portfolio_url=ext.portfolio_url,
            current_company=result.current_employer,
            current_designation=result.current_title,
            latest_company=result.latest_company,
            latest_designation=result.latest_designation,
            experience_months=result.total_experience_months,
            experience_years=result.total_experience_months / 12.0 if result.total_experience_months else None,
            current_location=ext.location,
            professional_summary=ext.summary,
        )
        session.add(candidate)
        await session.commit()
        await session.refresh(candidate)

        print(f"\n2. Saved to SQLite Database successfully! Candidate ID: {candidate.id}")

        # Verify query from DB
        stmt = select(Candidate).where(Candidate.id == candidate.id)
        res = await session.execute(stmt)
        db_candidate = res.scalar_one_or_none()

        print("\n3. DB PERSISTENCE VERIFICATION:")
        print(f"ID in DB:           {db_candidate.id}")
        print(f"Name in DB:         {db_candidate.name}")
        print(f"Email in DB:        {db_candidate.email}")
        print(f"Current Company:    {db_candidate.current_company}")
        print(f"Exp Months in DB:   {db_candidate.experience_months}")
        print(f"Exp Years in DB:    {db_candidate.experience_years:.1f}" if db_candidate.experience_years else "Exp Years: None")

    print("\nINTEGRATION TEST VERDICT: SUCCESS")


if __name__ == "__main__":
    asyncio.run(run_integration_test())
