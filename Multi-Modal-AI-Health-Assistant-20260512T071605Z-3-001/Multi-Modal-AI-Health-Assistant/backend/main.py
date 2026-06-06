"""
Multi-Modal AI Health Assistant - Backend Server
=================================================
FastAPI server with endpoints for:
- Medical report analysis (images, PDFs, text)
- AI chat (offline via Ollama)
- Reinforcement Learning feedback & metrics
- Emergency handling
"""

import os
import shutil
import base64
import uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from backend.ollama_engine import analyze_medical_data, check_ollama_status
from backend.emergency_handler import handle_emergency
from backend.rl_model import (
    get_agent, update_rl_model, classify_state,
    select_action, get_rl_metrics, load_rl_data
)
from backend.chat_handler import get_chat_manager
from backend.pdf_processor import extract_text_and_images
from backend.report_analyzer import analyze_report_text

# ============================================
# APP INITIALIZATION
# ============================================
app = FastAPI(
    title="Multi-Modal AI Health Assistant",
    description="Offline AI-powered medical analysis with Reinforcement Learning",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("temp", exist_ok=True)
os.makedirs("data", exist_ok=True)


# ============================================
# PYDANTIC MODELS
# ============================================
class FeedbackRequest(BaseModel):
    diagnosis_id: str
    is_accurate: bool
    comments: Optional[str] = None
    state: Optional[str] = "general_query"
    action: Optional[str] = "combined_approach"


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    model: Optional[str] = None


# ============================================
# ENDPOINT: ANALYZE REPORT
# ============================================
@app.post("/api/analyze")
async def analyze_report(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    patient_name: str = Form(...),
    emergency_contact: str = Form(""),
    latitude: Optional[str] = Form(None),
    longitude: Optional[str] = Form(None),
    question: str = Form(""),
    gender: str = Form("male")
):
    """Analyze medical report (image/PDF/text) with RL-guided strategy."""
    try:
        file_path = None
        extracted_text = ""
        image_base64 = None
        file_type = ""

        # Process uploaded file
        if file and file.filename:
            file_extension = file.filename.split(".")[-1].lower()
            file_type = file_extension
            file_path = f"temp/{file.filename}"

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            if file_extension == "pdf":
                extracted_text, first_image = extract_text_and_images(file_path)
                image_base64 = first_image
            elif file_extension in ["jpg", "jpeg", "png", "webp"]:
                with open(file_path, "rb") as image_file:
                    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")
            else:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": "Unsupported file format. Use JPG, PNG, WEBP, or PDF."}
                )

        # If no file text extracted, use the question as text context
        # so the knowledge base can analyze symptom descriptions
        text_for_analysis = extracted_text if extracted_text.strip() else question

        # RL: Classify state and select action
        rl_state = classify_state(text_for_analysis, file_type, question)
        rl_action = select_action(rl_state)

        # Run analysis with RL-selected strategy
        analysis_result, urgency_level, diagnosis_id = analyze_medical_data(
            image_b64=image_base64,
            text_context=text_for_analysis,
            question=question,
            action=rl_action
        )

        # Also get structured report analysis if we have text
        report_analysis = None
        if text_for_analysis.strip():
            report_analysis = analyze_report_text(text_for_analysis, question, gender)

        # Handle emergency
        if urgency_level == "CRITICAL" and emergency_contact:
            try:
                background_tasks.add_task(
                    handle_emergency,
                    patient_name=patient_name,
                    emergency_contact=emergency_contact,
                    analysis_text=analysis_result,
                    latitude=latitude,
                    longitude=longitude
                )
            except Exception:
                pass  # Don't fail analysis because of email issues

        # Cleanup temp file
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

        return {
            "success": True,
            "patient_name": patient_name,
            "diagnosis_id": diagnosis_id,
            "analysis": analysis_result,
            "urgency_level": urgency_level,
            "rl_state": rl_state,
            "rl_action": rl_action,
            "report_details": report_analysis if report_analysis else None,
            "location_received": bool(latitude and longitude)
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ============================================
# ENDPOINT: RL FEEDBACK
# ============================================
@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Submit user feedback to update RL model."""
    try:
        agent = get_agent()
        result = agent.process_feedback(
            diagnosis_id=feedback.diagnosis_id,
            is_accurate=feedback.is_accurate,
            state=feedback.state,
            action=feedback.action,
            comments=feedback.comments
        )
        return {"success": True, "rl_update": result}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ============================================
# ENDPOINT: RL METRICS
# ============================================
@app.get("/api/rl/metrics")
async def rl_metrics():
    """Get RL agent metrics for dashboard."""
    try:
        metrics = get_rl_metrics()
        return {"success": True, "metrics": metrics}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ============================================
# ENDPOINT: CHAT
# ============================================
@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Send a chat message and get AI response."""
    try:
        chat_manager = get_chat_manager()
        conversation_id = request.conversation_id or str(uuid.uuid4())

        result = chat_manager.send_message(
            conversation_id=conversation_id,
            user_message=request.message,
            model=request.model
        )
        return result
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/chat/history/{conversation_id}")
async def chat_history(conversation_id: str):
    """Get chat history for a conversation."""
    try:
        chat_manager = get_chat_manager()
        messages = chat_manager.get_conversation_history(conversation_id)
        return {"success": True, "messages": messages}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.delete("/api/chat/{conversation_id}")
async def clear_chat(conversation_id: str):
    """Clear a chat conversation."""
    try:
        chat_manager = get_chat_manager()
        result = chat_manager.clear_conversation(conversation_id)
        return result
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ============================================
# ENDPOINT: SYSTEM STATUS
# ============================================
@app.get("/api/status")
async def system_status():
    """Check system status (Ollama, models, RL agent)."""
    try:
        ollama = check_ollama_status()
        rl_data = load_rl_data()
        return {
            "success": True,
            "ollama": ollama,
            "rl_feedback_count": rl_data.get("total_feedback", 0),
            "version": "2.0.0"
        }
    except Exception as e:
        return {"success": True, "ollama": {"running": False}, "error": str(e)}


# ============================================
# SERVE FRONTEND
# ============================================
os.makedirs("frontend", exist_ok=True)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
