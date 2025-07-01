@echo off
REM Start Flask backend
start cmd /k "python app.py"
timeout /t 3
REM Start Dash frontend
start cmd /k "python dash_app.py"
timeout /t 2
REM Open UI in default browser
start http://localhost:8050 