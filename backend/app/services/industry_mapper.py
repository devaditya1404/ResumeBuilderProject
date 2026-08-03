"""
Industry Mapper Service.

Infers industry/domain from candidate employer names, designations, and project descriptions.
Examples:
- Dyson -> Manufacturing
- Toyota -> Automotive
- HSBC / Citi / Bankware Japan / ADP -> Banking
- Pfizer -> Healthcare
- Amazon -> E-commerce
"""
from typing import Dict, Any, List, Set

EMPLOYER_INDUSTRY_MAP: Dict[str, str] = {
    "dyson": "Manufacturing",
    "toyota": "Automotive",
    "honda": "Automotive",
    "ford": "Automotive",
    "tesla": "Automotive",
    "bmw": "Automotive",
    "hsbc": "Banking",
    "citi": "Banking",
    "citigroup": "Banking",
    "jpmorgan": "Banking",
    "chase": "Banking",
    "barclays": "Banking",
    "bankware japan": "Banking",
    "adp": "Banking",
    "pfizer": "Healthcare",
    "novartis": "Healthcare",
    "roche": "Healthcare",
    "johnson & johnson": "Healthcare",
    "merck": "Healthcare",
    "amazon": "E-commerce",
    "flipkart": "E-commerce",
    "ebay": "E-commerce",
    "shopify": "E-commerce",
    "infosys": "IT Services",
    "cognizant": "IT Services",
    "ust global": "IT Services",
    "tcs": "IT Services",
    "wipro": "IT Services",
    "accenture": "IT Services",
    "fidel softech": "IT Services",
    "genech": "IT Services",
    "indocosmo": "IT Services",
}


def infer_industries_from_candidate(candidate_data: Dict[str, Any]) -> List[str]:
    """
    Infer domain/industry from candidate structured profile (experiences, companies, projects, summary).
    """
    inferred: Set[str] = set()

    # Check current / latest company
    current_comp = (candidate_data.get("current_company") or candidate_data.get("latest_company") or "").lower()
    for employer, ind in EMPLOYER_INDUSTRY_MAP.items():
        if employer in current_comp:
            inferred.add(ind)

    # Check employment history companies & designations
    exps = candidate_data.get("experiences") or []
    for exp in exps:
        comp = (exp.get("company") or "").lower()
        for employer, ind in EMPLOYER_INDUSTRY_MAP.items():
            if employer in comp:
                inferred.add(ind)

    # Check projects
    projects = candidate_data.get("projects") or []
    for proj in projects:
        p_str = (f"{proj.get('name', '')} {proj.get('description', '')}").lower()
        if "banking" in p_str or "payroll" in p_str or "financial" in p_str or "finance" in p_str:
            inferred.add("Banking")
        if "manufacturing" in p_str or "mrp" in p_str or "plant" in p_str:
            inferred.add("Manufacturing")
        if "automotive" in p_str or "vehicle" in p_str:
            inferred.add("Automotive")
        if "healthcare" in p_str or "pharma" in p_str or "clinical" in p_str:
            inferred.add("Healthcare")
        if "e-commerce" in p_str or "ecommerce" in p_str or "retail" in p_str:
            inferred.add("E-commerce")

    # Keyword check in professional summary
    summary_text = (candidate_data.get("summary") or candidate_data.get("professional_summary") or "").lower()
    if "banking" in summary_text or "finance" in summary_text or "payroll" in summary_text:
        inferred.add("Banking")
    if "manufacturing" in summary_text:
        inferred.add("Manufacturing")
    if "automotive" in summary_text:
        inferred.add("Automotive")
    if "healthcare" in summary_text:
        inferred.add("Healthcare")
    if "e-commerce" in summary_text or "ecommerce" in summary_text:
        inferred.add("E-commerce")

    return list(inferred)
