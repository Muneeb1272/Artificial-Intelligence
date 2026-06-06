
# 🏥 Multi-Modal AI Health Assistant

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![AI-Engine](https://img.shields.io/badge/AI--Engine-Gemini%20%26%20Groq-orange.svg)](https://google.aistudio.google.com/)
[![License](https://img.shields.io/badge/Academic-Project-green.svg)]()

An intelligent, cross-platform, and multi-modal AI-powered healthcare application designed to bridge the gap between complex medical diagnostics and everyday users. This system can seamlessly analyze textual medical queries, laboratory reports (PDF/Images), and visual dermatological conditions to provide clear, actionable, and user-friendly health guidance.

---

## 👥 Group Members & Credits
* **Ali Zain** (Roll No: **05**) — *Lead Developer / System Architecture*
* **Muneeb Hamza** (Roll No: **13**) — *AI Engineer / Frontend Developer*
* **University:** University of Layyah
* **Course:** Artificial Intelligence (BS IT - Semester Project)
* **Project Evaluator:** Madam Nabiha Komal

---

## ✨ Key Features & Functionality

* **📸 Multimodal Image Analysis:** Advanced visual parsing of skin conditions (rashes, lesions), X-rays, and prescriptions using advanced AI models[cite: 1].
* **📊 Medical Report Summarization:** Transforms complex medical terminology from laboratory blood reports or diagnostic PDFs into clear, simplified summaries for laypersons[cite: 1].
* **💬 Intelligent Health Q&A Chatbot:** A context-aware conversational agent that handles medical queries and maintains historical interaction data[cite: 1].
* **🚨 Emergency & Smart Escalation System:** Instantly identifies life-threatening or critical health anomalies and triggers real-time visual alerts and automated emergency email notifications[cite: 1].
* **🧠 Hybrid Local & Cloud Execution:** Features intelligent failover management. It uses a cloud engine fallback if local processing models are unavailable, guaranteeing 100% uptime without relying on premium subscriptions.

---

## 🛠️ System Architecture & Tech Stack

| Component | Technology Used | Purpose |
| :--- | :--- | :--- |
| **Frontend UI** | Streamlit, HTML5, CSS3 | Clean, interactive, and responsive user dashboard |
| **AI Processing** | Google Gemini Engine, Groq API, Local Ollama | Natural language processing & image scanning |
| **Backend Engine** | Python 3.10+, FastAPI | Core orchestration logic and API pipeline routing |
| **Data Layer** | JSON (Medical Knowledge Base, RL State Maps) | Session persistence and medical range parameters |
| **Automation** | Secure SMTP Client | Triggering automated emergency alert emails |

---

## 🚀 Recommended Run Paths (Free Execution)

Choose either of the following execution workflows to host the system locally without needing paid subscription keys.

### 📌 Option 1: Streamlit UI Dashboard (Best Entry Point)
1. **Install required dependencies:**
```bash
   pip install -r requirements.txt
Execute the Streamlit launcher:

Bash
   streamlit run app.py
Access the App: Open the local Streamlit network URL generated in your terminal (usually http://localhost:8501).

📌 Option 2: Headless FastAPI Backend + Frontend Integration
Install required dependencies:

Bash
   pip install -r requirements.txt
Launch the backend server:

Bash
   uvicorn backend.main:app --reload
Access API Documentation: Navigate to http://127.0.0.1:8000 or http://127.0.0.1:8000/docs in your web browser.

⚙️ Environment Configuration (.env)
To safely configure third-party services and optional automated email dispatch, set up your credentials using the provided template file:

Locate the .env.example file in the root directory.

Duplicate or rename it to .env.

Populated the environment variables as required:

Code snippet
   GEMINI_API_KEY=your_gemini_key_here
   GROQ_API_KEY=your_groq_key_here
   EMAIL_PASSWORD=your_email_app_password_here
Note: The platform includes a fallback local response model, ensuring core operations remain functional even if external API tokens are omitted.

🛑 Important Academic & Medical Disclaimer
This software application is a prototype developed solely for academic evaluation purposes. It provides generalized health information and introductory guidance based on data pattern analysis.

It does not provide real medical diagnoses[cite: 1].

It is not a clinical substitute for diagnostic insights from a licensed physician, clinician, or professional medical practitioner[cite: 1].

In case of a real medical crisis or urgent health issue, please contact local emergency medical services immediately[cite: 1].


---

### Isay Update Krne Ka Tareeqa:
1. GitHub pr jain, **`README.md`** file ko open krein aur upar edit (pencil icon) pr click krein.
2. Purana text delete kr k yeh oopar wala naya code wahan paste kr dain.
3. Niche **Commit changes** kr dain.

Aap ka GitHub repository page ab intahai professional aur standard software project jesa dikhay ga!
