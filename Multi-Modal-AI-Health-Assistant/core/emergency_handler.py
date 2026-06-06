import os
import sys
from datetime import datetime

# Config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import EMERGENCY_KEYWORDS
from core.email_service import send_emergency_email

def check_for_emergency(analysis_text: str) -> bool:
    """
    Checks if the AI analysis contains any emergency keywords
    Returns True if emergency detected
    """
    text_lower = analysis_text.lower()
    for keyword in EMERGENCY_KEYWORDS:
        if keyword.lower() in text_lower:
            return True
    return False


def get_urgency_color(urgency_level: str) -> str:
    """
    Returns color code based on urgency level
    """
    colors = {
        "CRITICAL": "#FF0000",
        "HIGH": "#FF6600",
        "MEDIUM": "#FFA500",
        "LOW": "#00AA00"
    }
    return colors.get(urgency_level, "#00AA00")


def get_urgency_emoji(urgency_level: str) -> str:
    """
    Returns emoji based on urgency level
    """
    emojis = {
        "CRITICAL": "🚨",
        "HIGH": "⚠️",
        "MEDIUM": "🔶",
        "LOW": "✅"
    }
    return emojis.get(urgency_level, "✅")


def handle_emergency(
    patient_name: str,
    analysis_text: str,
    urgency_level: str,
    image_path: str = None,
    emergency_contact: str = None
) -> dict:
    """
    Main emergency handler:
    - Checks if situation is critical
    - Sends emergency email with report attached
    - Returns status and message
    """
    
    # Check if emergency exists
    is_emergency = check_for_emergency(analysis_text)
    is_critical = urgency_level in ["CRITICAL", "HIGH"]

    if is_emergency or is_critical:
        # Send emergency email
        email_result = send_emergency_email(
            patient_name=patient_name,
            analysis_text=analysis_text,
            urgency_level=urgency_level,
            image_path=image_path,
            recipient_email=emergency_contact
        )

        return {
            "emergency_detected": True,
            "urgency_level": urgency_level,
            "email_sent": email_result["success"],
            "email_message": email_result["message"],
            "alert_message": f"""
CRITICAL CONDITION DETECTED!

An emergency alert has been automatically sent to your designated 
contact with the full analysis report attached.

Urgency Level: {urgency_level}
Time: {datetime.now().strftime("%d-%m-%Y %I:%M %p")}

Please seek immediate medical attention!
Call Emergency: 1122
            """,
            "color": get_urgency_color(urgency_level),
            "emoji": get_urgency_emoji(urgency_level)
        }

    else:
        return {
            "emergency_detected": False,
            "urgency_level": urgency_level,
            "email_sent": False,
            "email_message": "No emergency detected. Email not sent.",
            "alert_message": "No critical condition detected.",
            "color": get_urgency_color(urgency_level),
            "emoji": get_urgency_emoji(urgency_level)
        }
