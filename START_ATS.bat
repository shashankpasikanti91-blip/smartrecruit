@echo off
REM Recruitment ATS v3.2 - Quick Start
REM This script starts the Flask app and opens the browser

cd /d "c:\Users\User\Desktop\pydantic\future-projects\Recruitement ATS\Recruitment_AI_System_v3_1_dev"

echo Starting Recruitment ATS v3.2...
echo.

REM Start the Flask app in a new window
start "Recruitment ATS v3.2 Server" python advanced_app_v3.py

REM Wait 3 seconds for server to start
timeout /t 3 /nobreak

REM Open browser
start http://localhost:5001

echo.
echo Recruitment ATS v3.2 is launching...
echo Server: http://localhost:5001
echo.
pause
