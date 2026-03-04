"""
Utility Functions
"""
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Any


# ============ FILE OPERATIONS ============

def save_json(data: dict[Any, Any], filepath: Path) -> None:
    """Save data as formatted JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(filepath: Path) -> dict[Any, Any]:
    """Load JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def read_transcript(filepath: Path) -> str:
    """Read transcript file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


# ============ ID GENERATION ============

def generate_account_id(company_name: str) -> str:
    """Generate clean account ID from company name."""
    clean = re.sub(r"[^a-zA-Z0-9\s]", "", company_name)
    return clean.lower().replace(" ", "_").strip("_")


def extract_account_id_from_filename(filename: str) -> str:
    """Extract account ID from transcript filename."""
    name = Path(filename).stem
    name = re.sub(r"_(demo|onboarding)$", "", name)
    return name


# ============ TIMESTAMP HELPERS ============

def get_timestamp() -> str:
    """Get current ISO timestamp."""
    return datetime.now().isoformat()


def format_business_hours(hours_dict: dict) -> str:
    """Format business hours dict as readable string."""
    days = hours_dict.get("days", [])
    start = hours_dict.get("start", "")
    end = hours_dict.get("end", "")
    tz = hours_dict.get("timezone", "")

    if not days or not start or not end:
        return "Hours not specified"

    if len(days) == 7:
        day_str = "Every day"
    elif len(days) == 6 and "Sunday" not in days:
        day_str = "Monday-Saturday"
    elif len(days) == 5 and "Saturday" not in days and "Sunday" not in days:
        day_str = "Monday-Friday"
    else:
        day_str = ", ".join(days)

    return f"{day_str} {start}-{end} {tz}"
