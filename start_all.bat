@echo off
REM Start Flask API backend on port 9100
start "Flask API" cmd /k python app.py

REM Start FastAPI WebSocket backend on port 9101
start "FastAPI WS" cmd /k python main.py

REM Start Dash frontend on port 9103
start "Dash UI" cmd /k python dash_app.py

REM Wait a few seconds for servers to start
ping 127.0.0.1 -n 5 > nul

REM Open the dashboard in the default browser
start http://127.0.0.1:9103/ 