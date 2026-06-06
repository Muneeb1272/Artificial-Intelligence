import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def handle_emergency(patient_name: str, emergency_contact: str, analysis_text: str, latitude: str = None, longitude: str = None):
    """
    Sends an emergency email with diagnosis and location if the condition is critical.
    """
    print(f"[EMERGENCY ALERT] Sending alert for {patient_name} to {emergency_contact}...")
    
    sender_email = os.getenv("SENDER_EMAIL", "emergency-alert@aihealth.local")
    sender_password = os.getenv("SENDER_PASSWORD", "")
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = emergency_contact
    msg['Subject'] = f"CRITICAL MEDICAL ALERT: {patient_name}"
    
    body = f"URGENT: A critical medical condition has been detected for {patient_name}.\n\n"
    body += f"AI Diagnosis Summary:\n{analysis_text}\n\n"
    
    if latitude and longitude:
        maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
        body += f"Patient's Last Known Location: {maps_link}\n\n"
    else:
        body += "Patient's location could not be determined.\n\n"
        
    body += "Please contact emergency services immediately."
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Attempt to send email if credentials exist, otherwise just log it
    if sender_password:
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, emergency_contact, text)
            server.quit()
            print("[EMERGENCY ALERT] Email sent successfully.")
        except Exception as e:
            print(f"[EMERGENCY ALERT] Failed to send email: {e}")
    else:
        print("[EMERGENCY ALERT] No email credentials found in environment. Simulated send:")
        print(body)
