import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def format_timestamp() -> str:
    """Returns formatted current timestamp"""
    return datetime.now().strftime("%d-%m-%Y %I:%M %p")


def clean_filename(name: str) -> str:
    """Cleans a string to be safe for use as filename"""
    return name.strip().replace(" ", "_").lower()


def validate_patient_name(name: str) -> dict:
    """Validates patient name input"""
    if not name or len(name.strip()) == 0:
        return {
            "valid": False,
            "error": "Patient name cannot be empty."
        }
    if len(name.strip()) < 2:
        return {
            "valid": False,
            "error": "Patient name must be at least 2 characters."
        }
    if len(name.strip()) > 50:
        return {
            "valid": False,
            "error": "Patient name must be less than 50 characters."
        }
    return {"valid": True, "error": None}


def validate_email(email: str) -> bool:
    """Basic email format validation"""
    if not email:
        return False
    if "@" not in email:
        return False
    if "." not in email.split("@")[-1]:
        return False
    return True


def get_file_size_mb(file) -> float:
    """Returns file size in MB"""
    try:
        size_bytes = len(file.getvalue())
        return round(size_bytes / (1024 * 1024), 2)
    except Exception:
        return 0.0


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncates long text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def format_analysis_for_email(analysis: str) -> str:
    """Formats analysis text for email body"""
    lines = analysis.split("\n")
    formatted = ""
    for line in lines:
        if line.strip():
            formatted += f"{line.strip()}<br>"
    return formatted


def get_emergency_contact_info() -> dict:
    """Returns emergency contact information"""
    return {
        "pakistan_emergency": "1122",
        "edhi_foundation": "115",
        "rescue": "1122",
        "police": "15",
        "ambulance": "1122"
    }
