"""
Resume section heading detection and normalization.

Identifies common resume section headings and categorizes them.
Used to help the LLM extraction and to segment the resume text.
"""
import re
from typing import List, Optional, Tuple
from dataclasses import dataclass


# ── Canonical section names and their common variants ──────────────
SECTION_MAP = {
    "SUMMARY": [
        "summary", "professional summary", "executive summary", "profile",
        "professional profile", "career summary", "about me", "about",
        "objective", "career objective", "professional objective",
    ],
    "EXPERIENCE": [
        "experience", "work experience", "professional experience",
        "employment history", "work history", "employment",
        "career history", "relevant experience",
    ],
    "EDUCATION": [
        "education", "educational background", "academic background",
        "academic qualifications", "qualifications", "academic details",
    ],
    "SKILLS": [
        "skills", "technical skills", "core skills", "key skills",
        "competencies", "core competencies", "technical competencies",
        "tools & technologies", "tools and technologies", "technologies",
        "programming languages", "proficiencies",
    ],
    "CERTIFICATIONS": [
        "certifications", "certificates", "professional certifications",
        "licenses", "licenses & certifications", "credentials",
        "accreditations",
    ],
    "PROJECTS": [
        "projects", "personal projects", "key projects",
        "notable projects", "academic projects", "side projects",
    ],
    "PUBLICATIONS": [
        "publications", "research", "papers", "research publications",
    ],
    "AWARDS": [
        "awards", "honors", "achievements", "honors & awards",
        "awards & recognition",
    ],
    "LANGUAGES": [
        "languages", "language skills", "language proficiency",
    ],
    "INTERESTS": [
        "interests", "hobbies", "hobbies & interests",
    ],
    "REFERENCES": [
        "references",
    ],
}

# Build a reverse lookup: variant -> canonical name
_VARIANT_TO_CANONICAL = {}
for canonical, variants in SECTION_MAP.items():
    for variant in variants:
        _VARIANT_TO_CANONICAL[variant.lower()] = canonical


@dataclass
class SectionBoundary:
    canonical_name: str
    original_heading: str
    start_line: int
    end_line: Optional[int] = None  # Set when next section is found


def detect_sections(text: str) -> List[SectionBoundary]:
    """
    Detect resume section headings in extracted text.
    Returns a list of SectionBoundary objects ordered by appearance.
    """
    if not text:
        return []

    lines = text.split("\n")
    sections: List[SectionBoundary] = []

    for line_idx, line in enumerate(lines):
        cleaned = _clean_heading(line)
        if not cleaned:
            continue

        canonical = _match_section_heading(cleaned)
        if canonical:
            sections.append(
                SectionBoundary(
                    canonical_name=canonical,
                    original_heading=line.strip(),
                    start_line=line_idx,
                )
            )

    # Set end_line for each section (up to the next section's start)
    for i in range(len(sections)):
        if i + 1 < len(sections):
            sections[i].end_line = sections[i + 1].start_line - 1
        else:
            sections[i].end_line = len(lines) - 1

    return sections


def _clean_heading(line: str) -> str:
    """
    Clean and normalize a potential heading line.
    Strips markdown-like markers, colons, pipes, and extra whitespace.
    """
    text = line.strip()

    # Remove common heading markers
    text = re.sub(r"^[#*\-=_|>•]+\s*", "", text)
    text = re.sub(r"\s*[:\-|]+\s*$", "", text)

    # Remove trailing colons
    text = text.rstrip(":")

    return text.strip()


def _match_section_heading(cleaned_text: str) -> Optional[str]:
    """
    Match a cleaned line against known section headings.
    Returns the canonical section name or None.
    """
    # Must be short enough to be a heading (not a full sentence)
    if len(cleaned_text) > 60:
        return None

    # Must not contain too many words (headings are usually 1-4 words)
    words = cleaned_text.split()
    if len(words) > 5:
        return None

    # Exact match against known variants
    lower = cleaned_text.lower()
    if lower in _VARIANT_TO_CANONICAL:
        return _VARIANT_TO_CANONICAL[lower]

    return None


def get_section_text(text: str, sections: List[SectionBoundary], section_name: str) -> Optional[str]:
    """
    Extract the text content of a specific section.
    """
    lines = text.split("\n")
    for section in sections:
        if section.canonical_name == section_name:
            start = section.start_line + 1  # Skip the heading itself
            end = section.end_line + 1 if section.end_line is not None else len(lines)
            return "\n".join(lines[start:end]).strip()
    return None
