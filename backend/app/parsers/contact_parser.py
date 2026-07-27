"""
Deterministic contact information extraction using regex.

This runs BEFORE the LLM call. Extracted contacts are passed to the LLM as hints
and also used to ground-check LLM output.

Extracts: email, phone, LinkedIn URL, GitHub URL, portfolio URL.
"""
import re
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ContactInfo:
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    all_emails: List[str] = None
    all_phones: List[str] = None
    all_urls: List[str] = None

    def __post_init__(self):
        if self.all_emails is None:
            self.all_emails = []
        if self.all_phones is None:
            self.all_phones = []
        if self.all_urls is None:
            self.all_urls = []


# ── Email ──────────────────────────────────────────────────────────
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

# ── Phone ──────────────────────────────────────────────────────────
PHONE_PATTERN = re.compile(
    r"(?:"
    r"\+?\d{1,3}[\s\-.]?"  # country code
    r")?"
    r"(?:\(?\d{2,4}\)?[\s\-.]?)?"  # area code
    r"\d{3,5}[\s\-.]?\d{3,5}"  # main number
    r"(?:\s*(?:ext|x|extension)\.?\s*\d{1,5})?",  # extension
    re.IGNORECASE,
)

# ── LinkedIn ──────────────────────────────────────────────────────
LINKEDIN_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+/?",
    re.IGNORECASE,
)

# ── GitHub ────────────────────────────────────────────────────────
GITHUB_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[\w\-]+/?",
    re.IGNORECASE,
)

# ── General URL ──────────────────────────────────────────────────
URL_PATTERN = re.compile(
    r"https?://[^\s<>\"'\)\]]+",
    re.IGNORECASE,
)

# Known non-portfolio domains to exclude
_EXCLUDE_DOMAINS = {
    "linkedin.com",
    "github.com",
    "twitter.com",
    "facebook.com",
    "instagram.com",
    "youtube.com",
    "medium.com",
    "stackoverflow.com",
    "fonts.googleapis.com",
    "cdn.",
    "w3.org",
    "schemas.microsoft.com",
}


def extract_contacts(text: str) -> ContactInfo:
    """
    Extract all contact information from resume text using regex.
    Returns the best candidate for each field, plus all matches found.
    """
    if not text or not text.strip():
        return ContactInfo()

    # ── Emails ──
    raw_emails = EMAIL_PATTERN.findall(text)
    # Filter out common false positives
    emails = [
        e
        for e in raw_emails
        if not e.endswith((".png", ".jpg", ".gif", ".svg", ".css", ".js"))
        and "@" in e
        and len(e) > 5
    ]

    # ── Phones ──
    raw_phones = PHONE_PATTERN.findall(text)
    phones = _filter_phones(raw_phones, text)

    # ── LinkedIn ──
    linkedin_matches = LINKEDIN_PATTERN.findall(text)

    # ── GitHub ──
    github_matches = GITHUB_PATTERN.findall(text)

    # ── All URLs ──
    all_urls = URL_PATTERN.findall(text)

    # ── Portfolio URL: first URL that isn't LinkedIn/GitHub/social ──
    portfolio = _find_portfolio_url(all_urls)

    return ContactInfo(
        email=emails[0] if emails else None,
        phone=phones[0] if phones else None,
        linkedin_url=linkedin_matches[0] if linkedin_matches else None,
        github_url=github_matches[0] if github_matches else None,
        portfolio_url=portfolio,
        all_emails=emails,
        all_phones=phones,
        all_urls=all_urls,
    )


def _filter_phones(raw_phones: List[str], text: str) -> List[str]:
    """
    Filter out false positive phone matches (dates, zip codes, IDs).
    A valid phone should have at least 7 digits.
    """
    phones = []
    for phone in raw_phones:
        # Strip whitespace
        phone = phone.strip()

        # Count only digits
        digits = re.sub(r"\D", "", phone)

        # Phone numbers should have 7-15 digits
        if len(digits) < 7 or len(digits) > 15:
            continue

        # Skip if it looks like a date (e.g. 2020-01-15)
        if re.match(r"^\d{4}[\-/]\d{2}[\-/]\d{2}$", phone.strip()):
            continue

        # Skip if it looks like a year range (2018 - 2022)
        if re.match(r"^\d{4}\s*[\-–]\s*\d{4}$", phone.strip()):
            continue

        phones.append(phone)

    return phones


def _find_portfolio_url(urls: List[str]) -> Optional[str]:
    """Find the first URL that looks like a personal portfolio."""
    for url in urls:
        url_lower = url.lower()
        is_excluded = any(domain in url_lower for domain in _EXCLUDE_DOMAINS)
        if not is_excluded:
            return url
    return None
