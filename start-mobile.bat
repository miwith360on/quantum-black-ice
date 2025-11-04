@echo off
setlocal enabledelayedexpansion

:: Black Ice Alert - Mobile PWA Launcher
:: Starts the server and provides mobile access instructions

title Black Ice Alert - Mobile PWA

echo.
echo ========================================
echo    📱 BLACK ICE ALERT - MOBILE PWA
echo ========================================
echo.

:: Activate virtual environment
call "%~dp0venv\Scripts\activate.bat"

:: Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set "ip=%%a"
    set "ip=!ip:~1!"
    goto :found_ip
)
:found_ip

echo 🌐 Network Information:
echo    Local:     http://localhost:5000/mobile.html
echo    Mobile:    http://!ip!:5000/mobile.html
echo.
echo 📱 iPhone Installation:
echo    1. Open Safari on your iPhone
echo    2. Go to: http://!ip!:5000/mobile.html
echo    3. Tap Share button → "Add to Home Screen"
echo    4. Tap "Add" to install the app
echo.
echo ✨ Features:
echo    • Works like a native app
echo    • Full offline support
echo    • Real-time WebSocket updates
echo    • AI/ML predictions
echo    • GPS location tracking
echo    • Interactive radar map
echo.
echo ========================================
echo.

:: Start the server
cd backend
python app.py

pause
