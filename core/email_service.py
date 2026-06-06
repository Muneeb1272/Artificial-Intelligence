import smtplib
import os
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# Config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    EMAIL_ADDRESS,
    EMAIL_APP_PASSWORD,
    EMERGENCY_EMAIL,
    EMAIL_SMTP_SERVER,
    EMAIL_SMTP_PORT,
    APP_NAME
)

def send_emergency_email(
    patient_name: str,
    analysis_text: str,
    urgency_level: str,
    image_path: str = None,
    recipient_email: str = None
) -> dict:
    """
    Emergency situation mein doctor/family ko email bhejta hai
    image attachment ke saath
    """
    try:
        # ============================================
        # EMAIL CONTENT BANAO
        # ============================================
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = EMERGENCY_EMAIL
        msg["Subject"] = f"EMERGENCY ALERT - {APP_NAME} | Patient: {patient_name} | Level: {urgency_level}"

        # Email body
        current_time = datetime.now().strftime("%d-%m-%Y %I:%M %p")

        body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">

    <div style="background-color: #ff4444; padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0;">EMERGENCY MEDICAL ALERT</h1>
        <p style="color: white; margin: 5px 0;">Multi-Modal AI Health Assistant</p>
    </div>

    <div style="background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd;">

        <h2 style="color: #ff4444;">Critical Condition Detected</h2>

        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background-color: #fff3f3;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Patient Name</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{patient_name}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Time</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{current_time}</td>
            </tr>
            <tr style="background-color: #fff3f3;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Urgency Level</td>
                <td style="padding: 10px; border: 1px solid #ddd;">
                    <span style="background-color: #ff4444; color: white; padding: 3px 10px; border-radius: 5px;">
                        {urgency_level}
                    </span>
                </td>
            </tr>
        </table>

        <h3 style="color: #333; margin-top: 20px;">AI Analysis Report:</h3>
        <div style="background-color: white; padding: 15px; border-left: 4px solid #ff4444; border-radius: 5px;">
            <p style="color: #555; line-height: 1.6;">{analysis_text}</p>
        </div>

        {"<h3 style='color: #333;'>Medical Image/Report:</h3><p style='color: #555;'>Please see the attached image for reference.</p>" if image_path else ""}

        <div style="background-color: #fff3cd; padding: 15px; margin-top: 20px; border-radius: 5px; border: 1px solid #ffc107;">
            <p style="margin: 0; color: #856404;">
                <strong>Important:</strong> This is an automated alert from AI Health Assistant. 
                Please contact the patient immediately and provide necessary medical assistance.
            </p>
        </div>

    </div>

    <div style="background-color: #333; padding: 15px; text-align: center; border-radius: 0 0 10px 10px;">
        <p style="color: #aaa; margin: 0; font-size: 12px;">
            This email was automatically sent by {APP_NAME}<br>
            For emergencies call: 1122 (Pakistan Emergency)
        </p>
    </div>

</body>
</html>
        """

        msg.attach(MIMEText(body, "html"))

        # ============================================
        # IMAGE ATTACHMENT (agar image ho)
        # ============================================
        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                img_data = f.read()
                img_attachment = MIMEBase("application", "octet-stream")
                img_attachment.set_payload(img_data)
                encoders.encode_base64(img_attachment)
                img_attachment.add_header(
                    "Content-Disposition",
                    f"attachment; filename=medical_report_{patient_name}.png"
                )
                msg.attach(img_attachment)

        # ============================================
        # Check whether email credentials are configured
        # ============================================
        recipient = recipient_email or EMERGENCY_EMAIL
        if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD or not recipient:
            return {
                "success": False,
                "message": "Email credentials are not configured. Emergency email was not sent."
            }

        # ============================================
        # EMAIL BHEJO
        # ============================================
        msg["To"] = recipient
        with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, recipient, msg.as_string())

        return {
            "success": True,
            "message": f"Emergency email successfully sent to {recipient}"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Email send karne mein error: {str(e)}"
        }
