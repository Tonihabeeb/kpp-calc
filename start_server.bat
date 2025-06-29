@echo off
echo Starting KPP Simulator Flask Server...
echo =====================================

cd /d "%~dp0"

echo Current directory: %CD%
echo.

echo Testing Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo Starting Flask server...
python app.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Flask server failed to start
    echo Trying diagnostic script...
    python debug_flask_startup.py
)

pause
