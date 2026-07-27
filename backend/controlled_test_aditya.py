#!/usr/bin/env python3
"""
controlled_test_aditya.py — Single controlled baseline extraction for aditya_resume.pdf.
Runs ONLY the parser pipeline: PDF -> Contacts -> Sections -> Ollama qwen2.5:3b -> Validation.
No database, no API server, no frontend.
"""
import asyncio
import os
import sys
import json
import time

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.parsers.pdf_parser import extract_text_from_pdf
from app.parsers.contact_parser import extract_contacts
from app.parsers.section_detector import detect_sections
from app.parsers.name_extractor import extract_name_from_text
from app.parsers.experience_calculator import (
    parse_date_range,
    calculate_total_experience_months,
    determine_current_employer,
)
from app.parsers.grounding_validator import validate_grounding
from app.ai.resume_extractor import extract_resume_with_llm
from app.ai.extraction_schemas import ResumeExtraction


async def run_test():
    file_path = "data/test_resumes/aditya_resume.pdf"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)

    print("=" * 70)
    print("CONTROLLED TEST: aditya_resume.pdf")
    print("=" * 70)

    # 1. Text extraction
    t0 = time.time()
    pdf_res = extract_text_from_pdf(file_path)
    extraction_ms = (time.time() - t0) * 1000

    # 2. Contacts
    t0 = time.time()
    contacts = extract_contacts(pdf_res.text)
    contact_ms = (time.time() - t0) * 1000

    # 3. Sections
    t0 = time.time()
    sections = detect_sections(pdf_res.text)
    section_ms = (time.time() - t0) * 1000
    section_hints = [s.canonical_name for s in sections]

    # 4. Name
    det_name = extract_name_from_text(pdf_res.text)

    # 5. Ollama extraction
    t0 = time.time()
    llm_extraction, metadata = await extract_resume_with_llm(
        resume_text=pdf_res.text,
        contacts=contacts,
        section_hints=section_hints,
    )
    llm_ms = (time.time() - t0) * 1000

    # 6. Override contacts and name
    if llm_extraction:
        llm_extraction.email = contacts.email
        llm_extraction.phone = contacts.phone
        llm_extraction.linkedin_url = contacts.linkedin_url
        if det_name and not llm_extraction.full_name:
            llm_extraction.full_name = det_name

    # 7. Grounding validation
    grounding_issues = []
    if llm_extraction:
        grounding = validate_grounding(
            llm_output=llm_extraction.model_dump(),
            resume_text=pdf_res.text,
            regex_contacts={
                "email": contacts.email,
                "phone": contacts.phone,
                "linkedin_url": contacts.linkedin_url,
            },
        )
        grounding_issues = [f"{i.field}: {i.llm_value} ({i.reason})" for i in grounding.issues]

    # 8. Experience calculation
    total_months = None
    curr_employer = None
    curr_title = None

    if llm_extraction and llm_extraction.experiences:
        date_ranges = [parse_date_range(e.start_date or "", e.end_date or "") for e in llm_extraction.experiences]
        total_months = calculate_total_experience_months(date_ranges)
        exp_dicts = [e.model_dump() for e in llm_extraction.experiences]
        curr_employer, curr_title = determine_current_employer(exp_dicts)

    print("\nRAW COMPACT JSON (from Ollama):")
    if metadata.get("compact_json"):
        print(json.dumps(metadata["compact_json"], indent=2))
    else:
        print("None / Raw text: " + str(metadata.get("raw_response")))

    print("\nCONVERTED CANONICAL RESULT:")
    if llm_extraction:
        print(json.dumps(llm_extraction.model_dump(), indent=2))
    else:
        print("LLM EXTRACTION FAILED")

    print("\nMETRICS & SPEED:")
    print(f"Model:                   {metadata.get('model')}")
    print(f"Input text chars:        {len(pdf_res.text)}")
    print(f"Output JSON chars:       {metadata.get('output_chars')}")
    print(f"Prompt eval tokens:      {metadata.get('prompt_eval_count')}")
    print(f"Generated tokens:        {metadata.get('eval_count')}")
    
    gen_duration_sec = (metadata.get('eval_duration_ms') or 0) / 1000
    tokens_per_sec = (metadata.get('eval_count') or 0) / gen_duration_sec if gen_duration_sec > 0 else 0
    print(f"Generation speed:        {tokens_per_sec:.2f} tokens/sec")

    print("\nTIMING BREAKDOWN:")
    print(f"PDF extraction:          {extraction_ms:.1f} ms")
    print(f"Contact regex:           {contact_ms:.1f} ms")
    print(f"Section detection:       {section_ms:.1f} ms")
    print(f"Client wall time:        {metadata.get('client_wall_time_ms'):.1f} ms")
    print(f"Ollama total duration:   {metadata.get('total_duration_ms'):.1f} ms")
    print(f"  - Load duration:       {metadata.get('load_duration_ms'):.1f} ms")
    print(f"  - Prompt eval duration:{metadata.get('prompt_eval_duration_ms'):.1f} ms")
    print(f"  - Generation duration: {metadata.get('eval_duration_ms'):.1f} ms")

    print("\nDERIVED CAREER INFO:")
    print(f"Calculated Total Exp:    {total_months} months ({total_months/12:.1f} years)" if total_months else "Calculated Total Exp:    NULL")
    print(f"Current Company:         {curr_employer}")
    print(f"Current Designation:     {curr_title}")
    print(f"Grounding Issues:        {grounding_issues if grounding_issues else 'NONE'}")
    print(f"Warnings:                {metadata.get('warnings')}")
    print(f"Error:                   {metadata.get('error')}")


if __name__ == "__main__":
    asyncio.run(run_test())
