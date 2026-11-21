@echo off
title Face Recognition Biometric Attendance System
echo ===================================================
echo   Starting Face Recognition Attendance System...
echo ===================================================
echo.
cd /d "%~dp0"
start "" http://127.0.0.1:5000
.\.venv\Scripts\python.exe app.py
pause
