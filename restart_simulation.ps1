#!/usr/bin/env powershell
<#
.SYNOPSIS
    KPP Simulator Clean Restart Script
.DESCRIPTION
    Automatically performs a clean restart of the KPP simulation engine
    while keeping all servers running.
.EXAMPLE
    .\restart_simulation.ps1
#>

Write-Host "KPP Simulator Clean Restart" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# Function to test if a URL is responding
function Test-Endpoint {
    param([string]$Url, [string]$Name)
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -UseBasicParsing -TimeoutSec 5
        Write-Host "[OK] $Name : RESPONDING (Status $($response.StatusCode))" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "[ERROR] $Name : NOT RESPONDING" -ForegroundColor Red
        return $false
    }
}

# Step 1: Check if all servers are running
Write-Host "`nStep 1: Checking server status..." -ForegroundColor Yellow

$backendOk = Test-Endpoint "http://localhost:9100/status" "Flask Backend (9100)"
$websocketOk = Test-Endpoint "http://localhost:9101" "WebSocket Server (9101)"
$dashOk = Test-Endpoint "http://localhost:9103" "Dash Frontend (9103)"

if (-not ($backendOk -and $websocketOk -and $dashOk)) {
    Write-Host "[ERROR] Some servers are not running. Please start them first." -ForegroundColor Red
    Write-Host "   Run: python app.py, python main.py, python dash_app.py" -ForegroundColor Yellow
    exit 1
}

# Step 2: Get current simulation status
Write-Host "`nStep 2: Getting current simulation status..." -ForegroundColor Yellow

try {
    $statusResponse = Invoke-WebRequest -Uri "http://localhost:9100/status" -Method GET -UseBasicParsing
    $status = $statusResponse.Content | ConvertFrom-Json
    
    Write-Host "   Current Engine Time: $($status.engine_time) seconds" -ForegroundColor White
    Write-Host "   Simulation Running: $($status.simulation_running)" -ForegroundColor White
    Write-Host "   Engine Initialized: $($status.engine_initialized)" -ForegroundColor White
}
catch {
    Write-Host "[ERROR] Could not get simulation status" -ForegroundColor Red
    exit 1
}

# Step 3: Stop simulation cleanly
Write-Host "`nStep 3: Stopping simulation cleanly..." -ForegroundColor Yellow

try {
    $stopResponse = Invoke-WebRequest -Uri "http://localhost:9100/stop" -Method POST -UseBasicParsing
    if ($stopResponse.StatusCode -eq 200) {
        Write-Host "[OK] Simulation stopped successfully" -ForegroundColor Green
    }
    else {
        Write-Host "[WARNING] Stop request returned status $($stopResponse.StatusCode)" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "[ERROR] Failed to stop simulation: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 4: Wait a moment for clean shutdown
Write-Host "`nStep 4: Waiting for clean shutdown..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
Write-Host "[OK] Shutdown wait complete" -ForegroundColor Green

# Step 5: Restart simulation
Write-Host "`nStep 5: Restarting simulation..." -ForegroundColor Yellow

try {
    $startResponse = Invoke-WebRequest -Uri "http://localhost:9100/start" -Method POST -UseBasicParsing
    if ($startResponse.StatusCode -eq 200) {
        $startData = $startResponse.Content | ConvertFrom-Json
        Write-Host "[OK] Simulation restarted successfully" -ForegroundColor Green
        Write-Host "   Message: $($startData.message)" -ForegroundColor White
        Write-Host "   Trace ID: $($startData.trace_id)" -ForegroundColor Gray
    }
}
catch {
    Write-Host "[ERROR] Failed to restart simulation: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 6: Verify restart success
Write-Host "`nStep 6: Verifying restart..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

try {
    $newStatusResponse = Invoke-WebRequest -Uri "http://localhost:9100/status" -Method GET -UseBasicParsing
    $newStatus = $newStatusResponse.Content | ConvertFrom-Json
    
    Write-Host "New Status:" -ForegroundColor Cyan
    Write-Host "   Backend Status: $($newStatus.backend_status)" -ForegroundColor White
    Write-Host "   Engine Running: $($newStatus.engine_running)" -ForegroundColor White
    Write-Host "   Engine Time: $($newStatus.engine_time) seconds" -ForegroundColor White
    Write-Host "   Has Data: $($newStatus.has_data)" -ForegroundColor White
    
    if ($newStatus.simulation_running -eq $true -and $newStatus.engine_running -eq $true) {
        Write-Host "`n[SUCCESS] RESTART SUCCESSFUL!" -ForegroundColor Green
        Write-Host "   Simulation is running with fresh data" -ForegroundColor Green
        Write-Host "   Dashboard: http://localhost:9103" -ForegroundColor Cyan
        Write-Host "   Backend API: http://localhost:9100/status" -ForegroundColor Cyan
    }
    else {
        Write-Host "`n[WARNING] Restart completed but simulation may not be running properly" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "[ERROR] Could not verify restart status" -ForegroundColor Red
}

Write-Host "`n" + "=" * 50 -ForegroundColor Cyan
Write-Host "Clean Restart Process Complete" -ForegroundColor Cyan 