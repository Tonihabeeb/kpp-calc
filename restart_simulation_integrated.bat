@echo off
REM KPP Simulator Clean Restart - Using Integrated Main Server Starter
echo.
echo ======================================
echo   KPP Simulator Clean Restart
echo   (Using Integrated Main Launcher)
echo ======================================
echo.

powershell -ExecutionPolicy Bypass -File start_sync_system.ps1 -RestartSimulation

echo.
echo Press any key to exit...
pause > nul 