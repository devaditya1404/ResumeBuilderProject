"""
Pydantic schemas for structured LLM resume extraction output.

Includes:
1. Compact internal transport schemas (JSON key aliasing for fast, token-efficient LLM responses).
2. Canonical domain models (ResumeExtraction) used across database, API, and frontend.
3. Converter function compact_to_canonical() that bridges the two seamlessly.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Any


def _coerce_str(v: Any) -> Optional[str]:
    """Safely coerce int, float, or raw string values into Optional[str]."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        cleaned = v.strip()
        if not cleaned or cleaned.lower() in ("null", "none", "undefined", "n/a"):
            return None
        return cleaned
    return str(v)


# ── COMPACT TRANSPORT SCHEMAS (LLM -> Python) ───────────────────────

class CompactExperience(BaseModel):
    c: Optional[str] = None   # company
    r: Optional[str] = None   # designation / role
    s: Optional[str] = None   # start_date (YYYY-MM or YYYY)
    e: Optional[str] = None   # end_date (YYYY-MM or YYYY or Present)
    cl: List[str] = Field(default_factory=list)  # clients

    @field_validator("c", "r", "s", "e", mode="before")
    @classmethod
    def coerce_strings(cls, v: Any) -> Optional[str]:
        return _coerce_str(v)


class CompactEducation(BaseModel):
    i: Optional[str] = None   # institution
    d: Optional[str] = None   # degree
    f: Optional[str] = None   # field of study

    @field_validator("i", "d", "f", mode="before")
    @classmethod
    def coerce_strings(cls, v: Any) -> Optional[str]:
        return _coerce_str(v)


class CompactProject(BaseModel):
    n: Optional[str] = None   # name
    t: List[str] = Field(default_factory=list)  # technologies

    @field_validator("n", mode="before")
    @classmethod
    def coerce_strings(cls, v: Any) -> Optional[str]:
        return _coerce_str(v)


class CompactResumeExtraction(BaseModel):
    n: Optional[str] = None       # full name
    loc: Optional[str] = None     # location
    exp: List[CompactExperience] = Field(default_factory=list)
    edu: List[CompactEducation] = Field(default_factory=list)
    cert: List[str] = Field(default_factory=list)
    pr: List[CompactProject] = Field(default_factory=list)
    lang: List[str] = Field(default_factory=list)
    sk: List[str] = Field(default_factory=list)  # SKILLS LAST!

    @field_validator("n", "loc", mode="before")
    @classmethod
    def coerce_strings(cls, v: Any) -> Optional[str]:
        return _coerce_str(v)

    @field_validator("sk", "cert", "lang", mode="before")
    @classmethod
    def coerce_string_lists(cls, v: Any) -> List[str]:
        if not v:
            return []
        if isinstance(v, str):
            return [v.strip()]
        if isinstance(v, list):
            res = []
            for item in v:
                c = _coerce_str(item)
                if c:
                    res.append(c)
            return res
        return []


# ── CANONICAL DOMAIN MODELS (Python -> DB / API / Frontend) ─────────

class ExtractedExperience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    client: Optional[str] = None


class ExtractedEducation(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None
    gpa: Optional[str] = None


class ExtractedCertification(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    date: Optional[str] = None
    credential_id: Optional[str] = None


class ExtractedProject(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[str] = None
    url: Optional[str] = None


class ResumeExtraction(BaseModel):
    full_name: Optional[str] = None
    current_title: Optional[str] = None
    summary: Optional[str] = None

    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None

    location: Optional[str] = None

    current_employer: Optional[str] = None
    total_experience_years: Optional[float] = None
    notice_period: Optional[str] = None
    current_ctc: Optional[str] = None
    expected_ctc: Optional[str] = None

    skills: List[str] = Field(default_factory=list)
    experiences: List[ExtractedExperience] = Field(default_factory=list)
    education: List[ExtractedEducation] = Field(default_factory=list)
    certifications: List[ExtractedCertification] = Field(default_factory=list)
    projects: List[ExtractedProject] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)


# ── CONVERTER: COMPACT TRANSPORT -> CANONICAL MODEL ──────────────────

def compact_to_canonical(compact: CompactResumeExtraction) -> ResumeExtraction:
    """Convert compact LLM extraction transport format into full canonical ResumeExtraction model."""
    experiences = [
        ExtractedExperience(
            company=e.c,
            title=e.r,
            start_date=e.s,
            end_date=e.e,
            client=", ".join(e.cl) if e.cl else None,
        )
        for e in compact.exp
        if e.c or e.r
    ]

    education = []
    for ed in compact.edu:
        if not ed.i and not ed.d:
            continue
        
        inst = ed.i
        deg = ed.d
        field = ed.f

        # Generic separation: If institution contains a university keyword alongside degree text
        if inst and not deg:
            parts = [p.strip() for p in inst.replace(".", ",").split(",") if p.strip()]
            univ_part = None
            deg_part = None
            for p in parts:
                p_lower = p.lower()
                if any(w in p_lower for w in ["university", "college", "institute", "school", "universidad", "politecnico"]):
                    univ_part = p
                else:
                    deg_part = p
            if univ_part and deg_part:
                inst = univ_part
                deg = deg_part

        education.append(ExtractedEducation(institution=inst, degree=deg, field_of_study=field))

    certifications = [
        ExtractedCertification(name=cert_name)
        for cert_name in compact.cert
        if cert_name
    ]

    projects = [
        ExtractedProject(
            name=p.n,
            technologies=", ".join(p.t) if p.t else None,
        )
        for p in compact.pr
        if p.n
    ]

    languages = compact.lang if isinstance(compact.lang, list) else []

    return ResumeExtraction(
        full_name=compact.n,
        location=compact.loc,
        skills=compact.sk or [],
        experiences=experiences,
        education=education,
        certifications=certifications,
        projects=projects,
        languages=languages,
    )
