@echo off
title AI Health Assistant - Starting...
echo ============================================
echo   Multi-Modal AI Health Assistant
echo   Starting Server...
echo ============================================
echo.

cd /d C:\Users\PMLS\Desktop\Multi-Modal-AI-Health-Assistant

echo [1/2] Starting server on http://127.0.0.1:8000 ...
echo.
echo ============================================
echo   Browser mein ye address kholein:
echo   http://127.0.0.1:8000
echo ============================================
echo.
echo   Band karne ke liye ye window band karein
echo   ya Ctrl+C dabayein.
echo.

start http://127.0.0.1:8000

.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

pause
