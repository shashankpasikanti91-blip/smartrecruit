@echo off
REM ============================================================================
REM Recruitment AI System - Complete Startup Script
REM Starts all required services for n8n + webhook integration
REM ============================================================================

echo.
echo ================================================================================
echo  RECRUITMENT AI SYSTEM - COMPLETE STARTUP
echo ================================================================================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in PATH
    exit /b 1
)

REM Get the current directory
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

echo [1/4] Checking environment...
if not exist ".env" (
    echo ERROR: .env file not found
    echo Please create .env file with your credentials
    exit /b 1
)

echo ✓ .env found

echo.
echo [2/4] Starting webhook server...
echo       URL: http://localhost:8000
echo.
start "Webhook Server" cmd /k python n8n_webhook_receiver.py

timeout /t 3 >nul

echo.
echo [3/4] Starting ngrok tunnel...
echo       Tunnel: http://localhost:4040 (management)
echo.
start "ngrok Tunnel" cmd /k ngrok http 8000

timeout /t 5 >nul

echo.
echo [4/4] You can now start n8n separately...
echo.
echo ================================================================================
echo  STARTUP COMPLETE
echo ================================================================================
echo.
echo Next steps:
echo.
echo  1. ngrok tunnel should be active (check: http://localhost:4040)
echo  2. Copy ngrok URL from dashboard
echo  3. Start n8n in another terminal: n8n
echo  4. Access n8n at: http://localhost:5678
echo.
echo To test webhook:
echo  python test_ngrok_webhook.py
echo.
pause
