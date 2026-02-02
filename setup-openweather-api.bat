@echo off
echo ============================================================
echo OpenWeather API Key Setup
echo ============================================================
echo.
echo You just purchased the PAID OpenWeather API!
echo Let's update your API key.
echo.
echo ============================================================
echo Step 1: Get Your New API Key
echo ============================================================
echo.
echo 1. Go to: https://home.openweathermap.org/api_keys
echo 2. Copy your NEW API key
echo 3. Come back here
echo.
pause
echo.
echo ============================================================
echo Step 2: Enter Your New API Key
echo ============================================================
echo.
set /p API_KEY="Paste your NEW API key here: "
echo.

REM Update .env file
echo Updating .env file...
(
echo # Environment Variables for Quantum Black Ice Detection System
echo # Updated with paid OpenWeather API key
echo.
echo OPENWEATHER_API_KEY=%API_KEY%
echo FLASK_ENV=development
echo PORT=5000
echo DATABASE_PATH=../data/black_ice.db
) > .env

echo.
echo ✅ API key updated in .env file!
echo.
echo ============================================================
echo Step 3: Update Railway
echo ============================================================
echo.
echo Now update Railway with your new API key:
echo.
echo 1. Go to: https://railway.app
echo 2. Open your project: quantum-black-ice
echo 3. Click Variables tab
echo 4. Update OPENWEATHER_API_KEY with: %API_KEY%
echo 5. Save (Railway will auto-redeploy)
echo.
echo ============================================================
echo Step 4: Test Your API Key
echo ============================================================
echo.
echo Testing API key...
curl "http://api.openweathermap.org/data/2.5/weather?lat=42.3314&lon=-83.0458&appid=%API_KEY%"
echo.
echo.
echo ✅ If you see weather data above, your API key works!
echo ❌ If you see an error, check your API key
echo.
echo ============================================================
echo Next Steps:
echo ============================================================
echo.
echo 1. Start local server:
echo    python backend/quick_start_no_ws.py
echo.
echo 2. Test on iPhone (same WiFi):
echo    http://192.168.1.103:5000
echo.
echo 3. Or use Railway (from anywhere):
echo    https://web-production-59bc.up.railway.app
echo.
pause
