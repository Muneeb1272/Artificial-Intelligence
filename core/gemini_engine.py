from PIL import Image
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.local_analysis import (
    generate_image_analysis,
    generate_text_analysis,
    detect_urgency_level as local_detect_urgency_level
)


def analyze_image_with_text(image: Image.Image, user_query: str = "") -> dict:
    """
    Free local image + text analysis fallback for Streamlit.
    """
    try:
        analysis = generate_image_analysis(image, user_query)
        return {
            "success": True,
            "analysis": analysis,
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "analysis": None,
            "error": str(e)
        }


def analyze_text_only(user_query: str) -> dict:
    """
    Free local text analysis fallback for Streamlit.
    """
    try:
        analysis = generate_text_analysis(user_query)
        return {
            "success": True,
            "analysis": analysis,
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "analysis": None,
            "error": str(e)
        }


# Re-exported for compatibility

def detect_urgency_level(analysis_text: str) -> str:
    return local_detect_urgency_level(analysis_text)
