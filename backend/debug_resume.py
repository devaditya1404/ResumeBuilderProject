#!/usr/bin/env python3
"""
debug_resume.py — CLI tool for debugging the resume parsing pipeline.

Usage:
    python debug_resume.py /path/to/resume.pdf
    python debug_resume.py /path/to/resume.docx --verbose

Outputs a detailed table of extracted fields with timing breakdown.
"""
import asyncio
import os
import sys
import json

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.parsers.resume_parser import parse_resume


def print_header(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_field(label: str, value, max_len: int = 80):
    if value is None:
        display = "NULL"
    elif isinstance(value, str) and len(value) > max_len:
        display = value[:max_len] + "..."
    elif isinstance(value, list):
        display = ", ".join(str(v) for v in value[:10])
        if len(value) > 10:
            display += f" ... (+{len(value) - 10} more)"
    else:
        display = str(value)
    print(f"  {label:.<35} {display}")


async def debug_parse(file_path: str, verbose: bool = False):
    """Run the full parse pipeline and print detailed results."""

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    print_header(f"PARSING: {os.path.basename(file_path)}")
    print(f"  File size: {os.path.getsize(file_path):,} bytes")
    print(f"  File type: {os.path.splitext(file_path)[1]}")

    # Run the pipeline
    result = await parse_resume(file_path)

    # ── Status ──
    print_header("PARSE STATUS")
    print_field("Success", "✅ YES" if result.success else "❌ NO")
    print_field("Extraction method", result.extraction_method)
    print_field("OCR used", result.ocr_used)
    print_field("Text quality score", f"{result.text_quality_score:.2f}")
    print_field("LLM model", result.llm_model)

    if result.errors:
        print_header("ERRORS")
        for err in result.errors:
            print(f"  ❌ {err}")

    if result.warnings:
        print_header("WARNINGS")
        for warn in result.warnings[:10]:
            print(f"  ⚠️  {warn}")

    if not result.extraction:
        print("\n❌ No extraction data available.")
        return

    ext = result.extraction

    # ── Identity ──
    print_header("IDENTITY")
    print_field("Full Name", ext.full_name)
    print_field("Current Title", ext.current_title)
    print_field("Summary", ext.summary)

    # ── Contact ──
    print_header("CONTACT (Deterministic + LLM)")
    print_field("Email", ext.email)
    print_field("Phone", ext.phone)
    print_field("LinkedIn", ext.linkedin_url)
    print_field("GitHub", ext.github_url)
    print_field("Portfolio", ext.portfolio_url)
    print_field("Location", ext.location)

    # ── Professional ──
    print_header("PROFESSIONAL")
    print_field("Current Employer", result.current_employer)
    print_field("Current Title", result.current_title)
    print_field("Total Exp (months)", result.total_experience_months)
    print_field("Total Exp (years)", f"{result.total_experience_months / 12:.1f}" if result.total_experience_months else "NULL")
    print_field("Notice Period", ext.notice_period)
    print_field("Current CTC", ext.current_ctc)
    print_field("Expected CTC", ext.expected_ctc)

    # ── Skills ──
    print_header(f"SKILLS ({len(ext.skills)})")
    if ext.skills:
        for i, skill in enumerate(ext.skills):
            print(f"  [{i+1:2d}] {skill}")

    # ── Experience ──
    print_header(f"EXPERIENCE ({len(ext.experiences)})")
    for i, exp in enumerate(ext.experiences):
        print(f"\n  [{i+1}] {exp.company or 'N/A'}")
        print_field("    Title", exp.title)
        print_field("    Period", f"{exp.start_date or '?'} → {exp.end_date or '?'}")
        print_field("    Location", exp.location)
        print_field("    Client", exp.client)
        if exp.description and verbose:
            print_field("    Description", exp.description)

    # ── Education ──
    print_header(f"EDUCATION ({len(ext.education)})")
    for i, edu in enumerate(ext.education):
        print(f"\n  [{i+1}] {edu.institution or 'N/A'}")
        print_field("    Degree", edu.degree)
        print_field("    Field", edu.field_of_study)
        print_field("    Period", f"{edu.start_year or '?'} → {edu.end_year or '?'}")

    # ── Certifications ──
    if ext.certifications:
        print_header(f"CERTIFICATIONS ({len(ext.certifications)})")
        for cert in ext.certifications:
            print(f"  • {cert.name} ({cert.issuer or 'N/A'})")

    # ── Projects ──
    if ext.projects:
        print_header(f"PROJECTS ({len(ext.projects)})")
        for proj in ext.projects:
            print(f"  • {proj.name}")
            if proj.technologies:
                print(f"    Tech: {proj.technologies}")

    # ── Languages ──
    if ext.languages:
        print_header(f"LANGUAGES ({len(ext.languages)})")
        for lang in ext.languages:
            print(f"  • {lang}")

    # ── Sections Found ──
    print_header("SECTIONS DETECTED")
    print(f"  {', '.join(result.sections_found) if result.sections_found else 'None'}")

    # ── Timings ──
    print_header("TIMING BREAKDOWN")
    t = result.timings
    print_field("Text extraction", f"{t.extraction_ms:.0f}ms")
    if t.ocr_ms > 0:
        print_field("OCR fallback", f"{t.ocr_ms:.0f}ms")
    print_field("Contact regex", f"{t.contact_ms:.0f}ms")
    print_field("Section detection", f"{t.section_ms:.0f}ms")
    print_field("Name extraction", f"{t.name_ms:.0f}ms")
    print_field("LLM extraction", f"{t.llm_ms:.0f}ms")
    print_field("Grounding validation", f"{t.grounding_ms:.0f}ms")
    print_field("Experience calc", f"{t.experience_ms:.0f}ms")
    print_field("TOTAL", f"{t.total_ms:.0f}ms")

    # ── Verbose: raw text ──
    if verbose:
        print_header("RAW TEXT (first 2000 chars)")
        print(result.raw_text[:2000])

    print(f"\n{'='*70}")
    print(f"  ✅ Debug complete")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_resume.py <resume_path> [--verbose]")
        sys.exit(1)

    file_path = sys.argv[1]
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    asyncio.run(debug_parse(file_path, verbose))
