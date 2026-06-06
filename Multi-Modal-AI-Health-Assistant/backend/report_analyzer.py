"""
Report Analyzer Module
======================
Extracts medical values from reports and compares them
with standard reference ranges to detect abnormalities.
Also matches symptoms against the medical knowledge base.
"""

import json
import os
import re

# ============================================
# DATA LOADING
# ============================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

BLOOD_RANGES_FILE = os.path.join(DATA_DIR, "blood_ranges.json")
MEDICAL_KB_FILE = os.path.join(DATA_DIR, "medical_kb.json")


def _load_json(filepath):
    """Safely load a JSON file."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def load_blood_ranges():
    return _load_json(BLOOD_RANGES_FILE)


def load_medical_kb():
    return _load_json(MEDICAL_KB_FILE)


# ============================================
# VALUE EXTRACTION (improved for natural language)
# ============================================
TEST_PATTERNS = {
    "hemoglobin": [
        r"(?:hemoglobin|hb|hgb)\s*(?:count)?\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "wbc": [
        r"(?:wbc|white\s*blood\s*cell|leucocyte|leukocyte)\s*(?:count)?\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "rbc": [
        r"(?:rbc|red\s*blood\s*cell|erythrocyte)\s*(?:count)?\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "platelets": [
        r"(?:platelet|plt)\s*(?:count)?\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "fasting_glucose": [
        r"(?:fasting\s*(?:blood\s*)?(?:glucose|sugar)|fbg|fbs)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
        r"(?:glucose|blood\s*sugar|sugar)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "hba1c": [
        r"(?:hba1c|glycated\s*hemoglobin|a1c)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "cholesterol_total": [
        r"(?:total\s*cholesterol|cholesterol)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "ldl": [
        r"(?:ldl|low\s*density)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "hdl": [
        r"(?:hdl|high\s*density)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "triglycerides": [
        r"(?:triglyceride|tg)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "alt": [
        r"(?:alt|sgpt|alanine\s*aminotransferase)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "ast": [
        r"(?:ast|sgot|aspartate\s*aminotransferase)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "bilirubin_total": [
        r"(?:total\s*bilirubin|bilirubin)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "creatinine": [
        r"(?:creatinine|creat)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "bun": [
        r"(?:bun|blood\s*urea\s*nitrogen|urea)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "tsh": [
        r"(?:tsh|thyroid\s*stimulating)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "vitamin_d": [
        r"(?:vitamin\s*d|25\s*oh\s*d|25-hydroxyvitamin)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "uric_acid": [
        r"(?:uric\s*acid)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "esr": [
        r"(?:esr|erythrocyte\s*sedimentation)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
    "iron": [
        r"(?:serum\s*iron|iron)\s*(?:level|value|is|was|of|=|:|-|\s)*?(\d+\.?\d*)",
    ],
}


def extract_values_from_text(report_text: str) -> dict:
    """Extract medical test values from text (handles natural language)."""
    extracted = {}
    text_lower = report_text.lower()

    for test_name, patterns in TEST_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    value = float(match.group(1))
                    extracted[test_name] = value
                    break
                except (ValueError, IndexError):
                    continue

    return extracted


# ============================================
# VALUE COMPARISON WITH NORMAL RANGES
# ============================================
def compare_with_ranges(extracted_values: dict, gender: str = "male") -> list:
    """Compare extracted values with normal reference ranges."""
    ranges = load_blood_ranges()
    findings = []

    for test_key, value in extracted_values.items():
        if test_key not in ranges:
            continue

        test_info = ranges[test_key]
        gender_key = gender.lower() if gender.lower() in ["male", "female"] else "male"
        normal_range = test_info.get(gender_key, test_info.get("male", {}))
        low = normal_range.get("low", 0)
        high = normal_range.get("high", 999999)
        critical_low = test_info.get("critical_low", 0)
        critical_high = test_info.get("critical_high", 999999)

        if value <= critical_low or value >= critical_high:
            status = "CRITICAL"
        elif value < low:
            status = "LOW"
        elif value > high:
            status = "HIGH"
        else:
            status = "NORMAL"

        finding = {
            "test": test_info.get("name", test_key),
            "value": value,
            "unit": test_info.get("unit", ""),
            "normal_range": f"{low} - {high}",
            "status": status,
            "interpretation": "",
            "prevention": ""
        }

        if status == "LOW" or (status == "CRITICAL" and value < low):
            finding["interpretation"] = test_info.get("low_means", "Below normal range")
            finding["prevention"] = test_info.get("prevention_low", "Consult your doctor")
        elif status == "HIGH" or (status == "CRITICAL" and value > high):
            finding["interpretation"] = test_info.get("high_means", "Above normal range")
            finding["prevention"] = test_info.get("prevention_high", "Consult your doctor")
        else:
            finding["interpretation"] = "Within normal range"
            finding["prevention"] = "Continue healthy lifestyle"

        findings.append(finding)

    return findings


# ============================================
# SYMPTOM EXTRACTION (new - for natural language)
# ============================================
COMMON_SYMPTOMS = [
    "headache", "fever", "high fever", "low fever", "cough", "sore throat",
    "body ache", "body aching", "fatigue", "tiredness", "weakness",
    "nausea", "vomiting", "diarrhea", "constipation", "abdominal pain",
    "chest pain", "back pain", "joint pain", "muscle pain",
    "shortness of breath", "difficulty breathing", "breathing difficulty",
    "dizziness", "fainting", "blurred vision", "weight loss", "weight gain",
    "skin rash", "itching", "swelling", "numbness", "tingling",
    "frequent urination", "blood in urine", "blood in stool",
    "loss of appetite", "insomnia", "night sweats", "palpitations",
    "bruising", "bleeding", "wheezing", "runny nose", "sneezing",
    "ear pain", "eye pain", "toothache", "cold", "flu",
    "pale skin", "jaundice", "yellow eyes", "dark urine",
    "mucus", "phlegm", "congestion", "lungs", "chest tightness"
]


def extract_symptoms(text: str) -> list:
    """Extract recognized symptoms from natural language text."""
    text_lower = text.lower()
    found = []
    for symptom in COMMON_SYMPTOMS:
        if symptom in text_lower:
            found.append(symptom)
    return found


# ============================================
# DISEASE MATCHING (improved)
# ============================================
def match_diseases(text: str, findings: list = None) -> list:
    """
    Match symptoms/findings against the medical knowledge base.
    Uses both keyword matching AND individual word matching for better recall.
    """
    kb = load_medical_kb()
    diseases = kb.get("diseases", [])
    text_lower = text.lower()
    detected_symptoms = extract_symptoms(text)

    matched = []
    for disease in diseases:
        score = 0

        # Match full keywords (phrase match)
        for keyword in disease.get("keywords", []):
            if keyword.lower() in text_lower:
                score += 2

        # Match disease symptoms against detected symptoms
        for symptom in disease.get("symptoms", []):
            symptom_lower = symptom.lower()
            for detected in detected_symptoms:
                if detected in symptom_lower or symptom_lower in text_lower:
                    score += 1
                    break

        # Match disease name words
        disease_words = disease.get("name", "").lower().split()
        for word in disease_words:
            if len(word) > 3 and word in text_lower:
                score += 1

        # Check findings for abnormal values
        if findings:
            for finding in findings:
                if finding["status"] in ["HIGH", "LOW", "CRITICAL"]:
                    test_name_lower = finding.get("test", "").lower()
                    for related_test in disease.get("related_tests", []):
                        if related_test.lower() in test_name_lower or test_name_lower in related_test.lower():
                            score += 3

        if score > 0:
            matched.append({
                "disease": disease["name"],
                "category": disease.get("category", ""),
                "match_score": score,
                "symptoms": disease.get("symptoms", []),
                "causes": disease.get("causes", []),
                "prevention": disease.get("prevention", []),
                "treatment": disease.get("treatment", []),
                "urgency": disease.get("urgency", "LOW")
            })

    matched.sort(key=lambda x: x["match_score"], reverse=True)
    return matched[:5]


# ============================================
# CHECK FOR EMERGENCIES
# ============================================
def check_emergency_conditions(text: str) -> dict:
    """Check if text contains emergency conditions."""
    kb = load_medical_kb()
    emergencies = kb.get("emergency_conditions", [])
    text_lower = text.lower()

    for emergency in emergencies:
        for keyword in emergency.get("keywords", []):
            if keyword.lower() in text_lower:
                return {
                    "is_emergency": True,
                    "condition": emergency["condition"],
                    "immediate_action": emergency["immediate_action"],
                    "urgency": emergency.get("urgency", "CRITICAL")
                }

    return {"is_emergency": False}


# ============================================
# COMPREHENSIVE REPORT ANALYSIS
# ============================================
def analyze_report_text(report_text: str, question: str = "", gender: str = "male") -> dict:
    """
    Comprehensive report analysis:
    1. Extract values from text
    2. Compare with normal ranges
    3. Extract symptoms from natural language
    4. Match possible diseases
    5. Check for emergencies
    6. Generate detailed summary
    """
    combined_text = f"{report_text} {question}".strip()

    # Step 1: Extract values
    extracted_values = extract_values_from_text(combined_text)

    # Step 2: Compare with ranges
    findings = compare_with_ranges(extracted_values, gender)

    # Step 3: Extract symptoms
    symptoms = extract_symptoms(combined_text)

    # Step 4: Match diseases
    diseases = match_diseases(combined_text, findings)

    # Step 5: Check emergencies
    emergency = check_emergency_conditions(combined_text)

    # Step 6: Determine overall urgency
    urgency = "NORMAL"
    for finding in findings:
        if finding["status"] == "CRITICAL":
            urgency = "CRITICAL"
            break
        elif finding["status"] in ["HIGH", "LOW"] and urgency != "CRITICAL":
            urgency = "WARNING"

    if emergency.get("is_emergency"):
        urgency = "CRITICAL"

    for disease in diseases:
        if disease["urgency"] == "CRITICAL":
            urgency = "CRITICAL"
            break
        elif disease["urgency"] == "HIGH" and urgency == "NORMAL":
            urgency = "WARNING"

    # If symptoms found but no disease matched, at least flag as warning
    if symptoms and not diseases and urgency == "NORMAL":
        urgency = "WARNING"

    # Step 7: Generate summary
    summary = _generate_summary(findings, diseases, emergency, extracted_values, symptoms)

    return {
        "success": True,
        "extracted_values": extracted_values,
        "findings": findings,
        "detected_symptoms": symptoms,
        "possible_diseases": diseases,
        "emergency": emergency,
        "urgency": urgency,
        "summary": summary,
        "values_found": len(extracted_values),
        "abnormal_count": sum(1 for f in findings if f["status"] != "NORMAL")
    }


def _generate_summary(findings: list, diseases: list, emergency: dict,
                       extracted_values: dict, symptoms: list = None) -> str:
    """Generate a human-readable summary of the analysis."""
    lines = []

    # Emergency warning
    if emergency.get("is_emergency"):
        lines.append(f"EMERGENCY: {emergency['condition']}")
        lines.append(f"Immediate Action: {emergency['immediate_action']}")
        lines.append("")

    # Detected Symptoms
    if symptoms:
        lines.append("DETECTED SYMPTOMS:")
        lines.append("-" * 40)
        lines.append(", ".join(s.title() for s in symptoms))
        lines.append("")

    # Lab Findings
    if findings:
        lines.append("LAB RESULTS ANALYSIS:")
        lines.append("-" * 40)
        for f in findings:
            status_icon = {"NORMAL": "[OK]", "LOW": "[LOW]", "HIGH": "[HIGH]", "CRITICAL": "[CRITICAL]"}.get(f["status"], "[?]")
            lines.append(f"{status_icon} {f['test']}: {f['value']} {f['unit']} "
                        f"(Normal: {f['normal_range']}) - {f['status']}")
            if f["status"] != "NORMAL":
                lines.append(f"   -> {f['interpretation']}")
                lines.append(f"   Tip: {f['prevention']}")
        lines.append("")

    # Possible diseases
    if diseases:
        lines.append("POSSIBLE CONDITIONS:")
        lines.append("-" * 40)
        for i, d in enumerate(diseases[:3], 1):
            lines.append(f"{i}. {d['disease']} (Urgency: {d['urgency']})")
            if d["symptoms"]:
                lines.append(f"   Common Symptoms: {', '.join(d['symptoms'][:5])}")
            if d["causes"]:
                lines.append(f"   Possible Causes: {', '.join(d['causes'][:3])}")
            if d["prevention"]:
                lines.append(f"   Prevention: {', '.join(d['prevention'][:3])}")
            if d["treatment"]:
                lines.append(f"   Treatment: {', '.join(d['treatment'][:3])}")
            lines.append("")

    # Nothing found at all
    if not findings and not diseases and not symptoms:
        lines.append("No specific medical values or symptoms were detected.")
        lines.append("Please describe your symptoms in more detail or upload a medical report.")
        lines.append("")

    # Disclaimer
    lines.append("DISCLAIMER: This is AI-generated analysis for informational purposes only.")
    lines.append("Always consult a qualified medical professional for proper diagnosis and treatment.")

    return "\n".join(lines)
