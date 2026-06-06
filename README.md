# Multi-Modal AI Health Assistant

A free local health assistant prototype centered around the Streamlit app in `app.py`.

## What is fixed
- `core/gemini_engine.py` now uses a free local analysis engine instead of a paid Gemini API.
- `backend/ollama_engine.py` still supports local Ollama if installed, but now falls back to a free analysis engine when Ollama is unavailable.
- `ui/styles.py` was repaired so the Streamlit interface can render correctly.
- `requirements.txt` now includes `streamlit` for the free Streamlit UI.
- Added `.env.example` to configure optional email alerts.

## Recommended free run path
### Option 1: Streamlit UI (best free entry)
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   streamlit run app.py
   ```
3. Open the Streamlit URL shown in the terminal.

### Option 2: FastAPI + frontend
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the backend:
   ```bash
   uvicorn backend.main:app --reload
   ```
3. Open `http://127.0.0.1:8000` in your browser.

## Notes for free use
- No paid API key is required for the Streamlit app.
- `backend/ollama_engine.py` can use local Ollama if you install it, but it is not required because the app falls back to a local response engine.
- The current system is a prototype and provides general guidance only. Always consult a qualified healthcare professional.

## Optional email alerts
- Configure `.env` from `.env.example` if you want email alerts.
- Email alerts are optional and will not prevent the free analysis flow from working.

## Important disclaimer
This app is for informational guidance only. It is not a medical diagnosis tool. Always seek help from a licensed doctor for real health issues.
