@echo off
echo ====================================
echo SRP SmartRecruit v3.2 Startup
echo ====================================
echo.

echo Starting FastAPI server on port 5003...
echo.

uvicorn app.main:app --reload --port 5003

pause
