"""
OCR fallback for scanned PDFs using Tesseract + pdf2image.

Only called when primary extraction quality is below threshold.
Requires system-level `tesseract` and `poppler` to be installed.
"""
import time
import shutil
import logging
from typing import List, Tuple
from app.parsers.pdf_parser import ExtractionResult

logger = logging.getLogger(__name__)


def is_tesseract_available() -> bool:
    """Check if tesseract binary exists on PATH."""
    return shutil.which("tesseract") is not None


def extract_text_with_ocr(file_path: str) -> ExtractionResult:
    """
    Extract text from a scanned PDF using Tesseract OCR.
    Falls back gracefully if dependencies are missing.
    """
    start = time.time()

    if not is_tesseract_available():
        elapsed = (time.time() - start) * 1000
        return ExtractionResult(
            text="",
            page_count=0,
            extraction_method="ocr",
            ocr_used=True,
            quality_score=0.0,
            quality_issues=["TESSERACT_NOT_INSTALLED"],
            extraction_time_ms=elapsed,
        )

    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError as e:
        elapsed = (time.time() - start) * 1000
        return ExtractionResult(
            text="",
            page_count=0,
            extraction_method="ocr",
            ocr_used=True,
            quality_score=0.0,
            quality_issues=[f"OCR_IMPORT_FAILED: {str(e)}"],
            extraction_time_ms=elapsed,
        )

    try:
        images = convert_from_path(file_path, dpi=300)
        pages_text: List[str] = []

        for page_idx, image in enumerate(images):
            page_text = pytesseract.image_to_string(image, lang="eng")
            if page_text.strip():
                pages_text.append(f"[PAGE {page_idx + 1}]\n{page_text.strip()}")

        full_text = "\n\n".join(pages_text)
        elapsed = (time.time() - start) * 1000

        quality_score, quality_issues = _assess_ocr_quality(full_text)
        lines = [l for l in full_text.split("\n") if l.strip()]

        return ExtractionResult(
            text=full_text,
            page_count=len(images),
            extraction_method="ocr",
            ocr_used=True,
            quality_score=quality_score,
            quality_issues=quality_issues,
            extraction_time_ms=elapsed,
            line_count=len(lines),
            char_count=len(full_text),
        )

    except Exception as e:
        elapsed = (time.time() - start) * 1000
        logger.error(f"OCR extraction failed: {e}")
        return ExtractionResult(
            text="",
            page_count=0,
            extraction_method="ocr",
            ocr_used=True,
            quality_score=0.0,
            quality_issues=[f"OCR_EXTRACTION_FAILED: {str(e)}"],
            extraction_time_ms=elapsed,
        )


def _assess_ocr_quality(text: str) -> Tuple[float, List[str]]:
    """Assess OCR extraction quality."""
    issues: List[str] = []

    if not text or not text.strip():
        return 0.0, ["OCR_TEXT_EMPTY"]

    lines = [l for l in text.split("\n") if l.strip()]
    if len(lines) < 5:
        issues.append("OCR_TOO_FEW_LINES")

    score = 0.8  # OCR starts lower baseline
    if "OCR_TOO_FEW_LINES" in issues:
        score -= 0.3

    return max(0.0, score), issues
