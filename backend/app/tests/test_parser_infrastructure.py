"""
Unit tests for resume parser infrastructure:
1. Current vs Latest company logic (historical vs active positions)
2. Atomic skill normalization (category prefix stripping, splitting, trimming)
"""
import pytest
from app.parsers.experience_calculator import (
    determine_current_employer,
    determine_latest_employer,
)
from app.parsers.skill_normalizer import normalize_skills


def test_historical_latest_job():
    """Historical job (ended 2025) should have current_company = None and latest_company set."""
    experiences = [
        {
            "company": "Rubixe.com",
            "title": "Data Science Consultant Intern",
            "start_date": "Jul-2024",
            "end_date": "Jan-2025",
        },
        {
            "company": "AICTE and EDUNET",
            "title": "AI internship",
            "start_date": "Aug-2023",
            "end_date": "Oct-2023",
        },
    ]

    curr_comp, curr_title = determine_current_employer(experiences)
    latest_comp, latest_title = determine_latest_employer(experiences)

    assert curr_comp is None, "Current company must be None for ended historical roles"
    assert curr_title is None, "Current title must be None for ended historical roles"
    assert latest_comp == "Rubixe.com", "Latest company must be Rubixe.com"
    assert latest_title == "Data Science Consultant Intern"


def test_active_ongoing_job():
    """Active job (end_date = Present) should populate both current and latest company."""
    experiences = [
        {
            "company": "Tech Corp",
            "title": "Senior Engineer",
            "start_date": "Jan-2024",
            "end_date": "Present",
        },
        {
            "company": "Old Startup",
            "title": "Junior Dev",
            "start_date": "Jan-2021",
            "end_date": "Dec-2023",
        },
    ]

    curr_comp, curr_title = determine_current_employer(experiences)
    latest_comp, latest_title = determine_latest_employer(experiences)

    assert curr_comp == "Tech Corp", "Current company should be Tech Corp"
    assert curr_title == "Senior Engineer"
    assert latest_comp == "Tech Corp"
    assert latest_title == "Senior Engineer"


def test_atomic_skill_normalization():
    """Test stripping category prefixes, splitting, and removing proficiency levels."""
    raw_skills = [
        "Programming Languages: C, Python",
        "Data Analytics Tools: Tableau, Power BI, Microsoft Excel (Intermediate)",
        "Python Libraries: Pandas, NumPy, Matplotlib, Seaborn, Scikit-learn",
        "Databases and SQL: MySQL Database Management, Data Retrieval & Manipulation",
        "Web Technologies: HTML, CSS, JavaScript,React.js",
        "Development Environments: Jupyter Notebook, Google Collab",
    ]

    normalized = normalize_skills(raw_skills)

    # Verify category prefixes removed & atomic skills extracted
    assert "C" in normalized
    assert "Python" in normalized
    assert "Tableau" in normalized
    assert "Power BI" in normalized
    assert "Microsoft Excel" in normalized
    assert "Pandas" in normalized
    assert "NumPy" in normalized
    assert "MySQL Database Management" in normalized
    assert "HTML" in normalized
    assert "CSS" in normalized
    assert "JavaScript" in normalized
    assert "React.js" in normalized
    assert "Jupyter Notebook" in normalized

    # Ensure no category prefixes remain as skills
    for s in normalized:
        assert not s.startswith("Programming Languages:")
        assert not s.startswith("Data Analytics Tools:")
        assert "(Intermediate)" not in s


def test_date_block_counting():
    """Test generic date block counting for completeness hint."""
    from app.ai.resume_extractor import count_probable_date_blocks

    sample_text = """
    Job A: Jan 2020 - Dec 2022
    Job B: June 2018 - Dec 2019
    Short Job C: Jan 2016 - Mar 2016
    """
    count = count_probable_date_blocks(sample_text)
    assert count == 3, f"Expected 3 date blocks, got {count}"


def test_language_null_normalization():
    """Test that compact.lang = None maps to canonical languages = []."""
    from app.ai.extraction_schemas import CompactResumeExtraction, compact_to_canonical

    compact = CompactResumeExtraction(n="Test User", lang=None)
    canonical = compact_to_canonical(compact)
    assert canonical.languages == []


def test_education_semantic_separation():
    """Test generic separation of degree vs institution in education."""
    from app.ai.extraction_schemas import CompactResumeExtraction, CompactEducation, compact_to_canonical

    compact = CompactResumeExtraction(
        edu=[CompactEducation(i="Computer Science Civil Engineer . State Technical University .")]
    )
    canonical = compact_to_canonical(compact)
    assert len(canonical.education) == 1
    assert "University" in canonical.education[0].institution
    assert "Civil Engineer" in canonical.education[0].degree


def test_nosql_skill_normalization():
    """Test NO SQL -> NoSQL variant normalization."""
    from app.parsers.skill_normalizer import normalize_skills

    raw = ["NO SQL", "Java", "REACTJS"]
    norm = normalize_skills(raw)
    assert "NoSQL" in norm
    assert "NO SQL" not in norm
    assert "React.js" in norm
