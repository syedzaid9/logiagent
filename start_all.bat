@echo off
title LogiAgent - Launcher
cd /d "%~dp0"
echo ===================================================
echo       LogiAgent AI Logistics Operations Platform
echo ===================================================
echo.
echo Launching Backend Server in new window...
start "LogiAgent Backend Server" cmd /k "call \"%~dp0start_backend.bat\""

timeout /t 3 /nobreak >nul

echo Launching Frontend Client in new window...
start "LogiAgent Frontend Client" cmd /k "call \"%~dp0start_frontend.bat\""

echo.
echo ===================================================
echo LogiAgent services have been launched!
echo.
echo Backend API : http://127.0.0.1:8000
echo Swagger Docs: http://127.0.0.1:8000/docs
echo Frontend App: http://localhost:5173
echo ===================================================
echo.
timeout /t 5 >nul
