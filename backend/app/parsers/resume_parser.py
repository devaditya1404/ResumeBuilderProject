"""
Resume Parser Orchestrator.

Ties all parser modules into a single pipeline:
1. Text extraction (PDF/DOCX/OCR)
2. Deterministic contact extraction
3. Section detection
4. Name extraction
5. LLM structured extraction
6. Grounding validation
7. Experience calculation
8. Return final structured result
"""
import os
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from app.parsers.pdf_parser import extract_text_from_pdf, ExtractionResult
from app.parsers.docx_parser import extract_text_from_docx
from app.parsers.ocr_parser import extract_text_with_ocr, is_tesseract_available
from app.parsers.contact_parser import extract_contacts, ContactInfo
from app.parsers.section_detector import detect_sections
from app.parsers.name_extractor import extract_name_from_text, validate_name
from app.parsers.experience_calculator import (
    parse_date_range,
    calculate_total_experience_months,
    determine_current_employer,
    determine_latest_employer,
    DateRange,
)
from app.parsers.skill_normalizer import normalize_skills
from app.parsers.grounding_validator import validate_grounding
from app.ai.resume_extractor import extract_resume_with_llm
from app.ai.extraction_schemas import ResumeExtraction

logger = logging.getLogger(__name__)

# Quality threshold below which OCR is attempted
OCR_QUALITY_THRESHOLD = 0.5


@dataclass
class ParseTimings:
    """Detailed timing breakdown for profiling."""
    extraction_ms: float = 0.0
    ocr_ms: float = 0.0
    contact_ms: float = 0.0
    section_ms: float = 0.0
    name_ms: float = 0.0
    llm_ms: float = 0.0
    grounding_ms: float = 0.0
    experience_ms: float = 0.0
    total_ms: float = 0.0


@dataclass
class ParseResult:
    """Complete result of parsing a resume."""
    success: bool = False
    parsing_status: str = "FAILED"  # "PARSED" | "PARTIAL" | "FAILED"
    extraction: Optional[ResumeExtraction] = None
    # Metadata
    extraction_method: str = ""  # "pymupdf" | "docx" | "ocr"
    ocr_used: bool = False
    llm_model: Optional[str] = None
    # Calculated fields (None when experience was not parsed)
    total_experience_months: Optional[int] = None
    current_employer: Optional[str] = None
    current_title: Optional[str] = None
    latest_company: Optional[str] = None
    latest_designation: Optional[str] = None
    # Contact (deterministic)
    contacts: Optional[ContactInfo] = None
    # Sections detected
    sections_found: List[str] = field(default_factory=list)
    # Quality
    text_quality_score: float = 0.0
    grounding_issues: List[str] = field(default_factory=list)
    # Timings
    timings: ParseTimings = field(default_factory=ParseTimings)
    # Errors
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    # Raw text (for debug)
    raw_text: str = ""


async def parse_resume(file_path: str) -> ParseResult:
    """
    Main resume parsing pipeline.

    Args:
        file_path: Path to the uploaded resume file (PDF or DOCX)

    Returns:
        ParseResult with extraction data and metadata
    """
    result = ParseResult()
    pipeline_start = time.time()

    # ── 1. Determine file type ──
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in (".pdf", ".docx"):
        result.errors.append(f"UNSUPPORTED_FORMAT: {ext}")
        return result

    # ── 2. Text Extraction ──
    t0 = time.time()
    if ext == ".pdf":
        extraction = extract_text_from_pdf(file_path)
    else:
        extraction = extract_text_from_docx(file_path)

    result.timings.extraction_ms = (time.time() - t0) * 1000
    result.extraction_method = extraction.extraction_method
    result.text_quality_score = extraction.quality_score

    logger.info(
        f"Text extraction: method={extraction.extraction_method}, "
        f"quality={extraction.quality_score:.2f}, "
        f"chars={extraction.char_count}, lines={extraction.line_count}"
    )

    # ── 3. OCR Fallback (if poor quality) ──
    if ext == ".pdf" and extraction.quality_score < OCR_QUALITY_THRESHOLD:
        logger.info(f"Low quality ({extraction.quality_score:.2f}), attempting OCR fallback...")
        if is_tesseract_available():
            t0 = time.time()
            ocr_result = extract_text_with_ocr(file_path)
            result.timings.ocr_ms = (time.time() - t0) * 1000

            if ocr_result.quality_score > extraction.quality_score:
                extraction = ocr_result
                result.extraction_method = "ocr"
                result.ocr_used = True
                result.text_quality_score = ocr_result.quality_score
                logger.info(f"OCR improved quality to {ocr_result.quality_score:.2f}")
            else:
                result.warnings.append("OCR_DID_NOT_IMPROVE_QUALITY")
        else:
            result.warnings.append("TESSERACT_NOT_AVAILABLE")

    if not extraction.text or not extraction.text.strip():
        result.errors.append("NO_TEXT_EXTRACTED")
        return result

    result.raw_text = extraction.text

    # ── 4. Deterministic Contact Extraction ──
    t0 = time.time()
    contacts = extract_contacts(extraction.text)
    result.timings.contact_ms = (time.time() - t0) * 1000
    result.contacts = contacts

    logger.info(
        f"Contacts: email={contacts.email}, phone={contacts.phone}, "
        f"linkedin={contacts.linkedin_url is not None}"
    )

    # ── 5. Section Detection ──
    t0 = time.time()
    sections = detect_sections(extraction.text)
    result.timings.section_ms = (time.time() - t0) * 1000
    result.sections_found = [s.canonical_name for s in sections]

    logger.info(f"Sections found: {result.sections_found}")

    # ── 6. Name Extraction (deterministic, before LLM) ──
    t0 = time.time()
    deterministic_name = extract_name_from_text(extraction.text)
    result.timings.name_ms = (time.time() - t0) * 1000

    logger.info(f"Deterministic name: {deterministic_name}")

    # ── 7. LLM Structured Extraction ──
    t0 = time.time()
    section_hints = [s.canonical_name for s in sections]
    llm_extraction, llm_metadata = await extract_resume_with_llm(
        resume_text=extraction.text,
        contacts=contacts,
        section_hints=section_hints,
    )
    result.timings.llm_ms = (time.time() - t0) * 1000
    result.llm_model = llm_metadata.get("model")

    if llm_metadata.get("error"):
        error_msg = llm_metadata["error"]
        result.errors.append(f"LLM_ERROR: {error_msg}")
        if "TIMEOUT" in error_msg.upper():
            result.warnings.append("OLLAMA_TIMEOUT")
        elif "OLLAMA" in error_msg.upper():
            result.warnings.append("OLLAMA_UNAVAILABLE")
        logger.error(f"LLM extraction failed: {error_msg}")
        # Continue with whatever we have deterministically
        llm_extraction = ResumeExtraction()
        result.parsing_status = "PARTIAL"
    else:
        result.parsing_status = "PARSED"

    result.extraction = llm_extraction

    # ── 8. Override LLM contacts with deterministic contacts ──
    if contacts.email and (not llm_extraction.email or llm_extraction.email != contacts.email):
        llm_extraction.email = contacts.email
    if contacts.phone and not llm_extraction.phone:
        llm_extraction.phone = contacts.phone
    if contacts.linkedin_url and not llm_extraction.linkedin_url:
        llm_extraction.linkedin_url = contacts.linkedin_url
    if contacts.github_url and not llm_extraction.github_url:
        llm_extraction.github_url = contacts.github_url
    if contacts.portfolio_url and not llm_extraction.portfolio_url:
        llm_extraction.portfolio_url = contacts.portfolio_url

    # ── 9. Override LLM name with deterministic name if safer ──
    if deterministic_name:
        llm_name = llm_extraction.full_name
        if not llm_name or validate_name(llm_name) is None:
            llm_extraction.full_name = deterministic_name
        else:
            # Use deterministic name if LLM name looks suspicious
            validated_llm = validate_name(llm_name)
            if validated_llm:
                llm_extraction.full_name = validated_llm
            else:
                llm_extraction.full_name = deterministic_name

    # ── 10. Grounding Validation ──
    t0 = time.time()
    grounding = validate_grounding(
        llm_output=llm_extraction.model_dump(),
        resume_text=extraction.text,
        regex_contacts={
            "email": contacts.email,
            "phone": contacts.phone,
            "linkedin_url": contacts.linkedin_url,
            "github_url": contacts.github_url,
        },
    )
    result.timings.grounding_ms = (time.time() - t0) * 1000

    for issue in grounding.issues:
        msg = f"{issue.severity}: {issue.field} = '{issue.llm_value}' — {issue.reason}"
        if issue.severity == "REJECT":
            result.warnings.append(msg)
            # Null out rejected fields
            if issue.field == "email":
                llm_extraction.email = contacts.email  # fallback to regex
            elif issue.field == "phone":
                llm_extraction.phone = contacts.phone
            elif issue.field == "linkedin_url":
                llm_extraction.linkedin_url = contacts.linkedin_url
            elif issue.field == "github_url":
                llm_extraction.github_url = contacts.github_url
        else:
            result.warnings.append(msg)

    result.grounding_issues = [str(i) for i in grounding.issues]

    # ── 11. Normalize Skills & Recover Missing Employment ──
    if llm_extraction:
        if llm_extraction.skills:
            llm_extraction.skills = normalize_skills(llm_extraction.skills)
        from app.parsers.employment_recoverer import recover_missing_employment
        llm_extraction.experiences = await recover_missing_employment(extraction.text, llm_extraction.experiences)

    # ── 12. Experience Calculation ──
    t0 = time.time()
    if llm_extraction and llm_extraction.experiences:
        date_ranges: List[DateRange] = []
        for exp in llm_extraction.experiences:
            dr = parse_date_range(exp.start_date or "", exp.end_date or "")
            date_ranges.append(dr)

        result.total_experience_months = calculate_total_experience_months(date_ranges)

        # Determine current (ongoing only) vs latest (chronologically most recent) employer
        exp_dicts = [e.model_dump() for e in llm_extraction.experiences]
        curr_employer, curr_title = determine_current_employer(exp_dicts)
        latest_employer, latest_title = determine_latest_employer(exp_dicts)

        result.current_employer = curr_employer
        result.current_title = curr_title
        result.latest_company = latest_employer
        result.latest_designation = latest_title
    else:
        result.current_employer = None
        result.current_title = None

    result.timings.experience_ms = (time.time() - t0) * 1000

    # ── 12. Final result ──
    result.timings.total_ms = (time.time() - pipeline_start) * 1000
    result.success = True

    logger.info(
        f"Parse complete: name={llm_extraction.full_name}, "
        f"skills={len(llm_extraction.skills)}, "
        f"experience={len(llm_extraction.experiences)}, "
        f"total_months={result.total_experience_months}, "
        f"total_time={result.timings.total_ms:.0f}ms"
    )

    return result
