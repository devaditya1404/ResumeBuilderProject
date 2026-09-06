import pytest
from app.services.match_engine import evaluate_match, find_skill_evidence_in_candidate, build_skill_regex
from app.services.skill_alias import extract_atomic_skills, normalize_skill_name, skills_match

def test_non_word_symbol_matching():
    """Verify skills ending in +, #, .js match correctly without boundary truncation."""
    cand_data = {
        "skills": ["CompTIA A+", "C++", "C#", "Node.js", ".NET"],
        "certifications": [{"name": "CompTIA A+ Certified"}],
        "experiences": [
            {
                "company": "Tech Corp",
                "designation": "Senior Developer",
                "responsibilities": ["Developed backend microservices using C++ and C#."]
            }
        ]
    }

    # 1. CompTIA A+
    status, evidence, _ = find_skill_evidence_in_candidate("CompTIA A+", cand_data)
    assert status == "MATCH", f"Expected MATCH for CompTIA A+, got {status}"

    # 2. C++
    status, evidence, _ = find_skill_evidence_in_candidate("C++", cand_data)
    assert status == "MATCH", f"Expected MATCH for C++, got {status}"

    # 3. C#
    status, evidence, _ = find_skill_evidence_in_candidate("C#", cand_data)
    assert status == "MATCH", f"Expected MATCH for C#, got {status}"

    # 4. Node.js
    status, evidence, _ = find_skill_evidence_in_candidate("Node.js", cand_data)
    assert status == "MATCH", f"Expected MATCH for Node.js, got {status}"


def test_parenthetical_atomic_extraction():
    """Verify parenthetical requirement strings extract atomic components cleanly."""
    atoms1 = extract_atomic_skills("Operating Systems (Windows, Linux, macOS)")
    assert "Operating Systems" in atoms1 or "Windows" in atoms1 or "Linux" in atoms1

    atoms2 = extract_atomic_skills("Networking concepts (LAN/WAN)")
    assert "LAN/WAN" in atoms2 or "LAN" in atoms2 or "Networking" in atoms2

    atoms3 = extract_atomic_skills("Ticketing and remote desktop applications (Zendesk, Freshdesk)")
    assert "Zendesk" in atoms3 and "Freshdesk" in atoms3


def test_rebecca_deskside_support_matching_precision():
    """Regression test for Rebecca Sommerau Deskside Support Engineer matching."""
    rebecca_candidate = {
        "name": "Rebecca Sommerau",
        "location": "Japan",
        "experience_years": 7.2,
        "current_company": "EIRE Systems",
        "current_designation": "Deskside Support Engineer",
        "skills": [
            "Deskside Support", "Technical Troubleshooting", "System Maintenance",
            "Ticket Handling", "Windows 10", "Linux", "macOS", "LAN/WAN",
            "Zendesk", "Freshdesk", "Documentation", "Active Directory", "Hardware Repair"
        ],
        "experiences": [
            {
                "company": "EIRE Systems",
                "designation": "Deskside Support Engineer",
                "responsibilities": [
                    "Provided tier-2/3 deskside support and technical troubleshooting for 500+ users across Tokyo office.",
                    "Managed ticket management and incident escalation using Zendesk and Freshdesk ticketing systems.",
                    "Performed routine system maintenance, hardware deployment, and OS installation for Windows, Linux, and macOS laptops.",
                    "Maintained office networking concepts including LAN/WAN configuration, routers, switches, and VPN access."
                ]
            }
        ],
        "certifications": [{"name": "CompTIA A+"}]
    }

    deskside_jd = {
        "job_title": "Deskside Support Engineer",
        "minimum_experience": 5.0,
        "location": "Japan",
        "mandatory_skills": [
            "Troubleshooting",
            "Ticket Management",
            "System Maintenance",
            "Documentation",
            "Operating Systems (Windows, Linux, macOS)",
            "Networking concepts (LAN/WAN)",
            "Ticketing and remote desktop applications (Zendesk, Freshdesk)"
        ],
        "preferred_skills": [
            "Active Directory",
            "Hardware Repair",
            "CompTIA A+"
        ]
    }

    output = evaluate_match(deskside_jd, rebecca_candidate)
    assert output.overall_score >= 85.0
    assert len(output.missing_mandatory_skills) == 0
    assert "CompTIA A+" in output.matching_skills or "CompTIA A+" in output.evidence_map
