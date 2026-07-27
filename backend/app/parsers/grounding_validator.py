"""
Grounding validator: cross-checks LLM-extracted data against the original resume text.

Prevents hallucination by rejecting LLM output that cannot be found in the source.
"""
import re
from typing import List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class GroundingIssue:
    field: str
    llm_value: str
    severity: str  # "WARNING" | "REJECT"
    reason: str


@dataclass
class GroundingResult:
    is_valid: bool = True
    issues: List[GroundingIssue] = field(default_factory=list)
    rejected_fields: List[str] = field(default_factory=list)

    def add_issue(self, field: str, llm_value: str, severity: str, reason: str):
        issue = GroundingIssue(field=field, llm_value=llm_value, severity=severity, reason=reason)
        self.issues.append(issue)
        if severity == "REJECT":
            self.rejected_fields.append(field)
            self.is_valid = False


def validate_grounding(
    llm_output: dict,
    resume_text: str,
    regex_contacts: dict,
) -> GroundingResult:
    """
    Cross-check LLM-extracted fields against original resume text.

    Rules:
    - Email: must exist in resume text (exact match) or match regex extraction
    - Phone: must exist in resume text or match regex extraction
    - LinkedIn/GitHub URLs: must exist in resume text or match regex extraction
    - Skills: each skill should appear in resume text (fuzzy match allowed)
    - Company names: should appear in resume text
    """
    result = GroundingResult()
    text_lower = resume_text.lower()

    # ── Contact grounding ──
    _validate_contact(result, "email", llm_output.get("email"), text_lower, regex_contacts.get("email"))
    _validate_contact(result, "phone", llm_output.get("phone"), text_lower, regex_contacts.get("phone"))
    _validate_contact(result, "linkedin_url", llm_output.get("linkedin_url"), text_lower, regex_contacts.get("linkedin_url"))
    _validate_contact(result, "github_url", llm_output.get("github_url"), text_lower, regex_contacts.get("github_url"))

    # ── Skills grounding ──
    skills = llm_output.get("skills", [])
    if isinstance(skills, list):
        for skill in skills:
            if isinstance(skill, str) and skill.strip():
                _validate_text_presence(result, f"skill:{skill}", skill, text_lower, severity="WARNING")

    # ── Experience company grounding ──
    experiences = llm_output.get("experiences", [])
    if isinstance(experiences, list):
        for exp in experiences:
            if isinstance(exp, dict):
                company = exp.get("company")
                if company:
                    _validate_text_presence(result, f"company:{company}", company, text_lower, severity="WARNING")

    return result


def _validate_contact(
    result: GroundingResult,
    field: str,
    llm_value: Optional[str],
    text_lower: str,
    regex_value: Optional[str],
):
    """
    Validate a contact field. Prefer regex extraction over LLM extraction.
    If LLM gives a value not in the text and not matching regex, reject it.
    """
    if not llm_value:
        return

    llm_lower = llm_value.lower().strip()

    # Check if it exists in the resume text
    if llm_lower in text_lower:
        return  # Grounded

    # Check if it matches the regex extraction
    if regex_value and llm_lower == regex_value.lower().strip():
        return  # Matches deterministic extraction

    # Not grounded — reject contact info from LLM
    result.add_issue(
        field=field,
        llm_value=llm_value,
        severity="REJECT",
        reason=f"LLM-extracted {field} not found in resume text and doesn't match regex extraction",
    )


def _validate_text_presence(
    result: GroundingResult,
    field: str,
    value: str,
    text_lower: str,
    severity: str = "WARNING",
):
    """Check if a value appears in the resume text (case-insensitive, fuzzy)."""
    if not value:
        return

    value_lower = value.lower().strip()

    # Exact substring match
    if value_lower in text_lower:
        return

    # Try matching individual words (for multi-word values)
    words = value_lower.split()
    if len(words) > 1:
        # If most words appear individually, consider it grounded
        found = sum(1 for w in words if w in text_lower)
        if found >= len(words) * 0.7:
            return

    result.add_issue(
        field=field,
        llm_value=value,
        severity=severity,
        reason=f"'{value}' not found in resume text",
    )
