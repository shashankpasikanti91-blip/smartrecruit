@echo off
REM ===================================================================
REM Recruitment ATS v3.2 - Production Demo Ready
REM FastAPI Server on Port 5003
REM ===================================================================

setlocal enabledelayedexpansion

REM Get the directory where this batch file is located
cd /d "%~dp0"

echo.
echo ===================================================================
echo  RECRUITMENT ATS v3.2 - DEMO VERSION
echo ===================================================================
echo.
echo Starting FastAPI Server on http://localhost:5003
echo.

REM Kill any existing Python processes on port 5003
taskkill /F /IM python.exe >nul 2>&1

REM Small delay to ensure port is released
timeout /t 2 /nobreak >nul

REM Start the FastAPI Server
title Recruitment ATS v3.2 - FastAPI Server
echo Activating virtual environment...
call .\.venv\Scripts\activate.bat

echo.
echo ===================================================================
echo  Server is starting... Opening browser in 5 seconds
echo ===================================================================
echo.

REM Start the server in the same window
start /b "" python -m uvicorn app.main:app --host 0.0.0.0 --port 5003 --reload

REM Wait for server to start
timeout /t 5 /nobreak >nul

REM Open browser
echo Opening application in browser...
start http://localhost:5003

echo.
echo ===================================================================
echo  Application is running!
echo  Dashboard: http://localhost:5003/dashboard
echo  Admin: http://localhost:5003/admin
echo.
echo Press Ctrl+C in this window to stop the server
echo ===================================================================
echo.

REM Keep window open
pause
