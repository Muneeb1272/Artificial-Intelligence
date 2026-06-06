import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ============================================
# APP SETTINGS
# ============================================
APP_NAME = "Multi-Modal AI Health Assistant"
APP_VERSION = "2.0.0"
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

# ============================================
# OLLAMA SETTINGS (LOCAL AI - FREE)
# ============================================
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_IMAGE_MODEL = "llava"          # Multimodal model for images
OLLAMA_TEXT_MODEL = "llama3.2:3b"     # Text chat model
OLLAMA_TIMEOUT = 180                   # seconds

# ============================================
# EMAIL SETTINGS
# ============================================
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
EMERGENCY_EMAIL = os.getenv("EMERGENCY_EMAIL")
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587

# ============================================
# EMERGENCY KEYWORDS
# ============================================
EMERGENCY_KEYWORDS = [
    "heart attack", "stroke", "chest pain", "difficulty breathing",
    "unconscious", "severe bleeding", "cancer", "tumor",
    "critical", "emergency", "urgent", "immediate",
    "dil ka dora", "sans lena mushkil", "shadeed dard",
    "beyhosh", "khoon", "cancer", "fori"
]

# ============================================
# ANALYSIS PROMPTS
# ============================================
MEDICAL_PROMPT = """
You are a helpful medical AI assistant for Multi-Modal AI Health Assistant.
Analyze the provided image/report and:
1. Describe what you observe in simple, easy-to-understand language
2. Mention possible conditions (if visible)
3. Suggest immediate steps the patient should take
4. Provide prevention tips for identified conditions
5. Rate urgency level: NORMAL / WARNING / CRITICAL
6. Always recommend consulting a real doctor

IMPORTANT: Always end with this disclaimer:
"⚠️ This is AI-generated information only. Please consult a qualified doctor
for proper diagnosis and treatment."

Respond in clear, simple English that a non-medical person can understand.
"""

# ============================================
# RL SETTINGS
# ============================================
RL_LEARNING_RATE = 0.1
RL_DISCOUNT_FACTOR = 0.9
RL_EPSILON_START = 1.0
RL_EPSILON_MIN = 0.1
RL_EPSILON_DECAY = 0.995
