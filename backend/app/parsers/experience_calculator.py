"""
Experience date normalization, overlap detection, and total months calculation.

Handles:
- Various date formats (Jan 2020, January 2020, 01/2020, 2020)
- "Present" / "Current" as end date
- Overlapping employment periods (counted once)
- Current vs latest employer detection
"""
import re
from datetime import date, datetime
from typing import List, Optional, Tuple
from dataclasses import dataclass

# ── Month name mapping ──────────────────────────────────────────
MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

# Patterns for "present" / "current"
PRESENT_PATTERNS = {"present", "current", "till date", "ongoing", "now", "to date"}


@dataclass
class DateRange:
    start_date: Optional[date] = None
    end_date: Optional[date] = None  # None means "present"
    is_current: bool = False
    raw_start: str = ""
    raw_end: str = ""

    @property
    def start_month_year(self) -> Optional[str]:
        if self.start_date:
            return self.start_date.strftime("%Y-%m")
        return None

    @property
    def end_month_year(self) -> Optional[str]:
        if self.is_current:
            return "Present"
        if self.end_date:
            return self.end_date.strftime("%Y-%m")
        return None


def parse_date_string(date_str: str) -> Optional[date]:
    """
    Parse various date string formats into a date object.

    Supported formats:
    - "Jan 2020", "January 2020"
    - "01/2020", "1/2020"
    - "2020-01", "2020/01"
    - "2020" (assumes January)
    - "Present", "Current" -> returns None (handled separately)
    """
    if not date_str:
        return None

    cleaned = date_str.strip().lower()

    # Check for "present" / "current"
    if cleaned in PRESENT_PATTERNS:
        return None  # Caller handles this as is_current=True

    # Format: "Month Year" (e.g., "Jan 2020", "January 2020")
    match = re.match(r"([a-zA-Z]+)\s*[,.]?\s*(\d{4})", date_str.strip())
    if match:
        month_str = match.group(1).lower()
        year = int(match.group(2))
        month = MONTH_MAP.get(month_str)
        if month and 1900 <= year <= 2100:
            return date(year, month, 1)

    # Format: "MM/YYYY" or "M/YYYY"
    match = re.match(r"(\d{1,2})[/\-](\d{4})", date_str.strip())
    if match:
        month = int(match.group(1))
        year = int(match.group(2))
        if 1 <= month <= 12 and 1900 <= year <= 2100:
            return date(year, month, 1)

    # Format: "YYYY-MM" or "YYYY/MM"
    match = re.match(r"(\d{4})[/\-](\d{1,2})", date_str.strip())
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        if 1 <= month <= 12 and 1900 <= year <= 2100:
            return date(year, month, 1)

    # Format: "YYYY" only
    match = re.match(r"^(\d{4})$", date_str.strip())
    if match:
        year = int(match.group(1))
        if 1900 <= year <= 2100:
            return date(year, 1, 1)

    return None


def parse_date_range(start_str: str, end_str: str) -> DateRange:
    """Parse a start and end date string into a DateRange."""
    is_current = end_str.strip().lower() in PRESENT_PATTERNS if end_str else False

    start_date = parse_date_string(start_str)
    end_date = None if is_current else parse_date_string(end_str)

    return DateRange(
        start_date=start_date,
        end_date=end_date,
        is_current=is_current,
        raw_start=start_str or "",
        raw_end=end_str or "",
    )


def calculate_months_between(start: date, end: Optional[date]) -> int:
    """Calculate months between two dates. If end is None, use today."""
    if not start:
        return 0

    end_date = end or date.today()

    if end_date < start:
        return 0

    months = (end_date.year - start.year) * 12 + (end_date.month - start.month)
    return max(0, months)


def calculate_total_experience_months(date_ranges: List[DateRange]) -> int:
    """
    Calculate total experience in months, handling overlapping periods.

    Uses a timeline merge approach:
    1. Convert all ranges to (start_month, end_month) tuples
    2. Sort and merge overlapping intervals
    3. Sum up merged intervals
    """
    if not date_ranges:
        return 0

    # Convert to sortable intervals (month index from epoch)
    intervals: List[Tuple[int, int]] = []

    for dr in date_ranges:
        if not dr.start_date:
            continue

        start_months = dr.start_date.year * 12 + dr.start_date.month
        if dr.is_current or not dr.end_date:
            end_months = date.today().year * 12 + date.today().month
        else:
            end_months = dr.end_date.year * 12 + dr.end_date.month

        if end_months >= start_months:
            intervals.append((start_months, end_months))

    if not intervals:
        return 0

    # Sort by start
    intervals.sort()

    # Merge overlapping intervals
    merged: List[Tuple[int, int]] = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            # Overlapping — extend
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # Sum up
    total = sum(end - start for start, end in merged)
    return total


def determine_current_employer(
    experiences: List[dict],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Determine CURRENT employer and designation.
    Returns (company, title) ONLY if an employment record is explicitly ongoing
    (e.g., end_date is 'Present', 'Current', 'Ongoing').
    Otherwise returns (None, None).
    """
    if not experiences:
        return None, None

    for exp in experiences:
        end_str = (exp.get("end_date") or "").strip().lower()
        if end_str in PRESENT_PATTERNS:
            return exp.get("company"), exp.get("title")

    return None, None


def determine_latest_employer(
    experiences: List[dict],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Determine LATEST employer and designation chronologically.
    Returns (company, title) of the most recent employment record.
    """
    if not experiences:
        return None, None

    # First check ongoing positions
    curr_comp, curr_title = determine_current_employer(experiences)
    if curr_comp:
        return curr_comp, curr_title

    # If no ongoing position, pick the position with the latest end or start date
    latest = None
    latest_date = None

    for exp in experiences:
        # Check end date first, then start date
        end_d = parse_date_string(exp.get("end_date", ""))
        start_d = parse_date_string(exp.get("start_date", ""))
        effective_d = end_d or start_d

        if effective_d:
            if latest_date is None or effective_d > latest_date:
                latest_date = effective_d
                latest = exp

    if latest:
        return latest.get("company"), latest.get("title")

    # Fallback to first position in list
    first = experiences[0]
    return first.get("company"), first.get("title")
