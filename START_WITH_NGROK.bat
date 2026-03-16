@echo off
TITLE SRP SmartRecruit v3.2 - Server + Ngrok
COLOR 0A

echo ========================================
echo  SRP SmartRecruit v3.2
echo  Server + Ngrok Public URL
echo ========================================
echo.

REM Check if ngrok is installed
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Ngrok not found!
    echo.
    echo Please install ngrok:
    echo 1. Visit: https://ngrok.com/download
    echo 2. Download and extract ngrok.exe
    echo 3. Add ngrok.exe to PATH or place in this folder
    echo 4. Run: ngrok config add-authtoken YOUR_TOKEN
    echo.
    pause
    exit /b 1
)

echo [1/3] Starting FastAPI server...
start "SRP ATS v3.2 Server" /min cmd /c "cd /d "%~dp0" && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 5003"

REM Wait for server to start
timeout /t 7 /nobreak >nul

echo [2/3] Starting ngrok tunnel...
echo.
echo Ngrok will create a public HTTPS URL for your server
echo This URL will be valid for 7 days with a free account
echo.

REM Start ngrok with new window
start "Ngrok Tunnel" cmd /c "ngrok http 5003"

timeout /t 3 /nobreak >nul

echo [3/3] Getting public URL...
timeout /t 2 /nobreak >nul

REM Try to get ngrok URL
powershell -Command "(Invoke-WebRequest -Uri http://localhost:4040/api/tunnels -UseBasicParsing).Content | ConvertFrom-Json | Select-Object -ExpandProperty tunnels | Select-Object -ExpandProperty public_url -First 1" > ngrok_url.txt 2>nul

if exist ngrok_url.txt (
    set /p NGROK_URL=<ngrok_url.txt
    echo.
    echo ========================================
    echo   SUCCESS! System is Running
    echo ========================================
    echo.
    echo  Local URL:  http://localhost:5003
    echo  Public URL: !NGROK_URL!
    echo  API Docs:   !NGROK_URL!/docs
    echo.
    echo ========================================
    echo  Share this URL with your team!
    echo ========================================
    echo.
    del ngrok_url.txt
) else (
    echo.
    echo ========================================
    echo  System is Running
    echo ========================================
    echo.
    echo  Local URL:  http://localhost:5003
    echo  Ngrok URL:  Check ngrok window
    echo  API Docs:   http://localhost:5003/docs
    echo.
    echo ========================================
)

echo.
echo Press any key to view ngrok dashboard (shows public URL)...
pause >nul
powershell -Command "Start-Process 'http://localhost:4040'"

echo.
echo Server is running. Do NOT close this window!
echo Press any key when you want to stop the server...
pause >nul

echo.
echo Stopping services...
taskkill /FI "WINDOWTITLE eq SRP ATS v3.2 Server" /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq Ngrok Tunnel" /F >nul 2>nul
taskkill /IM ngrok.exe /F >nul 2>nul

echo.
echo Services stopped. You can close this window.
pause
