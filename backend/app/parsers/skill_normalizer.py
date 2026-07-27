"""
Generic skill normalizer module.

Converts category-prefixed skill blocks (e.g., "Programming Languages: C, Python")
and delimited skill strings into clean, atomic individual skills.
"""
import re
from typing import List, Set


# Common proficiency level pattern in parentheses e.g. "(Intermediate)", "(Advanced)"
PROFICIENCY_PATTERN = re.compile(r"\s*\((?:intermediate|advanced|beginner|expert|proficient|basic|\d+\+?\s*years?)\)", re.IGNORECASE)

# Known tech variant normalizations
SKILL_VARIANTS = {
    "no sql": "NoSQL",
    "nosql": "NoSQL",
    "reactjs": "React.js",
    "react.js": "React.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
}


def normalize_skills(raw_skills: List[str]) -> List[str]:
    """
    Takes a list of raw extracted skill strings (which may contain category prefixes,
    comma-separated lists, parenthetical ratings, etc.) and normalizes them into atomic skills.

    Returns deduplicated list of clean skill strings.
    """
    if not raw_skills:
        return []

    atomic_skills: List[str] = []
    seen_lower: Set[str] = set()

    for item in raw_skills:
        if not item or not isinstance(item, str):
            continue

        text = item.strip()
        if not text:
            continue

        # 1. Strip category prefix if present (e.g., "Programming Languages: C, Python" -> "C, Python")
        if ":" in text:
            parts = text.split(":", 1)
            category_title = parts[0].strip()
            rest = parts[1].strip()

            if rest:
                text = rest
            elif category_title:
                text = category_title

        # 2. Strip parenthetical proficiencies (e.g., "Microsoft Excel (Intermediate)" -> "Microsoft Excel")
        text = PROFICIENCY_PATTERN.sub("", text).strip()

        # 3. Split by commas or semicolons
        splits = re.split(r"[,;]+", text)

        for s in splits:
            s_clean = s.strip()
            # Clean leading/trailing bullets or dashes
            s_clean = re.sub(r"^[\s•\-\*\.]+", "", s_clean).strip()
            s_clean = PROFICIENCY_PATTERN.sub("", s_clean).strip()

            if not s_clean:
                continue

            s_lower = s_clean.lower()

            # Apply variant normalization if matched
            if s_lower in SKILL_VARIANTS:
                s_clean = SKILL_VARIANTS[s_lower]
                s_lower = s_clean.lower()

            if s_lower not in seen_lower:
                seen_lower.add(s_lower)
                atomic_skills.append(s_clean)

    return atomic_skills
