@echo off
title KPP Simulator Dashboard
echo ============================================================
echo               KPP Simulator Dashboard Launcher
echo ============================================================
echo.
echo Starting the new Dash-based frontend...
echo Dashboard will be available at: http://127.0.0.1:8050
echo.
echo Press Ctrl+C to stop the dashboard
echo ============================================================
echo.

python dash_app.py

echo.
echo Dashboard stopped.
pause
