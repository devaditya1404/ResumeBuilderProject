"""
Experience calculator service for TalentVault AI.

Calculates experience_months and experience_years from candidate employment records,
handling date strings, current roles, and overlapping intervals cleanly.
"""
from datetime import datetime
import re
from typing import List, Dict, Any, Tuple


def parse_date_to_month_index(date_str: str, is_end_and_current: bool = False) -> Tuple[int, int]:
    """
    Parse date string like 'Feb 2026', '2026-02', '2025', 'Jan 2025' into (year, month).
    If date_str indicates present/current, returns current (year, month).
    """
    if not date_str or not isinstance(date_str, str):
        if is_end_and_current:
            now = datetime.now()
            return now.year, now.month
        return 0, 0

    clean_str = date_str.strip().lower()

    if clean_str in ["present", "current", "now", "ongoing", "till date"]:
        now = datetime.now()
        return now.year, now.month

    # Try ISO YYYY-MM
    iso_match = re.search(r'(\d{4})[-/](\d{1,2})', clean_str)
    if iso_match:
        y, m = int(iso_match.group(1)), int(iso_match.group(2))
        return y, max(1, min(12, m))

    # Try Month YYYY (e.g. Feb 2026 or February 2026)
    month_names = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }
    for name, m_val in month_names.items():
        if name in clean_str:
            year_match = re.search(r'\b(19\d\d|20\d\d)\b', clean_str)
            if year_match:
                return int(year_match.group(1)), m_val

    # Try plain YYYY
    year_only = re.search(r'\b(19\d\d|20\d\d)\b', clean_str)
    if year_only:
        return int(year_only.group(1)), 1 if not is_end_and_current else 12

    if is_end_and_current:
        now = datetime.now()
        return now.year, now.month

    return 0, 0


def calculate_experience_from_records(experiences: List[Dict[str, Any]]) -> Tuple[int, float]:
    """
    Calculate total non-overlapping experience_months and experience_years from employment items.
    Each item is a dict or object with keys: start_date, end_date, is_current.
    """
    if not experiences:
        return 0, 0.0

    intervals = []

    for exp in experiences:
        # Handle dict or Pydantic/SQLAlchemy model object
        start_date = getattr(exp, "start_date", None) if not isinstance(exp, dict) else exp.get("start_date")
        end_date = getattr(exp, "end_date", None) if not isinstance(exp, dict) else exp.get("end_date")
        is_current = getattr(exp, "is_current", False) if not isinstance(exp, dict) else exp.get("is_current", False)

        start_y, start_m = parse_date_to_month_index(start_date, is_end_and_current=False)
        end_y, end_m = parse_date_to_month_index(end_date, is_end_and_current=is_current)

        if start_y > 0 and end_y > 0:
            start_val = start_y * 12 + start_m
            end_val = end_y * 12 + end_m
            if end_val >= start_val:
                intervals.append((start_val, end_val))

    if not intervals:
        return 0, 0.0

    # Merge overlapping month intervals
    intervals.sort(key=lambda x: x[0])
    merged = []
    for start, end in intervals:
        if not merged:
            merged.append([start, end])
        else:
            prev_start, prev_end = merged[-1]
            if start <= prev_end + 1:
                merged[-1][1] = max(prev_end, end)
            else:
                merged.append([start, end])

    total_months = sum((end - start + 1) for start, end in merged)
    total_years = round(total_months / 12.0, 1)

    return total_months, total_years
