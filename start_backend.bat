@echo off
title LogiAgent - Backend Server
cd /d "%~dp0backend"
echo ===================================================
echo   LogiAgent AI Logistics Operations Backend Server
echo ===================================================
echo.
echo Starting FastAPI with Uvicorn on http://127.0.0.1:8000 ...
echo API Docs will be available at http://127.0.0.1:8000/docs
echo.

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo Backend exited with an error. Check Python environment.
    pause
)
