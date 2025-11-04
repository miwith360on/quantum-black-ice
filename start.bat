@echo off
REM Quick Start Script for Quantum Black Ice Detection System
REM Automatically activates environment and starts the server

echo.
echo ============================================================
echo    Quantum Black Ice Detection System - Quick Start
echo ============================================================
echo.

REM Navigate to project directory
cd /d "C:\Users\Kqumo\black ice weather\quantum-black-ice"

echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

echo [2/3] Checking dependencies...
python -c "import tensorflow; import flask_socketio; print('All dependencies installed')" 2>nul
if errorlevel 1 (
    echo.
    echo Missing dependencies detected!
    echo.
    echo Installing required packages...
    pip install -r requirements.txt
    echo.
)

echo [3/3] Starting server...
echo.
echo ============================================================
echo    Server starting on http://localhost:5000
echo ============================================================
echo.
echo Features Available:
echo    - AI/ML Deep Learning
echo    - Real-Time WebSocket Streaming
echo    - Satellite and Weather Radar
echo    - Route Monitoring
echo.
echo Dashboards:
echo    - Main: frontend/index.html
echo    - Route: frontend/route-dashboard.html
echo    - Advanced: frontend/advanced-dashboard.html
echo.
echo Tip: Open advanced-dashboard.html for all cutting-edge features!
echo.
echo ============================================================
echo.

cd backend
python app.py

pause
