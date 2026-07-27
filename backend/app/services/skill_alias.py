"""
Skill alias dictionary, atomic skill extraction, and safe matching engine.

Normalizes skills (case-insensitive, alias mapping, category prefix stripping, OCR cleanup)
while preserving strict distinctions:
- Java != JavaScript
- Spring != Spring Boot
- AWS != Azure
- Docker != Kubernetes
- SQL != PostgreSQL (unless generic SQL comparison)
"""
import re
from typing import List, Set, Optional

# Known alias dictionary (normalized lowercase -> Canonical display string)
SKILL_ALIASES = {
    "excel": "Excel",
    "ms excel": "Excel",
    "microsoft excel": "Excel",
    "excel functions": "Excel",
    "excel func*ons": "Excel",
    "advanced excel": "Excel",
    "excel advanced": "Excel",
    "microsoft excel intermediate": "Excel",
    "excel (intermediate)": "Excel",
    "powerbi": "Power BI",
    "power bi": "Power BI",
    "microsoft power bi": "Power BI",
    "tableau": "Tableau",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "psql": "PostgreSQL",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "springboot": "Spring Boot",
    "spring boot": "Spring Boot",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "aws": "Amazon Web Services",
    "amazon web services": "Amazon Web Services",
    "gcp": "Google Cloud Platform",
    "google cloud": "Google Cloud Platform",
    "google cloud platform": "Google Cloud Platform",
    "azure": "Microsoft Azure",
    "ms azure": "Microsoft Azure",
    "microsoft azure": "Microsoft Azure",
    "tf": "Terraform",
    "terraform": "Terraform",
    "react": "React.js",
    "reactjs": "React.js",
    "react.js": "React.js",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "nosql": "NoSQL",
    "no sql": "NoSQL",
    "py": "Python",
    "python": "Python",
    "sql": "SQL",
    "pivot table": "Pivot Tables",
    "pivot tables": "Pivot Tables",
    "pivot": "Pivot Tables",
    "vlookup": "VLOOKUP",
    "v look up": "VLOOKUP",
    "xlookup": "XLOOKUP",
    "power query": "Power Query",
}

# Strict distinct pairs that must NEVER match
DISTINCT_PAIRS = {
    ("java", "javascript"),
    ("javascript", "java"),
    ("spring", "spring boot"),
    ("spring boot", "spring"),
    ("aws", "azure"),
    ("azure", "aws"),
    ("docker", "kubernetes"),
    ("kubernetes", "docker"),
}


def clean_ocr_and_annotations(skill_str: str) -> str:
    """Clean OCR artifacts (e.g. asterisks) and trailing parenthetical annotations."""
    if not skill_str:
        return ""
    # Fix OCR asterisk artifacts (e.g. Func*ons -> Functions)
    cleaned = skill_str.replace("*", "t").replace("Func*ons", "Functions").replace("Repor*ng", "Reporting").replace("Visualiza*on", "Visualization")
    # Remove parenthetical details like (Intermediate), (Advanced), (Basic)
    cleaned = re.sub(r'\s*\((?:beginner|intermediate|advanced|basic|expert|\d+\s*yrs?)\)', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def extract_atomic_skills(raw_skill_input: str) -> List[str]:
    """
    Split category prefixes and composite skill entries into atomic comparable skills.
    Example:
      'Data Analytics Tools: Tableau, Power BI, Microsoft Excel (Intermediate)'
      -> ['Tableau', 'Power BI', 'Excel']
    """
    if not raw_skill_input or not isinstance(raw_skill_input, str):
        return []

    cleaned = clean_ocr_and_annotations(raw_skill_input)

    # Strip category prefix if present (e.g. "Data Analytics Tools: Tableau, Power BI")
    if ":" in cleaned:
        parts = cleaned.split(":", 1)
        cleaned = parts[1].strip()

    # Split by comma, semicolon, bullet
    sub_tokens = re.split(r'[,;•\n]+', cleaned)
    atomic_list: List[str] = []

    for token in sub_tokens:
        tok_clean = token.strip()
        if not tok_clean:
            continue

        norm = normalize_skill_name(tok_clean)
        if norm and norm not in atomic_list:
            atomic_list.append(norm)

    return atomic_list


def normalize_skill_name(skill: str) -> str:
    """Returns canonical normalized skill name if alias exists, else cleaned title case."""
    if not skill or not isinstance(skill, str):
        return ""

    cleaned = clean_ocr_and_annotations(skill)
    lower = cleaned.lower()

    if lower in SKILL_ALIASES:
        return SKILL_ALIASES[lower]

    # Check partial phrase matches for Excel / Power BI / SQL
    if "excel" in lower and "functions" in lower:
        return "Excel"
    if lower.startswith("ms excel") or lower.startswith("microsoft excel") or lower == "excel":
        return "Excel"
    if "power bi" in lower or lower == "powerbi":
        return "Power BI"
    if lower == "tableau":
        return "Tableau"

    return cleaned


def skills_match(skill_a: str, skill_b: str) -> bool:
    """
    Check if two skills match safely.
    Handles case-insensitivity, category prefix extraction, and known canonical aliases.
    Enforces strict non-matching rules for distinct technologies (e.g., Java vs JavaScript).
    """
    if not skill_a or not skill_b:
        return False

    a_lower = skill_a.strip().lower()
    b_lower = skill_b.strip().lower()

    if (a_lower, b_lower) in DISTINCT_PAIRS or (b_lower, a_lower) in DISTINCT_PAIRS:
        return False

    if a_lower == b_lower:
        return True

    # Check canonical aliases
    canon_a = normalize_skill_name(skill_a)
    canon_b = normalize_skill_name(skill_b)

    if canon_a.lower() == canon_b.lower():
        return True

    # Safe phrase check (e.g. "Excel" vs "Microsoft Excel" or "Excel Functions")
    if canon_a.lower() == "excel" and ("excel" in b_lower):
        return True
    if canon_b.lower() == "excel" and ("excel" in a_lower):
        return True

    if canon_a.lower() == "power bi" and ("power bi" in b_lower or "powerbi" in b_lower):
        return True
    if canon_b.lower() == "power bi" and ("power bi" in a_lower or "powerbi" in a_lower):
        return True

    return False
