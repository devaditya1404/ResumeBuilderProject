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
    "java": "Java",
    "core java": "Java",
    "java 8+": "Java",
    "java 8": "Java",
    "java 11": "Java",
    "java 17": "Java",
    "java ee": "Java",
    "j2ee": "Java",
    "springboot": "Spring Boot",
    "spring boot": "Spring Boot",
    "sql": "SQL",
    "oracle sql": "SQL",
    "mysql": "SQL",
    "pl/sql": "SQL",
    "plsql": "SQL",
    "t-sql": "SQL",
    "tsql": "SQL",
    "sdlc": "SDLC",
    "software development life cycle": "SDLC",
    "git": "Git",
    "github": "Git",
    "gitlab": "Git",
    "jira": "Jira",
    "atlassian jira": "Jira",
    "rest api": "REST API",
    "restful api": "REST API",
    "restful apis": "REST API",
    "restful webservices": "REST API",
    "restful": "REST API",
    "rest": "REST API",
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
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "Google Cloud Platform",
    "google cloud": "Google Cloud Platform",
    "google cloud platform": "Google Cloud Platform",
    "azure": "Microsoft Azure",
    "ms azure": "Microsoft Azure",
    "microsoft azure": "Microsoft Azure",
    "tf": "Terraform",
    "terraform": "Terraform",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "nosql": "NoSQL",
    "no sql": "NoSQL",
    "py": "Python",
    "python": "Python",
    # SAP Modules & Enterprise Skills
    "sap": "SAP",
    "sap sd": "SAP SD",
    "sap sd module": "SAP SD",
    "sap sd functional consultant": "SAP SD",
    "sap s4 hana": "SAP S/4 HANA",
    "sap s/4 hana": "SAP S/4 HANA",
    "s4/hana": "SAP S/4 HANA",
    "s4 hana": "SAP S/4 HANA",
    "sap erp": "SAP ERP",
    "sap erp consultant": "SAP ERP",
    "sap mm": "SAP MM",
    "sap pp": "SAP PP",
    "sap fico": "SAP FICO",
    "sap fi/co": "SAP FICO",
    "sap abap": "SAP ABAP",
    "pivot table": "Pivot Tables",
    "pivot tables": "Pivot Tables",
    "pivot": "Pivot Tables",
    "vlookup": "VLOOKUP",
    "v look up": "VLOOKUP",
    "xlookup": "XLOOKUP",
    "power query": "Power Query",
    # IT Support, Deskside & Infrastructure Aliases
    "troubleshooting": "Troubleshooting",
    "technical troubleshooting": "Troubleshooting",
    "desktop troubleshooting": "Troubleshooting",
    "deskside support": "Troubleshooting",
    "ticket management": "Ticket Management",
    "ticket handling": "Ticket Management",
    "ticketing": "Ticket Management",
    "incident management": "Ticket Management",
    "system maintenance": "System Maintenance",
    "desktop support": "System Maintenance",
    "system support": "System Maintenance",
    "hardware maintenance": "System Maintenance",
    "it maintenance": "System Maintenance",
    "operating systems": "Operating Systems",
    "os installation": "Operating Systems",
    "networking": "Networking",
    "networking concepts": "Networking",
    "lan/wan": "LAN/WAN",
    "lan": "LAN",
    "wan": "WAN",
    "zendesk": "Zendesk",
    "freshdesk": "Freshdesk",
    "comptia a+": "CompTIA A+",
    "a+": "CompTIA A+",
    "c++": "C++",
    "c#": "C#",
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
    ("react", "angular"),
    ("angular", "react"),
    ("react", "angularjs"),
    ("angularjs", "react"),
    ("sql", "oracle"),
    ("oracle", "sql"),
}

GENERIC_CATEGORY_WORDS = {
    "tools", "frameworks", "methodology", "database", "database:", "testing:", "concepts:", "api",
    "frameworks:", "tools:", "methodology:", "concepts", "integration", "api integration"
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
    Split category prefixes, parenthetical groupings, and composite skill entries into atomic comparable skills.
    Example:
      'Operating Systems (Windows, Linux, macOS)' -> ['Operating Systems', 'Windows', 'Linux', 'macOS']
      'Networking concepts (LAN/WAN)' -> ['Networking concepts', 'LAN/WAN', 'LAN', 'WAN']
      'Ticketing and remote desktop applications (Zendesk, Freshdesk)' -> ['Ticketing and remote desktop applications', 'Zendesk', 'Freshdesk']
    """
    if not raw_skill_input or not isinstance(raw_skill_input, str):
        return []

    cleaned = clean_ocr_and_annotations(raw_skill_input)
    atomic_list: List[str] = []

    # First, extract parenthetical contents cleanly if present
    parenthetical_matches = re.findall(r'\(([^)]+)\)', cleaned)
    
    # Remove parenthetical blocks to get base skill title
    base_title = re.sub(r'\([^)]*\)', '', cleaned).strip()

    candidate_raw_tokens = []
    if base_title:
        candidate_raw_tokens.append(base_title)
    
    for p_content in parenthetical_matches:
        candidate_raw_tokens.append(p_content)

    # Split sub-tokens by colon, slash, comma, semicolon, bullet, newline, 'and'
    for raw_tok in candidate_raw_tokens:
        sub_tokens = re.split(r'[:;,•\n]+|\b(?:and)\b', raw_tok, flags=re.IGNORECASE)
        for token in sub_tokens:
            # Also handle slashes like LAN/WAN -> both LAN/WAN and LAN, WAN
            slash_tokens = [token.strip()]
            if '/' in token and not token.strip().lower().startswith("http"):
                slash_tokens.extend([t.strip() for t in token.split('/') if t.strip()])
            
            for st in slash_tokens:
                st_clean = st.strip()
                if not st_clean:
                    continue

                if st_clean.lower() in GENERIC_CATEGORY_WORDS:
                    continue

                norm = normalize_skill_name(st_clean)
                if norm and norm.lower() not in GENERIC_CATEGORY_WORDS and norm not in atomic_list:
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
    if lower in ["java 8+", "java 8", "java 11", "java 17", "core java"]:
        return "Java"
    if "spring boot" in lower:
        return "Spring Boot"
    if lower in ["restful api", "restful apis", "rest api", "restful webservices"]:
        return "REST API"

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

    # Check atomic sub-tokens if composite strings are passed
    sub_a = extract_atomic_skills(skill_a)
    sub_b = extract_atomic_skills(skill_b)

    for sa in sub_a:
        for sb in sub_b:
            if (sa.lower(), sb.lower()) in DISTINCT_PAIRS or (sb.lower(), sa.lower()) in DISTINCT_PAIRS:
                continue
            if sa.lower() == sb.lower() or normalize_skill_name(sa).lower() == normalize_skill_name(sb).lower():
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

    # SAP module relationship matching (e.g. SAP ERP vs SAP SD / SAP MM)
    if "sap" in canon_a.lower() and "sap" in canon_b.lower():
        return True

    return False

