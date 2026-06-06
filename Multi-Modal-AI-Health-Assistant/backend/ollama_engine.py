"""
AI Engine Module — Online + Offline Medical Analysis
=====================================================
Priority chain for ANALYSIS:
  1. Groq API (FREE online — best for images + text)
  2. Ollama   (local offline — works without internet)
  3. Knowledge Base (always available — regex + JSON)

Priority chain for CHAT:
  1. Ollama (offline first — so chat works without internet)
  2. Groq   (online fallback)
  3. Basic offline response
"""

import requests
import json
import uuid
import re
import os
import sys
import base64

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.report_analyzer import analyze_report_text, check_emergency_conditions
from dotenv import load_dotenv

load_dotenv()

# ============================================
# CONFIGURATION
# ============================================
# Groq API (FREE — sign up at console.groq.com)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_TEXT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# Gemini API (FREE tier backup)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Ollama (LOCAL — completely offline)
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
IMAGE_MODEL = "llava"
TEXT_MODEL = "llama3.2:3b"

MEDICAL_ANALYSIS_PROMPT = """You are an expert AI Medical Assistant. Analyze the provided medical report, image, or symptoms carefully.

Context from document: {text_context}
User Question: {question}

Provide a detailed analysis including:
1. **Observation**: What you observe in the report/image
2. **Possible Conditions**: What medical conditions this may indicate
3. **Key Findings**: Any abnormal values or concerning features
4. **Recommended Actions**: What the patient should do next
5. **Prevention Tips**: How to prevent or manage these conditions
6. **Urgency Assessment**: Rate as NORMAL, WARNING, or CRITICAL

Be specific and helpful. If analyzing a medical image (X-ray, blood report, skin condition), describe what you see in detail.

IMPORTANT: End with a disclaimer that this is AI-generated and the patient should consult a real doctor.
At the very end, write exactly: URGENCY: [LEVEL] where [LEVEL] is NORMAL, WARNING, or CRITICAL."""


# ============================================
# STATUS CHECK
# ============================================
def check_ollama_status() -> dict:
    """Check Ollama + Online API availability."""
    result = {
        "running": False,
        "models": [],
        "has_image_model": False,
        "has_text_model": False,
        "online_available": False,
        "online_provider": None
    }

    # Check Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            result["running"] = True
            result["models"] = model_names
            result["has_image_model"] = any("llava" in m for m in model_names)
            result["has_text_model"] = len(model_names) > 0
    except Exception:
        pass

    # Check online API availability
    if GROQ_API_KEY:
        result["online_available"] = True
        result["online_provider"] = "Groq"
    elif GEMINI_API_KEY:
        result["online_available"] = True
        result["online_provider"] = "Gemini"

    return result


# ============================================
# MAIN ANALYSIS FUNCTION
# ============================================
def analyze_medical_data(image_b64: str = None, text_context: str = "",
                          question: str = "", action: str = "combined_approach"):
    """
    Analyze medical data using the best available engine.
    Flow: Online API → Ollama (offline) → Knowledge Base fallback

    Returns: (analysis_text, urgency_level, diagnosis_id)
    """
    diagnosis_id = str(uuid.uuid4())

    # Always run KB analysis (available offline)
    kb_analysis = analyze_report_text(text_context, question)
    kb_summary = kb_analysis.get("summary", "")
    kb_urgency = kb_analysis.get("urgency", "NORMAL")

    # Check emergency conditions
    emergency = check_emergency_conditions(f"{text_context} {question}")

    # If RL chose keyword/KB strategy, use that directly
    if action in ["keyword_basic", "knowledge_base"]:
        result = kb_summary if kb_summary else "No analysis available for the provided input."
        if emergency.get("is_emergency"):
            result = _prepend_emergency(emergency, result)
            kb_urgency = "CRITICAL"
        return result, kb_urgency, diagnosis_id

    # -------- TRY ONLINE API FIRST (best quality, esp. for images) --------
    ai_result = None
    used_engine = None

    # Try Groq (FREE)
    if GROQ_API_KEY:
        ai_result = _call_groq(image_b64, text_context, question)
        if ai_result:
            used_engine = "Groq AI"

    # Try Gemini if Groq failed
    if ai_result is None and GEMINI_API_KEY:
        ai_result = _call_gemini(image_b64, text_context, question)
        if ai_result:
            used_engine = "Gemini AI"

    # -------- TRY OLLAMA (offline) --------
    if ai_result is None:
        ai_result = _call_ollama(image_b64, text_context, question, action)
        if ai_result:
            used_engine = "Ollama (Offline)"

    # -------- BUILD FINAL RESULT --------
    if ai_result:
        urgency = _extract_urgency(ai_result)

        # For combined approach, merge AI + KB results
        if action == "combined_approach" and kb_summary and kb_analysis.get("values_found", 0) > 0:
            ai_result = (
                f"{ai_result}\n\n"
                f"{'=' * 50}\n"
                f"AUTOMATED LAB VALUE ANALYSIS:\n"
                f"{'=' * 50}\n"
                f"{kb_summary}"
            )
            if kb_urgency == "CRITICAL":
                urgency = "CRITICAL"
            elif kb_urgency == "WARNING" and urgency == "NORMAL":
                urgency = "WARNING"

        # Add engine info
        ai_result = f"[Analyzed by: {used_engine}]\n\n{ai_result}"

        if emergency.get("is_emergency"):
            urgency = "CRITICAL"
            ai_result = _prepend_emergency(emergency, ai_result)

        return ai_result, urgency, diagnosis_id

    # -------- FALLBACK: Knowledge Base only --------
    if kb_summary:
        result = f"[Analyzed by: Knowledge Base (Offline)]\n\n{kb_summary}"
        if emergency.get("is_emergency"):
            result = _prepend_emergency(emergency, result)
            kb_urgency = "CRITICAL"
        return result, kb_urgency, diagnosis_id

    # -------- LAST RESORT --------
    fallback = _generate_fallback(text_context, question, image_b64)
    return fallback, "WARNING", diagnosis_id


# ============================================
# GROQ API (FREE — console.groq.com)
# ============================================
def _call_groq(image_b64: str, text_context: str, question: str) -> str:
    """Call Groq API for analysis. Free tier: thousands of requests/day."""
    if not GROQ_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = MEDICAL_ANALYSIS_PROMPT.format(
        text_context=text_context or "No document text available",
        question=question or "Please analyze the provided medical data"
    )

    # Build message content
    if image_b64:
        # Vision model with image
        user_content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_b64}"
                }
            }
        ]
        model = GROQ_VISION_MODEL
    else:
        user_content = prompt
        model = GROQ_TEXT_MODEL

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert medical AI assistant. Provide detailed, accurate medical analysis."},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.3,
        "max_tokens": 2048
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            print(f"[Groq] API error {response.status_code}: {response.text[:200]}")
            return None
    except requests.exceptions.ConnectionError:
        return None  # No internet
    except Exception as e:
        print(f"[Groq] Error: {e}")
        return None


# ============================================
# GEMINI API (FREE tier)
# ============================================
def _call_gemini(image_b64: str, text_context: str, question: str) -> str:
    """Call Google Gemini API for analysis. Free tier available."""
    if not GEMINI_API_KEY:
        return None

    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"

    prompt = MEDICAL_ANALYSIS_PROMPT.format(
        text_context=text_context or "No document text available",
        question=question or "Please analyze the provided medical data"
    )

    # Build parts
    parts = [{"text": prompt}]

    if image_b64:
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": image_b64
            }
        })

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                text_parts = content.get("parts", [])
                if text_parts:
                    return text_parts[0].get("text", "")
        else:
            print(f"[Gemini] API error {response.status_code}: {response.text[:200]}")
            return None
    except requests.exceptions.ConnectionError:
        return None  # No internet
    except Exception as e:
        print(f"[Gemini] Error: {e}")
        return None


# ============================================
# OLLAMA (LOCAL / OFFLINE)
# ============================================
def _call_ollama(image_b64: str, text_context: str, question: str, action: str) -> str:
    """Call local Ollama for analysis. Works completely offline."""
    prompt = MEDICAL_ANALYSIS_PROMPT.format(
        text_context=text_context or "No document text provided",
        question=question or "Please analyze the provided medical data"
    )

    if action == "ollama_detailed":
        prompt = (
            "IMPORTANT: Provide an extremely detailed medical analysis.\n"
            "Include specific medical terminology and differential diagnoses.\n\n"
            + prompt
        )

    model = IMAGE_MODEL if image_b64 else TEXT_MODEL

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    if image_b64:
        payload["images"] = [image_b64]

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=180)
        if response.status_code == 200:
            return response.json().get("response", "")
        return None
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return None
    except Exception:
        return None


# ============================================
# GROQ CHAT (for chat_handler to use)
# ============================================
def groq_chat(messages: list) -> str:
    """Call Groq API for chat. Used by chat_handler as online fallback."""
    if not GROQ_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_TEXT_MODEL,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 1500
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        return None
    except Exception:
        return None


def gemini_chat(prompt_text: str) -> str:
    """Call Gemini API for chat. Used as last online fallback."""
    if not GEMINI_API_KEY:
        return None

    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1500}
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        return None
    except Exception:
        return None


# ============================================
# UTILITIES
# ============================================
def _extract_urgency(text: str) -> str:
    """Extract urgency level from analysis text."""
    match = re.search(r'URGENCY:\s*(NORMAL|WARNING|CRITICAL)', text, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    text_lower = text.lower()
    if any(w in text_lower for w in ["critical", "emergency", "immediate", "life-threatening"]):
        return "CRITICAL"
    if any(w in text_lower for w in ["warning", "concerning", "abnormal", "elevated", "high risk"]):
        return "WARNING"
    return "NORMAL"


def _prepend_emergency(emergency: dict, text: str) -> str:
    """Prepend emergency alert to analysis text."""
    return (
        f"EMERGENCY DETECTED: {emergency['condition']}\n"
        f"{emergency['immediate_action']}\n\n"
        f"{'=' * 50}\n\n"
        f"{text}"
    )


def _generate_fallback(text_context: str = "", question: str = "", image_b64: str = None) -> str:
    """Generate fallback when all engines are unavailable."""
    parts = ["The AI analysis engines are currently unavailable.\n"]

    if image_b64:
        parts.append("A medical image was uploaded but cannot be analyzed without an AI model.")
        parts.append("Please ensure either:")
        parts.append("  - Internet connection (for online AI analysis)")
        parts.append("  - Ollama is running locally (for offline analysis)\n")

    if text_context:
        parts.append(f"Report text received ({len(text_context)} characters).")
    if question:
        parts.append(f"Your question: {question}\n")

    parts.append("How to enable AI analysis:")
    parts.append("  ONLINE: Get a free Groq API key at console.groq.com")
    parts.append("          Add GROQ_API_KEY=your_key to .env file")
    parts.append("  OFFLINE: Install Ollama from ollama.com")
    parts.append("           Run: ollama serve")
    parts.append("           Run: ollama pull llama3.2:3b")
    parts.append("           Run: ollama pull llava (for images)\n")
    parts.append("Always consult a qualified medical professional.")

    return "\n".join(parts)
