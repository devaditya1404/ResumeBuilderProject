"""
Fallback Deterministic Section Extractor for TalentVault.

Enriches ResumeExtraction when LLM is unavailable or when LLM omits sections.
Extracts:
1. Skills (via regex & known skill keywords)
2. Education (degree & university patterns)
3. Experience (company & designation from experience section lines)
4. Languages (English, Japanese, JLPT levels N1-N5, etc.)
"""
import re
from typing import List, Optional
from app.ai.extraction_schemas import (
    ResumeExtraction,
    ExtractedExperience,
    ExtractedEducation,
)
from app.parsers.skill_normalizer import normalize_skills

COMMON_TECH_SKILLS = [
    "Python", "FastAPI", "React", "React.js", "TypeScript", "JavaScript", "Docker", "SQL",
    "PostgreSQL", "SQLite", "MongoDB", "PyTorch", "TensorFlow", "LLMs", "LLM", "REST APIs",
    "REST API", "Git", "AWS", "GCP", "Azure", "Kubernetes", "Node.js", "Express", "C++",
    "Java", "C#", "Go", "Golang", "Rust", "HTML", "CSS", "TailwindCSS", "Redux", "GraphQL",
    "FAISS", "Vector DB", "Pandas", "NumPy", "Scikit-Learn", "OpenCV", "Machine Learning",
    "Deep Learning", "Artificial Intelligence", "NLP", "CI/CD", "Linux", "Bash"
]

LANGUAGES_PATTERN = re.compile(
    r"\b(Japanese(?:\s*\([^)]+\))?|JLPT\s*N[1-5](?:\s*Certified)?|English(?:\s*\([^)]+\))?|Spanish|French|German|Hindi|Mandarin|Chinese)\b",
    re.IGNORECASE
)

DEGREE_PATTERN = re.compile(
    r"\b(B\.?Tech[^\n,]*|M\.?Tech[^\n,]*|B\.?S\.?[^\n,]*|M\.?S\.?[^\n,]*|B\.?A\.?[^\n,]*|M\.?A\.?[^\n,]*|Ph\.?D\.?[^\n,]*|Bachelor[^\n,]*|Master[^\n,]*|Associate[^\n,]*)\b",
    re.IGNORECASE
)

INSTITUTION_PATTERN = re.compile(
    r"\b([A-Z][A-Za-z0-9\s&,.'-]{2,40}(?:University|College|Institute|School|Academy|Politecnico))\b",
    re.IGNORECASE
)


def enrich_extraction_with_fallbacks(
    resume_text: str,
    extraction: ResumeExtraction,
) -> ResumeExtraction:
    """
    Enrich an existing ResumeExtraction object with fallback extracted values
    for any missing fields (skills, education, experience, languages).
    """
    if not extraction:
        extraction = ResumeExtraction()

    # 1. Languages / JLPT
    found_langs = list(set(m.strip() for m in LANGUAGES_PATTERN.findall(resume_text)))
    if found_langs:
        if not extraction.languages:
            extraction.languages = found_langs
        else:
            for lang in found_langs:
                if lang not in extraction.languages:
                    extraction.languages.append(lang)

    # 2. Skills
    if not extraction.skills:
        extracted_skills = []
        for skill in COMMON_TECH_SKILLS:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, resume_text, re.IGNORECASE):
                extracted_skills.append(skill)
        if extracted_skills:
            extraction.skills = normalize_skills(extracted_skills)

    # 3. Education
    if not extraction.education:
        degrees = DEGREE_PATTERN.findall(resume_text)
        institutions = INSTITUTION_PATTERN.findall(resume_text)
        if degrees or institutions:
            edu_item = ExtractedEducation(
                institution=institutions[0].strip() if institutions else None,
                degree=degrees[0].strip() if degrees else None,
            )
            extraction.education = [edu_item]

    # 4. Experiences (if missing)
    if not extraction.experiences:
        # Heuristic line search for "Company - Title" or "Title at Company"
        exp_lines = re.findall(
            r"([A-Z][A-Za-z0-9\s&.-]{2,40})\s*[-–—|@]\s*([A-Z][A-Za-z0-9\s&.-]{2,40})",
            resume_text
        )
        exps = []
        for p1, p2 in exp_lines[:5]:
            p1_str, p2_str = p1.strip(), p2.strip()
            if any(w in p1_str.lower() for w in ["engineer", "developer", "manager", "lead", "specialist", "intern", "consultant", "director"]):
                title, company = p1_str, p2_str
            else:
                company, title = p1_str, p2_str
            exps.append(ExtractedExperience(company=company, title=title))
        if exps:
            extraction.experiences = exps

    return extraction
