@echo off
echo.
echo ========================================
echo    MOBILE ACCESS - ANYWHERE SETUP
echo ========================================
echo.
echo This will give you a public URL to access
echo your app from ANYWHERE (not just home WiFi)
echo.
echo Options:
echo.
echo 1. NGROK (Recommended for testing)
echo    - Works in 2 minutes
echo    - Free tier available
echo    - URL like: https://abc123.ngrok.io
echo    - Access from anywhere
echo.
echo 2. Cloud Deployment (For permanent hosting)
echo    - Takes 10-15 minutes
echo    - Free tier available
echo    - Permanent URL
echo    - No computer needed
echo.
pause
echo.
echo Installing ngrok...
echo.

:: Check if ngrok is installed
where ngrok >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ngrok is already installed!
) else (
    echo Downloading ngrok...
    powershell -Command "& { Invoke-WebRequest -Uri 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip' -OutFile 'ngrok.zip'; Expand-Archive -Path 'ngrok.zip' -DestinationPath '.' -Force; Remove-Item 'ngrok.zip' }"
    echo ngrok downloaded!
)

echo.
echo ========================================
echo    SETUP INSTRUCTIONS
echo ========================================
echo.
echo 1. Go to: https://ngrok.com/
echo 2. Sign up for free account
echo 3. Copy your authtoken
echo 4. Run: ngrok config add-authtoken YOUR_TOKEN
echo.
echo Then run this script again!
echo.
pause
