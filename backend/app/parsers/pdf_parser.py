"""
PDF text extraction using PyMuPDF (fitz).

Preserves page boundaries, line boundaries, and text block structure.
Does NOT blindly concatenate spans. Evaluates extraction quality
and reports whether OCR fallback is recommended.
"""
import time
import fitz  # PyMuPDF
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class ExtractionResult:
    text: str
    page_count: int
    extraction_method: str  # "pymupdf" | "docx" | "ocr"
    ocr_used: bool = False
    quality_score: float = 0.0  # 0.0 - 1.0
    quality_issues: List[str] = field(default_factory=list)
    extraction_time_ms: float = 0.0
    line_count: int = 0
    char_count: int = 0


def extract_text_from_pdf(file_path: str) -> ExtractionResult:
    """
    Extract text from a PDF using PyMuPDF with block/line structure preservation.
    Returns an ExtractionResult with quality assessment.
    """
    start = time.time()
    pages_text: List[str] = []
    total_pages = 0

    try:
        doc = fitz.open(file_path)
        total_pages = len(doc)

        for page_idx, page in enumerate(doc):
            page_lines: List[str] = []
            page_lines.append(f"[PAGE {page_idx + 1}]")

            # Extract text blocks preserving structure
            blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

            for block in blocks:
                if block.get("type") != 0:  # Skip image blocks
                    continue

                block_lines: List[str] = []
                for line in block.get("lines", []):
                    spans_text = []
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text:
                            spans_text.append(text)

                    if spans_text:
                        # Join spans within a line with space, not concatenation
                        line_text = " ".join(spans_text)
                        block_lines.append(line_text)

                if block_lines:
                    page_lines.append("\n".join(block_lines))

            pages_text.append("\n\n".join(page_lines))
        doc.close()

    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return ExtractionResult(
            text="",
            page_count=total_pages,
            extraction_method="pymupdf",
            quality_score=0.0,
            quality_issues=[f"PDF_EXTRACTION_FAILED: {str(e)}"],
            extraction_time_ms=elapsed,
        )

    full_text = "\n\n".join(pages_text)
    elapsed = (time.time() - start) * 1000

    # Assess quality
    quality_score, quality_issues = _assess_extraction_quality(full_text)

    lines = [l for l in full_text.split("\n") if l.strip()]

    return ExtractionResult(
        text=full_text,
        page_count=total_pages,
        extraction_method="pymupdf",
        ocr_used=False,
        quality_score=quality_score,
        quality_issues=quality_issues,
        extraction_time_ms=elapsed,
        line_count=len(lines),
        char_count=len(full_text),
    )


def _assess_extraction_quality(text: str) -> Tuple[float, List[str]]:
    """
    Evaluate whether extracted text is meaningful or garbage.
    Returns (score 0.0-1.0, list of issues).
    """
    issues: List[str] = []

    if not text or not text.strip():
        return 0.0, ["TEXT_EMPTY"]

    stripped = text.strip()
    lines = [l for l in stripped.split("\n") if l.strip()]
    meaningful_lines = [l for l in lines if len(l.strip()) > 3]

    # Check: enough meaningful lines
    if len(meaningful_lines) < 5:
        issues.append("TOO_FEW_MEANINGFUL_LINES")

    # Check: alphanumeric ratio
    alnum_count = sum(1 for c in stripped if c.isalnum())
    total_count = len(stripped)
    alnum_ratio = alnum_count / total_count if total_count > 0 else 0

    if alnum_ratio < 0.3:
        issues.append("LOW_ALPHANUMERIC_RATIO")

    # Check: suspicious repeated characters (garbled text)
    if stripped.count("�") > 5 or stripped.count("\ufffd") > 5:
        issues.append("GARBLED_CHARACTERS")

    # Check: very short total content
    if len(stripped) < 100:
        issues.append("VERY_SHORT_CONTENT")

    # Calculate quality score
    score = 1.0
    if "TEXT_EMPTY" in issues:
        score = 0.0
    elif "TOO_FEW_MEANINGFUL_LINES" in issues:
        score -= 0.3
    if "LOW_ALPHANUMERIC_RATIO" in issues:
        score -= 0.3
    if "GARBLED_CHARACTERS" in issues:
        score -= 0.2
    if "VERY_SHORT_CONTENT" in issues:
        score -= 0.2

    return max(0.0, min(1.0, score)), issues
