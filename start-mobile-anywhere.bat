@echo off
setlocal enabledelayedexpansion

title Black Ice Alert - Mobile Anywhere (ngrok)

echo.
echo ========================================
echo    STARTING MOBILE-ANYWHERE MODE
echo ========================================
echo.

:: Check if ngrok is configured
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: ngrok not found!
    echo.
    echo Please run: setup-mobile-anywhere.bat first
    echo.
    pause
    exit /b
)

:: Start Flask server in background
echo Starting Flask server...
cd "%~dp0backend"
start /B python app.py

:: Wait for server to start
timeout /t 5 /nobreak >nul

:: Start ngrok tunnel
echo.
echo Starting ngrok tunnel...
echo.
echo ========================================
echo    YOUR PUBLIC URL
echo ========================================
echo.

ngrok http 5000

pause
