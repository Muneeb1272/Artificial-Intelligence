import streamlit as st
import sys
import os
import uuid
import base64
from PIL import Image
import io

# ============================================
# PATH SETUP
# ============================================
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ============================================
# IMPORTS
# ============================================
from config.settings import APP_NAME, APP_VERSION
from core.gemini_engine import (
    analyze_image_with_text,
    analyze_text_only,
    detect_urgency_level
)
from core.emergency_handler import handle_emergency
from core.report_processor import (
    load_and_validate_image,
    save_temp_image,
    delete_temp_image,
    resize_image_if_needed,
    extract_pdf_report
)
from backend.rl_model import load_rl_data, update_rl_model
from ui.styles import get_main_styles
from ui.components import (
    render_header,
    render_sidebar,
    render_urgency_banner,
    render_emergency_alert,
    render_analysis_result,
    render_disclaimer
)
from utils.helpers import (
    validate_patient_name,
    get_file_size_mb,
    format_timestamp
)

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title=APP_NAME,
    page_icon="Hospital",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# LOAD STYLES
# ============================================
st.markdown(get_main_styles(), unsafe_allow_html=True)

# ============================================
# RENDER SIDEBAR
# ============================================
render_sidebar()

# ============================================
# RENDER HEADER
# ============================================
render_header()

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []
if "total_analyses" not in st.session_state:
    st.session_state.total_analyses = 0

# ============================================
# MAIN CONTENT - TWO COLUMNS
# ============================================
col1, col2 = st.columns([1, 1], gap="large")

# ============================================
# LEFT COLUMN - INPUT SECTION
# ============================================
with col1:
    st.markdown("""
    <div class="info-card">
        <h3 style="color: #4a9eff; margin-top: 0;">Patient Information</h3>
    </div>
    """, unsafe_allow_html=True)

    patient_name = st.text_input(
        "Patient Full Name",
        placeholder="Enter patient full name...",
        help="Enter the name of the patient for the report"
    )

    emergency_contact = st.text_input(
        "Emergency Contact Email",
        placeholder="doctor@example.com or family@example.com",
        help="Email address where emergency alerts will be sent"
    )

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card">
        <h3 style="color: #4a9eff; margin-top: 0;">Upload Medical Image / Report</h3>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload Image or Medical Report",
        type=["jpg", "jpeg", "png", "webp", "pdf"],
        help="Supported formats: JPG, JPEG, PNG, WEBP, PDF | Max size: 10MB"
    )

    if uploaded_file is not None:
        file_size = get_file_size_mb(uploaded_file)
        st.success(f"File uploaded: {uploaded_file.name} ({file_size} MB)")

        extension = os.path.splitext(uploaded_file.name)[1].lower()
        if extension in [".jpg", ".jpeg", ".png", ".webp"]:
            preview_image = Image.open(uploaded_file)
            st.image(
                preview_image,
                caption="Uploaded Medical Image",
                use_column_width=True
            )
            uploaded_file.seek(0)
        elif extension == ".pdf":
            st.info("PDF report uploaded. Text and first image (if available) will be extracted.")
        else:
            st.warning("Uploaded file format is not fully supported for preview.")

    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card">
        <h3 style="color: #4a9eff; margin-top: 0;">Your Question (Optional)</h3>
    </div>
    """, unsafe_allow_html=True)

    user_query = st.text_area(
        "Ask a specific question about your condition",
        placeholder="Example: What does this rash indicate? Is this blood report normal?",
        height=120,
        help="Optional: Ask a specific question about your uploaded image or condition"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    analyze_button = st.button(
        "Analyze Now",
        use_container_width=True,
        type="primary"
    )

# ============================================
# RIGHT COLUMN - RESULTS SECTION
# ============================================
with col2:
    st.markdown("""
    <div class="info-card">
        <h3 style="color: #4a9eff; margin-top: 0;">Analysis Results</h3>
    </div>
    """, unsafe_allow_html=True)

    if analyze_button:

        name_validation = validate_patient_name(patient_name)
        if not name_validation["valid"]:
            st.error(f"Error {name_validation['error']}")

        elif uploaded_file is None and not user_query.strip():
            st.error("Error Please upload an image or enter a question.")

        else:
            with st.spinner("AI is analyzing... Please wait..."):

                temp_image_path = None
                analysis_result = None
                diagnosis_id = str(uuid.uuid4())

                try:
                    if uploaded_file is not None:
                        extension = os.path.splitext(uploaded_file.name)[1].lower()

                        if extension in [".jpg", ".jpeg", ".png", ".webp"]:
                            uploaded_file.seek(0)
                            image_result = load_and_validate_image(uploaded_file)

                            if not image_result["success"]:
                                st.error(f"Error {image_result['error']}")
                            else:
                                image = image_result["image"]
                                image = resize_image_if_needed(image)

                                uploaded_file.seek(0)
                                temp_image_path = save_temp_image(
                                    uploaded_file,
                                    patient_name
                                )

                                uploaded_file.seek(0)
                                analysis_result = analyze_image_with_text(
                                    image=image,
                                    user_query=user_query
                                )

                        elif extension == ".pdf":
                            uploaded_file.seek(0)
                            pdf_result = extract_pdf_report(uploaded_file)

                            if not pdf_result["success"]:
                                st.error(f"Error {pdf_result['error']}")
                            else:
                                extracted_text = pdf_result["text"]
                                if extracted_text.strip():
                                    st.markdown("**Extracted report preview:**")
                                    st.text_area(
                                        "PDF text preview",
                                        extracted_text[:1500],
                                        height=220,
                                        disabled=True
                                    )

                                if pdf_result.get("image_bytes"):
                                    pdf_image = Image.open(io.BytesIO(pdf_result["image_bytes"]))
                                    st.image(
                                        pdf_image,
                                        caption="First image extracted from PDF",
                                        use_column_width=True
                                    )

                                prompt_text = extracted_text
                                if user_query.strip():
                                    prompt_text += f"\n\nQuestion: {user_query}"
                                analysis_result = analyze_text_only(prompt_text)

                        else:
                            st.error("Unsupported file format. Please upload JPG, PNG, WEBP, or PDF.")
                            analysis_result = None

                    else:
                        analysis_result = analyze_text_only(user_query)

                    if analysis_result and analysis_result["success"]:

                        analysis_text = analysis_result["analysis"]

                        urgency_level = detect_urgency_level(analysis_text)

                        from core.emergency_handler import (
                            get_urgency_color,
                            get_urgency_emoji
                        )
                        urgency_color = get_urgency_color(urgency_level)
                        urgency_emoji = get_urgency_emoji(urgency_level)

                        render_urgency_banner(
                            urgency_level,
                            urgency_emoji,
                            urgency_color
                        )

                        emergency_result = handle_emergency(
                            patient_name=patient_name,
                            analysis_text=analysis_text,
                            urgency_level=urgency_level,
                            image_path=temp_image_path,
                            emergency_contact=emergency_contact
                        )

                        if emergency_result["emergency_detected"]:
                            render_emergency_alert(
                                alert_message=emergency_result["alert_message"],
                                email_sent=emergency_result["email_sent"],
                                email_message=emergency_result["email_message"]
                            )

                        render_analysis_result(analysis_text)

                        st.markdown("### Feedback")
                        feedback_col1, feedback_col2 = st.columns(2)
                        with feedback_col1:
                            if st.button("👍 Accurate", key=f"feedback_yes_{diagnosis_id}"):
                                update_rl_model(diagnosis_id, True, user_query)
                                st.success("Thanks! Your feedback is saved.")
                        with feedback_col2:
                            if st.button("👎 Inaccurate", key=f"feedback_no_{diagnosis_id}"):
                                update_rl_model(diagnosis_id, False, user_query)
                                st.warning("Feedback recorded.")

                        rl_stats = load_rl_data()
                        st.info(
                            f"Feedback total: {rl_stats['total_feedback']} | "
                            f"Positive: {rl_stats['positive_feedback']} | "
                            f"Negative: {rl_stats['negative_feedback']}"
                        )

                        render_disclaimer()

                        st.session_state.total_analyses += 1
                        st.session_state.analysis_history.append({
                            "patient": patient_name,
                            "urgency": urgency_level,
                            "time": format_timestamp()
                        })

                        if temp_image_path:
                            delete_temp_image(temp_image_path)

                    elif analysis_result:
                        st.error(f"Error Analysis failed: {analysis_result['error']}")

                except Exception as e:
                    st.error(f"Error An error occurred: {str(e)}")
                    if temp_image_path:
                        delete_temp_image(temp_image_path)

    else:
        st.markdown("""
        <div style="
            text-align: center;
            padding: 60px 20px;
            color: #555;
        ">
            <div style="font-size: 5rem;">Hospital</div>
            <h3 style="color: #4a9eff; margin: 20px 0 10px 0;">
                Ready for Analysis
            </h3>
            <p style="color: #666; font-size: 1rem;">
                Fill in patient details, upload a medical image or report,
                and click <strong style="color: #4a9eff;">Analyze Now</strong>
                to get instant AI-powered health insights.
            </p>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# BOTTOM SECTION - ANALYSIS HISTORY
# ============================================
if st.session_state.total_analyses > 0:
    st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)
    st.markdown("""
    <div class="info-card">
        <h3 style="color: #4a9eff; margin-top: 0;">Session History</h3>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    for i, record in enumerate(st.session_state.analysis_history[-4:]):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="info-card" style="text-align: center;">
                <p style="color: #4a9eff; margin: 0; font-weight: bold;">
                    {record['patient']}
                </p>
                <p style="color: #aaa; margin: 5px 0; font-size: 0.8rem;">
                    {record['time']}
                </p>
                <span class="badge-{record['urgency'].lower()}">
                    {record['urgency']}
                </span>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="
    text-align: center;
    padding: 20px;
    border-top: 1px solid #2a4a7a;
    color: #555;
    font-size: 0.85rem;
">
    <p style="margin: 0;">
        Hospital <strong style="color: #4a9eff;">Multi-Modal AI Health Assistant</strong>
        | Powered by Local AI Health Assistant
    </p>
    <p style="margin: 5px 0 0 0;">
        Warning For informational purposes only.
        Always consult a qualified medical professional.
        | Emergency: 1122
    </p>
</div>
""", unsafe_allow_html=True)
