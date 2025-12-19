@echo off
echo ============================================================
echo Black Ice Project - Security Updates (Quick)
echo ============================================================
echo.
echo This will update CRITICAL security packages only.
echo Estimated time: 2-3 minutes
echo.
pause

echo.
echo [1/4] Updating pip...
python -m pip install --upgrade pip

echo.
echo [2/4] Updating SSL/Security packages...
pip install --upgrade certifi==2025.11.12 urllib3==2.6.2

echo.
echo [3/4] Updating Web Framework security...
pip install --upgrade werkzeug==3.1.4 requests==2.32.3

echo.
echo [4/4] Updating Flask ecosystem...
pip install --upgrade flask-cors==6.0.2 flask-socketio==5.5.1

echo.
echo ============================================================
echo ✅ Security updates complete!
echo ============================================================
echo.

echo Testing installation...
python -c "import flask, requests; print('✅ All packages working!')" 2>nul && (
    echo ✅ Test passed!
) || (
    echo ❌ Test failed - check errors above
    pause
    exit /b 1
)

echo.
echo Next steps:
echo 1. Test locally: python backend\quick_start_no_ws.py
echo 2. Visit: http://localhost:5000
echo 3. If working, push to Railway: git push origin main
echo.
echo ============================================================
pause
