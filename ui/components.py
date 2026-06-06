import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import APP_NAME, APP_VERSION


def render_header():
    """
    Renders the main app header
    """
    st.markdown(f"""
    <div class="app-header">
        <h1>Hospital {APP_NAME}</h1>
        <p>AI-Powered Medical Image & Report Analysis System | v{APP_VERSION}</p>
        <p style="color: #7ab3e8; font-size: 0.9rem;">
            Upload medical images, skin conditions, or reports for instant AI analysis
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """
    Renders the sidebar with app info and instructions
    """
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-header" style="background: linear-gradient(135deg, #1a56a0 0%, #0d3b7a 100%); padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0;">Hospital Health Assistant</h2>
            <p style="color: #a8c4e8; margin: 5px 0 0 0; font-size: 0.85rem;">
                Multi-Modal AI System
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### How To Use")
        st.markdown("""
        1. **Enter** your name
        2. **Upload** a medical image or report
        3. **Type** your question (optional)
        4. **Click** Analyze
        5. **View** AI analysis results
        """)

        st.markdown("---")

        st.markdown("### What Can Be Analyzed")
        st.markdown("""
        - Skin rashes & conditions
        - Lab reports & blood tests
        - X-rays & scans
        - Prescriptions
        - Medical documents
        """)

        st.markdown("---")

        st.markdown("### Emergency Levels")
        st.markdown("""
        <div style="margin: 5px 0;">
            <span class="badge-critical">CRITICAL</span>
            <span style="color: #aaa; margin-left: 10px; font-size: 0.85rem;">
                Immediate action required
            </span>
        </div>
        <div style="margin: 10px 0;">
            <span class="badge-high">HIGH</span>
            <span style="color: #aaa; margin-left: 10px; font-size: 0.85rem;">
                See doctor today
            </span>
        </div>
        <div style="margin: 10px 0;">
            <span class="badge-medium">MEDIUM</span>
            <span style="color: #aaa; margin-left: 10px; font-size: 0.85rem;">
                Schedule appointment
            </span>
        </div>
        <div style="margin: 10px 0;">
            <span class="badge-low">LOW</span>
            <span style="color: #aaa; margin-left: 10px; font-size: 0.85rem;">
                Monitor symptoms
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("""
        <div class="disclaimer">
            Warning: This AI tool provides 
            informational support only. Always consult a qualified 
            medical professional for diagnosis and treatment.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <p style="color: #555; font-size: 0.75rem; text-align: center; margin-top: 20px;">
            Emergency: 1122 (Pakistan)<br>
            Copyright 2025 Multi-Modal AI Health Assistant
        </p>
        """, unsafe_allow_html=True)


def render_urgency_banner(urgency_level: str, emoji: str, color: str):
    """
    Renders urgency level banner
    """
    st.markdown(f"""
    <div style="
        background-color: {color}22;
        border: 2px solid {color};
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin: 15px 0;
    ">
        <h2 style="color: {color}; margin: 0;">
            {emoji} Urgency Level: {urgency_level}
        </h2>
    </div>
    """, unsafe_allow_html=True)


def render_emergency_alert(alert_message: str, email_sent: bool, email_message: str):
    """
    Renders emergency alert box with email status
    """
    st.markdown(f"""
    <div class="emergency-card">
        <div class="emergency-title">EMERGENCY ALERT DETECTED</div>
        <pre style="color: #ffaaaa; white-space: pre-wrap; font-family: Arial;">
{alert_message}
        </pre>
    </div>
    """, unsafe_allow_html=True)

    if email_sent:
        st.markdown(f"""
        <div class="success-msg">
            Check: <strong>Emergency Email Sent Successfully!</strong><br>
            {email_message}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error(f"Warning Email could not be sent: {email_message}")


def render_analysis_result(analysis_text: str):
    """
    Renders the AI analysis result
    """
    st.markdown("""
    <div class="result-card">
        <h3 style="color: #4a9eff; margin-top: 0;">
            AI Analysis Report
        </h3>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(analysis_text)


def render_disclaimer():
    """
    Renders the medical disclaimer
    """
    st.markdown("""
    <div class="disclaimer">
        Warning: <strong>Medical Disclaimer:</strong> This analysis is generated 
        by Artificial Intelligence and is intended for informational purposes 
        only. It does not constitute medical advice, diagnosis, or treatment. 
        Always consult a qualified healthcare professional before making any 
        medical decisions.
    </div>
    """, unsafe_allow_html=True)
