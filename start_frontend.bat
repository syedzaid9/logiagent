@echo off
title LogiAgent - Frontend UI
cd /d "%~dp0frontend"
echo ===================================================
echo   LogiAgent AI Logistics Operations Frontend UI
echo ===================================================
echo.
echo Starting Vite Dev Server on http://localhost:5173 ...
echo.

npm run dev

if %ERRORLEVEL% neq 0 (
    echo.
    echo Frontend exited with an error. Running npm install...
    npm install
    npm run dev
    pause
)
