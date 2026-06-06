"""
Chat Handler Module — Online + Offline
=======================================
Chat priority:
  1. Ollama (offline — so chat ALWAYS works even without internet)
  2. Groq API (online free — when Ollama not installed)
  3. Gemini API (online free — another fallback)
  4. Basic offline response (always available)
"""

import json
import os
import time
import requests

from backend.ollama_engine import groq_chat, gemini_chat

# ============================================
# CONFIGURATION
# ============================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CHAT_HISTORY_FILE = os.path.join(DATA_DIR, "chat_history.json")

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
DEFAULT_CHAT_MODEL = "llama3.2:3b"

os.makedirs(DATA_DIR, exist_ok=True)

SYSTEM_PROMPT = """You are an AI Medical Health Assistant. You provide helpful, accurate medical information while always recommending professional medical consultation.

You can:
1. Explain medical conditions in simple, easy-to-understand language
2. Suggest preventive measures and healthy lifestyle tips
3. Interpret basic health metrics and lab results
4. Provide first-aid guidance for common situations
5. Answer general health and wellness questions
6. Explain medications and their common side effects

IMPORTANT RULES:
- Always remind users that you are an AI and they should consult a real doctor
- Never diagnose with certainty - use phrases like "this may indicate" or "could suggest"
- For emergencies, always advise calling emergency services (1122)
- Be empathetic and caring in your responses
- If you don't know something, say so honestly
- Provide evidence-based information only"""


class ChatManager:
    """Manages chat conversations with online + offline AI models."""

    def __init__(self):
        self.conversations = self._load_conversations()

    def _load_conversations(self):
        """Load saved conversations from disk."""
        if os.path.exists(CHAT_HISTORY_FILE):
            try:
                with open(CHAT_HISTORY_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, KeyError):
                return {}
        return {}

    def _save_conversations(self):
        """Save conversations to disk."""
        with open(CHAT_HISTORY_FILE, "w") as f:
            json.dump(self.conversations, f, indent=2)

    def get_or_create_conversation(self, conversation_id: str):
        """Get existing conversation or create new one."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "id": conversation_id,
                "messages": [],
                "created_at": time.time(),
                "updated_at": time.time(),
                "report_context": None
            }
        return self.conversations[conversation_id]

    def add_report_context(self, conversation_id: str, report_text: str):
        """Add analyzed report context to the conversation."""
        conv = self.get_or_create_conversation(conversation_id)
        conv["report_context"] = report_text
        self._save_conversations()

    def send_message(self, conversation_id: str, user_message: str,
                     model: str = None) -> dict:
        """
        Send a message and get AI response.
        Priority: Ollama (offline) → Groq (online) → Gemini (online) → Basic
        """
        conv = self.get_or_create_conversation(conversation_id)
        model = model or DEFAULT_CHAT_MODEL

        # Add user message to history
        conv["messages"].append({
            "role": "user",
            "content": user_message,
            "timestamp": time.time()
        })

        # Build message list
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if conv.get("report_context"):
            messages.append({
                "role": "system",
                "content": f"The patient has a medical report with these findings:\n{conv['report_context']}\nUse this context to provide more relevant answers."
            })

        for msg in conv["messages"][-20:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # -------- TRY ENGINES IN ORDER --------
        response_text = None
        engine_used = None

        # 1. Try Ollama (offline first — so chat works without internet)
        response_text = self._call_ollama_chat(messages, model)
        if response_text:
            engine_used = "Ollama (Offline)"

        # 2. Try Groq (online free)
        if response_text is None:
            response_text = self._call_groq_chat(messages)
            if response_text:
                engine_used = "Groq AI (Online)"

        # 3. Try Gemini (online free)
        if response_text is None:
            response_text = self._call_gemini_chat(user_message, conv)
            if response_text:
                engine_used = "Gemini AI (Online)"

        # 4. Basic offline response
        if response_text is None:
            response_text = self._offline_response(user_message)
            engine_used = "Basic (Offline)"

        # Add assistant response to history
        conv["messages"].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": time.time()
        })

        conv["updated_at"] = time.time()
        self._save_conversations()

        return {
            "success": True,
            "response": response_text,
            "conversation_id": conversation_id,
            "message_count": len(conv["messages"]),
            "engine": engine_used
        }

    # ============================================
    # ENGINE 1: OLLAMA (OFFLINE)
    # ============================================
    def _call_ollama_chat(self, messages: list, model: str) -> str:
        """Call Ollama chat API. Works completely offline."""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            response = requests.post(OLLAMA_URL, json=payload, timeout=120)
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "")
            return None
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return None
        except Exception:
            return None

    # ============================================
    # ENGINE 2: GROQ (ONLINE FREE)
    # ============================================
    def _call_groq_chat(self, messages: list) -> str:
        """Call Groq API for chat. Uses function from ollama_engine."""
        try:
            return groq_chat(messages)
        except Exception:
            return None

    # ============================================
    # ENGINE 3: GEMINI (ONLINE FREE)
    # ============================================
    def _call_gemini_chat(self, user_message: str, conv: dict) -> str:
        """Call Gemini API for chat."""
        try:
            # Build prompt with context
            context_parts = [SYSTEM_PROMPT + "\n"]
            if conv.get("report_context"):
                context_parts.append(f"Report context: {conv['report_context']}\n")
            for msg in conv["messages"][-8:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                context_parts.append(f"{role}: {msg['content']}")
            context_parts.append(f"User: {user_message}")
            context_parts.append("Assistant:")

            full_prompt = "\n".join(context_parts)
            return gemini_chat(full_prompt)
        except Exception:
            return None

    # ============================================
    # ENGINE 4: BASIC OFFLINE
    # ============================================
    def _offline_response(self, user_message: str) -> str:
        """
        Generate a SMART response using the Medical Knowledge Base.
        Even without an AI model, this gives disease-specific, detailed answers
        by searching through blood_ranges.json and medical_kb.json.
        """
        from backend.report_analyzer import (
            load_medical_kb, load_blood_ranges, extract_symptoms,
            match_diseases, check_emergency_conditions, extract_values_from_text,
            compare_with_ranges
        )

        msg_lower = user_message.lower()

        # -------- 1. EMERGENCY CHECK --------
        emergency = check_emergency_conditions(user_message)
        if emergency.get("is_emergency"):
            return (
                f"EMERGENCY ALERT: {emergency['condition']}\n\n"
                f"IMMEDIATE ACTION: {emergency['immediate_action']}\n\n"
                "CALL EMERGENCY SERVICES (1122) IMMEDIATELY!\n\n"
                "While waiting for help:\n"
                "- Stay calm and keep the patient comfortable\n"
                "- Do not give food or water to an unconscious person\n"
                "- If trained, perform CPR if needed\n"
                "- Keep the patient warm and lying down\n"
                "- Note the time symptoms started\n\n"
                "DO NOT rely on AI advice in emergencies. Call 1122 NOW.\n\n"
                "Disclaimer: This is AI advice. Always follow instructions from emergency services."
            )

        # -------- 2. CHECK FOR LAB VALUES IN THE MESSAGE --------
        extracted_values = extract_values_from_text(user_message)
        if extracted_values:
            findings = compare_with_ranges(extracted_values)
            if findings:
                lines = ["Based on the values you mentioned, here is my analysis:\n"]
                lines.append("LAB RESULTS:")
                lines.append("-" * 40)
                for f in findings:
                    status_label = {"NORMAL": "NORMAL", "LOW": "LOW", "HIGH": "HIGH", "CRITICAL": "CRITICAL"}.get(f["status"], "?")
                    lines.append(f"[{status_label}] {f['test']}: {f['value']} {f['unit']}")
                    lines.append(f"  Normal Range: {f['normal_range']}")
                    if f["status"] != "NORMAL":
                        lines.append(f"  What it means: {f['interpretation']}")
                        lines.append(f"  Recommendation: {f['prevention']}")
                    else:
                        lines.append(f"  Status: Within normal range - Good!")
                    lines.append("")

                # Also match diseases based on findings
                diseases = match_diseases(user_message, findings)
                if diseases:
                    lines.append("POSSIBLE CONDITIONS:")
                    lines.append("-" * 40)
                    for i, d in enumerate(diseases[:2], 1):
                        lines.append(f"{i}. {d['disease']}")
                        lines.append(f"   Prevention: {', '.join(d['prevention'][:3])}")
                    lines.append("")

                lines.append("Disclaimer: This is AI analysis. Always consult a doctor for proper diagnosis.")
                return "\n".join(lines)

        # -------- 3. MATCH DISEASES FROM KNOWLEDGE BASE --------
        symptoms = extract_symptoms(user_message)
        diseases = match_diseases(user_message)

        if diseases:
            top_disease = diseases[0]
            lines = []
            lines.append(f"Based on your question, here is information about {top_disease['disease']}:\n")

            if top_disease.get("symptoms"):
                lines.append("COMMON SYMPTOMS:")
                for s in top_disease["symptoms"][:6]:
                    lines.append(f"  - {s}")
                lines.append("")

            if top_disease.get("causes"):
                lines.append("POSSIBLE CAUSES:")
                for c in top_disease["causes"][:5]:
                    lines.append(f"  - {c}")
                lines.append("")

            if top_disease.get("prevention"):
                lines.append("PREVENTION TIPS:")
                for p in top_disease["prevention"][:5]:
                    lines.append(f"  - {p}")
                lines.append("")

            if top_disease.get("treatment"):
                lines.append("TREATMENT OPTIONS:")
                for t in top_disease["treatment"][:5]:
                    lines.append(f"  - {t}")
                lines.append("")

            lines.append(f"Urgency Level: {top_disease.get('urgency', 'Unknown')}")
            lines.append("")

            # Show other possible conditions if any
            if len(diseases) > 1:
                lines.append("OTHER POSSIBLE CONDITIONS:")
                for d in diseases[1:3]:
                    lines.append(f"  - {d['disease']} (Urgency: {d.get('urgency', 'Unknown')})")
                lines.append("")

            if symptoms:
                lines.append(f"Detected symptoms: {', '.join(s.title() for s in symptoms)}")
                lines.append("")

            lines.append("Disclaimer: This is AI-generated information. Always consult a qualified doctor for proper diagnosis and treatment.")
            return "\n".join(lines)

        # -------- 4. CHECK BLOOD TEST QUESTIONS --------
        blood_ranges = load_blood_ranges()
        for test_key, test_info in blood_ranges.items():
            test_name = test_info.get("name", "").lower()
            test_keywords = [test_key.replace("_", " "), test_name]
            for kw in test_keywords:
                if kw and len(kw) > 2 and kw in msg_lower:
                    lines = [f"Here is information about {test_info.get('name', test_key)}:\n"]
                    lines.append(f"Unit: {test_info.get('unit', 'N/A')}")

                    male_range = test_info.get("male", {})
                    female_range = test_info.get("female", {})
                    if male_range:
                        lines.append(f"Normal Range (Male): {male_range.get('low', '?')} - {male_range.get('high', '?')} {test_info.get('unit', '')}")
                    if female_range:
                        lines.append(f"Normal Range (Female): {female_range.get('low', '?')} - {female_range.get('high', '?')} {test_info.get('unit', '')}")

                    lines.append(f"\nCritical Low: Below {test_info.get('critical_low', '?')} {test_info.get('unit', '')}")
                    lines.append(f"Critical High: Above {test_info.get('critical_high', '?')} {test_info.get('unit', '')}")

                    if test_info.get("high_means"):
                        lines.append(f"\nIf HIGH: {test_info['high_means']}")
                    if test_info.get("low_means"):
                        lines.append(f"If LOW: {test_info['low_means']}")
                    if test_info.get("prevention_high"):
                        lines.append(f"\nTo prevent HIGH levels: {test_info['prevention_high']}")
                    if test_info.get("prevention_low"):
                        lines.append(f"To prevent LOW levels: {test_info['prevention_low']}")

                    lines.append("\nDisclaimer: Normal ranges may vary by lab. Always consult your doctor for interpretation.")
                    return "\n".join(lines)

        # -------- 5. COMMON HEALTH TOPICS (expanded) --------
        health_topics = {
            "fever": (
                "FEVER - Information & Guidance\n\n"
                "What is Fever?\n"
                "A body temperature above 98.6F (37C). Usually indicates your body is fighting an infection.\n\n"
                "Common Causes:\n"
                "- Viral infections (flu, cold, COVID-19)\n"
                "- Bacterial infections (UTI, strep throat)\n"
                "- Inflammatory conditions\n"
                "- Post-vaccination reaction\n\n"
                "What to Do:\n"
                "- Rest and drink plenty of fluids\n"
                "- Take paracetamol (500mg) every 6 hours if needed\n"
                "- Use a cool, damp cloth on forehead\n"
                "- Wear light clothing\n"
                "- Monitor temperature regularly\n\n"
                "When to See a Doctor:\n"
                "- Fever above 103F (39.4C)\n"
                "- Fever lasting more than 3 days\n"
                "- Accompanied by severe headache, stiff neck, or rash\n"
                "- Difficulty breathing\n"
                "- In children under 3 months with any fever\n\n"
                "Disclaimer: Always consult a doctor for persistent or high fever."
            ),
            "headache": (
                "HEADACHE - Information & Guidance\n\n"
                "Common Types:\n"
                "1. Tension Headache: Dull, pressing pain on both sides\n"
                "2. Migraine: Throbbing pain, often one-sided, with nausea\n"
                "3. Cluster Headache: Severe pain around one eye\n"
                "4. Sinus Headache: Pain in forehead/cheeks with congestion\n\n"
                "Common Causes:\n"
                "- Stress and tension\n"
                "- Dehydration\n"
                "- Poor sleep\n"
                "- Eye strain (screen time)\n"
                "- Skipping meals\n"
                "- High blood pressure\n\n"
                "What to Do:\n"
                "- Drink water (dehydration is #1 cause)\n"
                "- Rest in a dark, quiet room\n"
                "- Take paracetamol or ibuprofen\n"
                "- Apply cold pack to forehead\n"
                "- Reduce screen time\n"
                "- Practice relaxation techniques\n\n"
                "When to See a Doctor:\n"
                "- Sudden, severe 'thunderclap' headache\n"
                "- Headache with fever, stiff neck, confusion\n"
                "- After a head injury\n"
                "- Persistent headache lasting days\n\n"
                "Disclaimer: Always consult a doctor for severe or recurring headaches."
            ),
            "cough": (
                "COUGH - Information & Guidance\n\n"
                "Types of Cough:\n"
                "- Dry cough: No mucus, often viral\n"
                "- Wet/productive cough: With mucus, may be bacterial\n"
                "- Chronic cough: Lasting more than 3 weeks\n\n"
                "Common Causes:\n"
                "- Common cold or flu\n"
                "- Allergies\n"
                "- Asthma\n"
                "- Acid reflux (GERD)\n"
                "- Smoking\n"
                "- Post-nasal drip\n\n"
                "What to Do:\n"
                "- Stay hydrated (warm water, soups)\n"
                "- Honey with warm water (natural cough suppressant)\n"
                "- Steam inhalation\n"
                "- Gargle with salt water\n"
                "- Avoid smoking and dusty environments\n"
                "- Use cough lozenges\n\n"
                "When to See a Doctor:\n"
                "- Cough lasting more than 2-3 weeks\n"
                "- Coughing up blood\n"
                "- Difficulty breathing\n"
                "- Chest pain while coughing\n"
                "- High fever with cough\n\n"
                "Disclaimer: Always consult a doctor for persistent cough."
            ),
            "diabetes": (
                "DIABETES - Information & Guidance\n\n"
                "Types:\n"
                "- Type 1: Autoimmune, body doesn't make insulin\n"
                "- Type 2: Body doesn't use insulin properly (most common)\n"
                "- Gestational: During pregnancy\n\n"
                "Key Numbers:\n"
                "- Normal Fasting Sugar: 70-100 mg/dL\n"
                "- Pre-Diabetes: 100-125 mg/dL\n"
                "- Diabetes: Above 126 mg/dL\n"
                "- Normal HbA1c: Below 5.7%\n"
                "- Diabetes HbA1c: Above 6.5%\n\n"
                "Symptoms:\n"
                "- Frequent urination\n"
                "- Excessive thirst\n"
                "- Unexplained weight loss\n"
                "- Blurred vision\n"
                "- Slow wound healing\n"
                "- Fatigue\n\n"
                "Management:\n"
                "- Monitor blood sugar regularly\n"
                "- Follow a balanced, low-sugar diet\n"
                "- Exercise 30 minutes daily\n"
                "- Take medications as prescribed\n"
                "- Regular eye and foot checkups\n"
                "- Reduce stress\n"
                "- Avoid sugary drinks and processed foods\n\n"
                "Disclaimer: Always follow your doctor's treatment plan."
            ),
            "blood pressure": (
                "BLOOD PRESSURE - Information & Guidance\n\n"
                "Blood Pressure Categories:\n"
                "- Normal: Below 120/80 mmHg\n"
                "- Elevated: 120-129 / less than 80\n"
                "- High (Stage 1): 130-139 / 80-89\n"
                "- High (Stage 2): 140+ / 90+\n"
                "- Crisis: Above 180/120 (call doctor immediately)\n\n"
                "Symptoms of High BP:\n"
                "- Often no symptoms (silent killer)\n"
                "- Severe headache\n"
                "- Shortness of breath\n"
                "- Nosebleeds\n"
                "- Dizziness\n\n"
                "Prevention & Management:\n"
                "- Reduce salt intake (less than 5g/day)\n"
                "- Exercise regularly (30 min/day)\n"
                "- Maintain healthy weight\n"
                "- Limit alcohol and quit smoking\n"
                "- Eat fruits, vegetables, whole grains\n"
                "- Manage stress\n"
                "- Take prescribed medications regularly\n"
                "- Monitor BP at home\n\n"
                "Disclaimer: Always consult your doctor for blood pressure management."
            ),
            "weight": (
                "WEIGHT MANAGEMENT - Information & Guidance\n\n"
                "BMI Categories:\n"
                "- Underweight: Below 18.5\n"
                "- Normal: 18.5 - 24.9\n"
                "- Overweight: 25 - 29.9\n"
                "- Obese: 30+\n\n"
                "Healthy Weight Loss Tips:\n"
                "- Eat smaller portions\n"
                "- Drink water before meals\n"
                "- Include protein in every meal\n"
                "- Reduce sugar and refined carbs\n"
                "- Exercise 30-60 minutes daily\n"
                "- Get 7-8 hours of sleep\n"
                "- Avoid crash diets\n\n"
                "Healthy Weight Gain Tips:\n"
                "- Eat more frequent meals\n"
                "- Include healthy fats (nuts, avocado)\n"
                "- Strength training exercises\n"
                "- Increase protein intake\n"
                "- Drink smoothies and shakes\n\n"
                "Disclaimer: Consult a dietitian for a personalized plan."
            ),
            "sleep": (
                "SLEEP HEALTH - Information & Guidance\n\n"
                "How Much Sleep Do You Need?\n"
                "- Adults: 7-9 hours\n"
                "- Teens: 8-10 hours\n"
                "- Children: 9-12 hours\n\n"
                "Common Sleep Problems:\n"
                "- Insomnia: Difficulty falling/staying asleep\n"
                "- Sleep apnea: Breathing stops during sleep\n"
                "- Restless leg syndrome\n\n"
                "Tips for Better Sleep:\n"
                "- Keep a consistent sleep schedule\n"
                "- Avoid screens 1 hour before bed\n"
                "- Keep room cool and dark\n"
                "- Avoid caffeine after 2 PM\n"
                "- Exercise regularly (but not near bedtime)\n"
                "- Avoid heavy meals before sleep\n"
                "- Try relaxation techniques\n\n"
                "Disclaimer: See a sleep specialist if problems persist."
            ),
            "vitamin": (
                "VITAMINS & NUTRITION - Information & Guidance\n\n"
                "Essential Vitamins:\n"
                "- Vitamin D: Bone health, immunity (sunlight, eggs, fish)\n"
                "- Vitamin C: Immunity, skin (citrus, peppers, guava)\n"
                "- Vitamin B12: Energy, nerve health (meat, dairy, eggs)\n"
                "- Iron: Blood health (red meat, spinach, lentils)\n"
                "- Calcium: Bones, teeth (milk, yogurt, cheese)\n"
                "- Zinc: Immunity, healing (nuts, seeds, meat)\n\n"
                "Signs of Deficiency:\n"
                "- Vitamin D: Bone pain, fatigue, muscle weakness\n"
                "- Iron: Pale skin, tiredness, dizziness\n"
                "- B12: Numbness, fatigue, memory problems\n"
                "- Vitamin C: Slow healing, bleeding gums\n\n"
                "Tips:\n"
                "- Eat a balanced, colorful diet\n"
                "- Get 15-20 minutes of sunlight daily\n"
                "- Take supplements only if doctor recommends\n"
                "- Get blood tests done regularly\n\n"
                "Disclaimer: Always consult a doctor before starting supplements."
            ),
        }

        for keyword, response in health_topics.items():
            if keyword in msg_lower:
                return response

        # -------- 6. GREETING / GENERAL --------
        greetings = ["hello", "hi", "hey", "salam", "assalam", "good morning", "good evening"]
        if any(g in msg_lower for g in greetings):
            return (
                "Hello! I'm your AI Health Assistant.\n\n"
                "I can help you with:\n"
                "- Information about diseases and conditions\n"
                "- Understanding lab test results (blood tests, etc.)\n"
                "- Prevention tips and healthy lifestyle advice\n"
                "- First-aid guidance\n"
                "- Medication information\n\n"
                "Try asking me things like:\n"
                "- 'What is dengue fever?'\n"
                "- 'My sugar level is 250'\n"
                "- 'What are symptoms of diabetes?'\n"
                "- 'My platelet count is 80000'\n"
                "- 'How to reduce blood pressure?'\n\n"
                "Ask me anything about your health!"
            )

        # -------- 7. TRULY UNKNOWN QUERY --------
        # Still try to find SOMETHING from the KB
        kb = load_medical_kb()
        all_diseases = kb.get("diseases", [])
        for disease in all_diseases:
            name_words = disease.get("name", "").lower().split()
            for word in name_words:
                if len(word) > 3 and word in msg_lower:
                    lines = [f"Here is information about {disease['name']}:\n"]
                    if disease.get("symptoms"):
                        lines.append("Symptoms: " + ", ".join(disease["symptoms"][:5]))
                    if disease.get("causes"):
                        lines.append("Causes: " + ", ".join(disease["causes"][:4]))
                    if disease.get("prevention"):
                        lines.append("\nPrevention:")
                        for p in disease["prevention"][:4]:
                            lines.append(f"  - {p}")
                    if disease.get("treatment"):
                        lines.append("\nTreatment:")
                        for t in disease["treatment"][:4]:
                            lines.append(f"  - {t}")
                    lines.append(f"\nUrgency: {disease.get('urgency', 'Unknown')}")
                    lines.append("\nDisclaimer: Always consult a doctor for proper diagnosis.")
                    return "\n".join(lines)

        # -------- 8. FALLBACK --------
        return (
            f"Thank you for your question.\n\n"
            "I searched my medical knowledge base but couldn't find specific information "
            f"about: \"{user_message}\"\n\n"
            "Here are some things you can try:\n"
            "- Describe your symptoms in more detail\n"
            "- Ask about a specific disease (e.g., 'What is dengue?')\n"
            "- Ask about a lab test (e.g., 'What is normal hemoglobin?')\n"
            "- Provide lab values (e.g., 'My sugar is 250')\n\n"
            "General Health Tips:\n"
            "- Stay hydrated (8 glasses of water daily)\n"
            "- Get 7-8 hours of sleep\n"
            "- Exercise for 30 minutes daily\n"
            "- Eat a balanced diet with fruits and vegetables\n"
            "- Manage stress through relaxation techniques\n\n"
            "Disclaimer: Always consult a real doctor for medical decisions."
        )

    def get_conversation_history(self, conversation_id: str) -> list:
        """Get message history for a conversation."""
        conv = self.conversations.get(conversation_id, {})
        return conv.get("messages", [])

    def get_all_conversations(self) -> list:
        """Get list of all conversations."""
        summaries = []
        for conv_id, conv in self.conversations.items():
            messages = conv.get("messages", [])
            first_msg = messages[0]["content"] if messages else "Empty"
            summaries.append({
                "id": conv_id,
                "preview": first_msg[:100],
                "message_count": len(messages),
                "created_at": conv.get("created_at", 0),
                "updated_at": conv.get("updated_at", 0)
            })
        return sorted(summaries, key=lambda x: x["updated_at"], reverse=True)

    def clear_conversation(self, conversation_id: str):
        """Clear a specific conversation."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            self._save_conversations()
        return {"success": True}


# ============================================
# GLOBAL INSTANCE
# ============================================
_chat_manager = None

def get_chat_manager() -> ChatManager:
    global _chat_manager
    if _chat_manager is None:
        _chat_manager = ChatManager()
    return _chat_manager
