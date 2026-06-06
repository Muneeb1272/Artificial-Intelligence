# 🏥 Multi-Modal AI Health Assistant

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/AI_Engine-Gemini_%26_Groq-orange?style=for-the-badge" alt="AI Engine">
  <img src="https://img.shields.io/badge/Academic-Project-green?style=for-the-badge" alt="Academic Project">
</p>

---

### 👥 Group Members & Academic Credits
* 🎖️ **Ali Zain** (Roll No: **05**) — *Lead Developer & System Architecture*
* 🎖️ **Muneeb Hamza** (Roll No: **13**) — *AI Engineer & Frontend Developer*
* 🏛️ **University:** University of Layyah
* 📘 **Course:** Artificial Intelligence (BS IT - Semester Project)
* 🎓 **Project Evaluator:** Madam Nabiha Komal

---

## 🎯 Project Overview
An intelligent, cross-platform, and multi-modal AI-powered healthcare application designed to bridge the gap between complex medical diagnostics and everyday users. This system can seamlessly analyze textual medical queries, laboratory reports (PDF/Images), and visual dermatological conditions to provide clear, actionable, and user-friendly health guidance[cite: 1].

---

## ✨ Key Features

* **📸 Multimodal Image Analysis**  
  Advanced visual parsing of skin conditions (rashes, lesions), X-rays, and prescriptions using state-of-the-art AI models[cite: 1].
* **📊 Medical Report Summarization**  
  Transforms complex medical terminology from laboratory blood reports or diagnostic PDFs into clear, simplified summaries for laypersons[cite: 1].
* **💬 Intelligent Health Q&A Chatbot**  
  A context-aware conversational agent that handles medical queries and maintains historical interaction data[cite: 1].
* **🚨 Emergency Smart Escalation**  
  Instantly identifies life-threatening or critical health anomalies and triggers real-time visual alerts and automated emergency email notifications[cite: 1].
* **🧠 Hybrid Local & Cloud Execution**  
  Features intelligent failover management. It uses a cloud engine fallback if local models are unavailable, guaranteeing 100% uptime without relying on premium subscriptions.

---

## 🛠️ Tech Stack & System Architecture

| Component | Technology Used | Purpose |
| :--- | :--- | :--- |
| 💻 **Frontend UI** | Streamlit, HTML5, CSS3 | Clean, interactive, and responsive user dashboard |
| 🧠 **AI Processing** | Google Gemini Engine, Groq API, Local Ollama | Natural language processing & image scanning |
| ⚙️ **Backend Engine** | Python 3.10+, FastAPI | Core orchestration logic and API pipeline routing |
| 📁 **Data Layer** | JSON Database Structure | Session persistence and medical range parameters |
| ✉️ **Automation** | Secure SMTP Client | Triggering automated emergency alert emails |

---

## 🚀 Setup & Execution Guide (100% Free)

> [!NOTE]  
> Choose either of the following execution workflows to host the system locally without needing paid subscription keys.

### 📌 Option 1: Streamlit UI Dashboard (Recommended)

1. **Install required dependencies:**
```bash
   pip install -r requirements.txt
Execute the Streamlit launcher:

Bash
   streamlit run app.py
Access the Application:

Open the local URL generated in your terminal (usually http://localhost:8501).

📌 Option 2: Headless FastAPI Backend
Install required dependencies:

Bash
   pip install -r requirements.txt
Launch the backend server:

Bash
   uvicorn backend.main:app --reload
Access API Documentation:

Navigate to http://127.0.0.1:8000/docs in your web browser.

⚙️ Environment Configuration (.env)
To safely configure third-party services and optional automated email dispatch, set up your credentials using the template:

Locate the .env.example file in the root directory.

Rename or duplicate it to .env.

Populate the environment variables as required:

Code snippet
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
EMAIL_PASSWORD=your_email_app_password_here
[!TIP]
The platform includes a fallback local response model, ensuring core operations remain functional even if external API tokens are omitted.

🛑 Important Academic & Medical Disclaimer
[!WARNING]

This software application is a prototype developed solely for academic evaluation purposes. It provides generalized health information and introductory guidance based on data pattern analysis.

It does not provide real medical diagnoses[cite: 1].

It is not a clinical substitute for diagnostic insights from a licensed physician, clinician, or professional medical practitioner[cite: 1].

In case of a real medical crisis or urgent health issue, please contact local emergency medical services immediately[cite: 1].
