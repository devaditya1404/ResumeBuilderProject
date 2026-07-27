"""
Safe candidate name extraction with blacklist validation.

The name is typically the first prominent text in a resume.
This module applies strict safety checks to prevent common parser errors
like extracting "PROFESSIONAL SUMMARY" as a name.
"""
import re
from typing import Optional, List

# ── Name blacklist: these strings MUST NEVER be accepted as names ──
NAME_BLACKLIST = {
    # Common section headings that appear at the top
    "resume", "cv", "curriculum vitae",
    "professional summary", "professionalsummary",
    "executive summary", "career summary",
    "summary", "profile", "about me", "about",
    "objective", "career objective", "professional objective",
    "professional profile",
    # Section headings
    "experience", "work experience", "professional experience",
    "education", "skills", "technical skills",
    "certifications", "projects", "references",
    "contact", "contact information", "contact details",
    "personal information", "personal details",
    # Common false positives
    "page", "confidential", "private",
    "updated", "last updated", "date",
}

# Words that should never appear in a person's name
NAME_WORD_BLACKLIST = {
    "resume", "cv", "summary", "experience", "education",
    "skills", "certifications", "projects", "references",
    "contact", "objective", "profile", "page", "confidential",
    "professional", "technical", "career", "personal",
    "information", "details", "updated", "date",
}


def extract_name_from_text(text: str) -> Optional[str]:
    """
    Extract candidate name from the top of the resume text.
    Uses heuristics: name is typically the first non-empty line
    that passes all safety checks.
    """
    if not text:
        return None

    lines = text.split("\n")
    candidates: List[str] = []

    for line in lines[:20]:  # Only look at the first 20 lines
        cleaned = line.strip()

        # Skip empty lines
        if not cleaned:
            continue

        # Skip page markers
        if cleaned.startswith("[PAGE"):
            continue

        # Skip lines that are clearly contact info
        if "@" in cleaned or "http" in cleaned.lower():
            continue
        if re.match(r"^[\+\d\(\)\-\s\.]{7,}$", cleaned):
            continue

        # Skip very long lines (names are usually short)
        if len(cleaned) > 50:
            continue

        # Skip lines with too many words (names are 2-4 words)
        words = cleaned.split()
        if len(words) > 5 or len(words) < 1:
            continue

        candidates.append(cleaned)

    # Try each candidate through validation
    for candidate in candidates:
        validated = validate_name(candidate)
        if validated:
            return validated

    return None


def validate_name(name: str) -> Optional[str]:
    """
    Validate and clean a candidate name.
    Returns the cleaned name or None if it fails validation.
    """
    if not name:
        return None

    # Clean the name
    cleaned = name.strip()
    cleaned = re.sub(r"[,|:;]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Remove trailing/leading special characters
    cleaned = re.sub(r"^[\-–—•*#>]+\s*", "", cleaned)
    cleaned = re.sub(r"\s*[\-–—•*#>]+$", "", cleaned)

    if not cleaned:
        return None

    # Check against full-string blacklist
    if cleaned.lower() in NAME_BLACKLIST:
        return None

    # Check if any blacklisted word appears in the name
    name_words = set(cleaned.lower().split())
    if name_words & NAME_WORD_BLACKLIST:
        return None

    # Must contain at least one letter
    if not re.search(r"[a-zA-Z]", cleaned):
        return None

    # Must have at least 2 characters
    if len(cleaned) < 2:
        return None

    # Must not be all uppercase and match a known heading pattern
    if cleaned.isupper() and len(cleaned.split()) <= 2:
        # Allow all-caps names, but only if they're short and not a heading
        if cleaned.lower() in NAME_BLACKLIST:
            return None

    # Title-case the name
    # Handle names like "ADITYA BONDE" -> "Aditya Bonde"
    parts = cleaned.split()
    formatted_parts = []
    for part in parts:
        if part.isupper() and len(part) > 1:
            formatted_parts.append(part.capitalize())
        else:
            formatted_parts.append(part)

    return " ".join(formatted_parts)
