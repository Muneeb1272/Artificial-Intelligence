import re
from PIL import Image

FREE_MEDICAL_HINTS = [
    (
        ["chest pain", "difficulty breathing", "shortness of breath", "heavy breathing", "heart attack", "angina"],
        "These symptoms may indicate a serious cardiovascular or respiratory problem. Seek immediate medical attention or visit the nearest emergency room.",
        "CRITICAL"
    ),
    (
        ["severe bleeding", "blood loss", "broken bone", "fracture", "unconscious", "fainting", "collapse"],
        "This may be an emergency. Get urgent medical help right away.",
        "CRITICAL"
    ),
    (
        ["high fever", "fever", "temperature", "shivering", "sweating"],
        "Fever can be a sign of infection. Stay hydrated and see a doctor if it does not improve quickly.",
        "HIGH"
    ),
    (
        ["cough", "sore throat", "cold", "flu", "runny nose"],
        "These symptoms often point to a respiratory infection. Rest, drink fluids, and consult a doctor if symptoms worsen.",
        "MEDIUM"
    ),
    (
        ["rash", "itching", "skin", "redness", "swelling"],
        "Skin irritation may need a doctor’s review, especially if it is painful or spreading.",
        "MEDIUM"
    ),
    (
        ["stomach pain", "abdominal pain", "nausea", "vomiting", "diarrhea"],
        "Abdominal discomfort can come from infection or digestive issues. Monitor closely and seek medical advice if it worsens.",
        "MEDIUM"
    ),
    (
        ["headache", "migraine", "dizziness", "lightheaded"],
        "Headaches can have many causes. Rest, drink water, and consult a doctor if the pain is severe or persistent.",
        "LOW"
    ),
]

DEFAULT_RESPONSE = (
    "I can provide general guidance based on the information available, but I am not a doctor. "
    "Please consult a qualified medical professional for a proper diagnosis and treatment."
)


def _normalize_text(text: str) -> str:
    return text.lower().strip()


def _find_matches(text: str):
    normalized = _normalize_text(text)
    matches = []

    for keywords, advice, urgency in FREE_MEDICAL_HINTS:
        for keyword in keywords:
            if keyword in normalized:
                matches.append({
                    "keyword": keyword,
                    "advice": advice,
                    "urgency": urgency
                })
                break

    return matches


def generate_text_analysis(user_query: str) -> str:
    """
    Generates a simple free analysis from a text query.
    """
    if not user_query or not user_query.strip():
        return (
            "No symptoms or question were provided. Please describe your condition or ask a specific medical question."
            f"\n\n{DEFAULT_RESPONSE}"
        )

    matches = _find_matches(user_query)
    response_lines = [
        "I reviewed the symptoms and question you provided."
    ]

    if matches:
        urgencies = set()
        for index, match in enumerate(matches, start=1):
            response_lines.append(f"{index}. {match['advice']}")
            urgencies.add(match["urgency"])

        highest_urgency = "LOW"
        if "CRITICAL" in urgencies:
            highest_urgency = "CRITICAL"
        elif "HIGH" in urgencies:
            highest_urgency = "HIGH"
        elif "MEDIUM" in urgencies:
            highest_urgency = "MEDIUM"

        response_lines.append(f"\nPotential urgency level: {highest_urgency}")
    else:
        response_lines.append(
            "The information provided is not specific enough for a clear conclusion. "
            "If you can share more details like duration, exact symptoms, or test results, I can give better general guidance."
        )

    response_lines.append(f"\n{DEFAULT_RESPONSE}")
    return "\n\n".join(response_lines)


def generate_image_analysis(image: Image.Image, user_query: str = "") -> str:
    """
    Generates a basic response for an uploaded image and optional question.
    """
    width, height = image.size
    image_info = f"An image was uploaded with size {width}×{height} pixels."

    if user_query and user_query.strip():
        analysis = generate_text_analysis(user_query)
        return f"{image_info}\n\n{analysis}"

    return (
        f"{image_info}\n\n"
        "No specific question was provided. Please describe your symptoms or ask a question about the image for better guidance.\n\n"
        f"{DEFAULT_RESPONSE}"
    )


def generate_fallback_analysis(text_context: str = "", question: str = "", image_b64: str = None) -> str:
    """
    Generates a fallback analysis when a local model is not available.
    """
    content = " ".join(filter(None, [text_context, question])).strip()

    if content:
        return generate_text_analysis(content)

    if image_b64:
        return (
            "A medical image was provided, but the free local model cannot inspect it directly. "
            "Please describe the symptoms or enter a question for general medical guidance.\n\n"
            f"{DEFAULT_RESPONSE}"
        )

    return (
        "No medical information was provided. Upload a report or image, and ask a question to get general assistance.\n\n"
        f"{DEFAULT_RESPONSE}"
    )


def detect_urgency_level(analysis_text: str) -> str:
    """
    Detects the urgency level from the analysis text.
    """
    text_lower = _normalize_text(analysis_text)

    if "critical" in text_lower:
        return "CRITICAL"
    if "high" in text_lower or "urgent" in text_lower:
        return "HIGH"
    if "medium" in text_lower or "moderate" in text_lower:
        return "MEDIUM"
    return "LOW"
