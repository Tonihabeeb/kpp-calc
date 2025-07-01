@echo off
REM Start Flask backend in background
start "Flask Backend" cmd /k "python app.py"
timeout /t 3
REM Start Dash frontend in background
start "Dash Frontend" cmd /k "python dash_app.py"
timeout /t 3

REM Check if Flask backend is listening on port 5000
powershell -Command "if ((Test-NetConnection -ComputerName localhost -Port 5000).TcpTestSucceeded) { Write-Host 'Flask backend is running on port 5000.' } else { Write-Host 'Flask backend is NOT running on port 5000.' }"
REM Check if Dash frontend is listening on port 8050
powershell -Command "if ((Test-NetConnection -ComputerName localhost -Port 8050).TcpTestSucceeded) { Write-Host 'Dash frontend is running on port 8050.' } else { Write-Host 'Dash frontend is NOT running on port 8050.' }"

REM Open UI in default browser
start http://localhost:8050 