@echo off
REM KPP Simulator Clean Restart - Batch File Version
echo.
echo ======================================
echo    KPP Simulator Clean Restart
echo ======================================
echo.

echo [1/3] Stopping simulation...
curl -X POST http://localhost:9100/stop -s > nul 2>&1
if %ERRORLEVEL% == 0 (
    echo     ✓ Simulation stopped successfully
) else (
    echo     ✗ Failed to stop simulation
    goto :error
)

echo.
echo [2/3] Waiting for clean shutdown...
timeout /t 2 /nobreak > nul
echo     ✓ Wait complete

echo.
echo [3/3] Restarting simulation...
curl -X POST http://localhost:9100/start -s > nul 2>&1
if %ERRORLEVEL% == 0 (
    echo     ✓ Simulation restarted successfully
) else (
    echo     ✗ Failed to restart simulation
    goto :error
)

echo.
echo ======================================
echo    ✓ RESTART COMPLETE!
echo    Dashboard: http://localhost:9102
echo ======================================
echo.
goto :end

:error
echo.
echo ======================================
echo    ✗ RESTART FAILED
echo    Check if servers are running
echo ======================================
echo.
pause

:end 