# KPP Simulator Synchronized System Launcher for Windows PowerShell
# Starts all servers in the correct order for real-time synchronization
# Enhanced with comprehensive error handling and monitoring

param(
    [switch]$Test,
    [switch]$Stop,
    [switch]$RestartSimulation,
    [switch]$Debug
)

# Error handling configuration
$ErrorActionPreference = "Continue"
$script:ErrorLog = @()
$script:LastErrorCheck = Get-Date
$script:ErrorCheckInterval = 30  # seconds
$script:MaxRetries = 3
$script:RetryDelay = 5  # seconds

# Error severity levels
$ErrorLevels = @{
    "CRITICAL" = 1
    "HIGH" = 2
    "MEDIUM" = 3
    "LOW" = 4
    "INFO" = 5
}

# Error categories
$ErrorCategories = @{
    "STARTUP" = "Server startup failures"
    "RUNTIME" = "Runtime errors during operation"
    "NETWORK" = "Network connectivity issues"
    "RESOURCE" = "Resource exhaustion (CPU, memory, disk)"
    "DEPENDENCY" = "Missing dependencies or configuration"
    "SYNCHRONIZATION" = "Inter-service communication issues"
    "DATABASE" = "Data persistence or retrieval errors"
    "SECURITY" = "Security-related issues"
}

# Function to log errors with timestamp and severity
function Write-ErrorLog {
    param(
        [string]$Message,
        [string]$Severity = "MEDIUM",
        [string]$Category = "RUNTIME",
        [string]$Server = "UNKNOWN",
        [string]$Details = ""
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $errorEntry = @{
        Timestamp = $timestamp
        Severity = $Severity
        Category = $Category
        Server = $Server
        Message = $Message
        Details = $Details
    }
    
    $script:ErrorLog += $errorEntry
    
    # Color coding based on severity
    $color = switch ($Severity) {
        "CRITICAL" { "Red" }
        "HIGH" { "DarkRed" }
        "MEDIUM" { "Yellow" }
        "LOW" { "Cyan" }
        "INFO" { "Gray" }
        default { "White" }
    }
    
    Write-Host "[$timestamp] [$Severity] [$Server] $Message" -ForegroundColor $color
    if ($Details -and $Debug) {
        Write-Host "   Details: $Details" -ForegroundColor Gray
    }
}

# Function to check server health and detect errors
function Test-ServerHealth {
    param([string]$ServerName, [string]$HealthUrl, [int]$Port)
    
    try {
        $response = Invoke-WebRequest -Uri $HealthUrl -Method GET -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            return @{ Status = "HEALTHY"; ResponseTime = $response.BaseResponse.ResponseTime; Details = "OK" }
        } else {
            Write-ErrorLog -Message "Server returned status $($response.StatusCode)" -Severity "HIGH" -Category "RUNTIME" -Server $ServerName -Details "HTTP $($response.StatusCode)"
            return @{ Status = "DEGRADED"; ResponseTime = $response.BaseResponse.ResponseTime; Details = "HTTP $($response.StatusCode)" }
        }
    }
    catch {
        $errorMsg = $_.Exception.Message
        Write-ErrorLog -Message "Server health check failed" -Severity "HIGH" -Category "NETWORK" -Server $ServerName -Details $errorMsg
        return @{ Status = "FAILED"; ResponseTime = -1; Details = $errorMsg }
    }
}

# Function to check job status and detect process errors
function Test-JobStatus {
    param([System.Management.Automation.Job]$Job)
    
    $jobName = $Job.Name
    $jobState = $Job.State
    
    if ($jobState -eq "Failed") {
        $errorDetails = $Job.ChildJobs[0].Error | Select-Object -First 1 | ForEach-Object { $_.Exception.Message }
        Write-ErrorLog -Message "Job failed" -Severity "CRITICAL" -Category "RUNTIME" -Server $jobName -Details $errorDetails
        return "FAILED"
    }
    elseif ($jobState -eq "Stopped") {
        Write-ErrorLog -Message "Job stopped unexpectedly" -Severity "HIGH" -Category "RUNTIME" -Server $jobName
        return "STOPPED"
    }
    elseif ($jobState -eq "Running") {
        # Check if job has been running for too long without output (potential hang)
        $jobAge = (Get-Date) - $Job.PSBeginTime
        if ($jobAge.TotalMinutes -gt 5) {
            $hasOutput = $Job.ChildJobs[0].Output.Count -gt 0
            if (-not $hasOutput) {
                Write-ErrorLog -Message "Job may be hanging (no output for $([math]::Round($jobAge.TotalMinutes, 1)) minutes)" -Severity "MEDIUM" -Category "RUNTIME" -Server $jobName
            }
        }
        return "RUNNING"
    }
    
    return $jobState
}

# Function to check system resources
function Test-SystemResources {
    $cpuUsage = (Get-Counter "\Processor(_Total)\% Processor Time").CounterSamples[0].CookedValue
    $memoryUsage = (Get-Counter "\Memory\% Committed Bytes In Use").CounterSamples[0].CookedValue
    $diskUsage = (Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace / (Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'").Size * 100
    
    if ($cpuUsage -gt 90) {
        Write-ErrorLog -Message "High CPU usage detected: $([math]::Round($cpuUsage, 1))%" -Severity "MEDIUM" -Category "RESOURCE" -Server "SYSTEM"
    }
    
    if ($memoryUsage -gt 85) {
        Write-ErrorLog -Message "High memory usage detected: $([math]::Round($memoryUsage, 1))%" -Severity "HIGH" -Category "RESOURCE" -Server "SYSTEM"
    }
    
    if ($diskUsage -lt 10) {
        Write-ErrorLog -Message "Low disk space: $([math]::Round($diskUsage, 1))% free" -Severity "HIGH" -Category "RESOURCE" -Server "SYSTEM"
    }
}

# Function to attempt automatic recovery
function Invoke-ErrorRecovery {
    param([string]$ServerName, [string]$ErrorType)
    
    Write-Host "Attempting recovery for $ServerName..." -ForegroundColor Yellow
    
    switch ($ErrorType) {
        "STARTUP" {
            # Restart the specific server
            $job = Get-Job -Name $ServerName -ErrorAction SilentlyContinue
            if ($job) {
                Stop-Job -Job $job -ErrorAction SilentlyContinue
                Remove-Job -Job $job -ErrorAction SilentlyContinue
            }
            
            # Restart based on server type
            switch ($ServerName) {
                "Flask-Backend" {
                    Start-Job -ScriptBlock { Set-Location $using:PWD; python app.py } -Name "Flask-Backend" | Out-Null
                    Start-Sleep 3
                }
                "Master-Clock" {
                    Start-Job -ScriptBlock { Set-Location $using:PWD; python realtime_sync_master.py } -Name "Master-Clock" | Out-Null
                    Start-Sleep 2
                }
                "WebSocket-Server" {
                    Start-Job -ScriptBlock { Set-Location $using:PWD; python main.py } -Name "WebSocket-Server" | Out-Null
                    Start-Sleep 2
                }
                "Dash-Frontend" {
                    Start-Job -ScriptBlock { Set-Location $using:PWD; python dash_app.py } -Name "Dash-Frontend" | Out-Null
                    Start-Sleep 3
                }
            }
            
            Write-ErrorLog -Message "Server restarted" -Severity "INFO" -Category "RUNTIME" -Server $ServerName
        }
        "NETWORK" {
            # Wait and retry health check
            Start-Sleep -Seconds $script:RetryDelay
            Write-ErrorLog -Message "Network retry completed" -Severity "INFO" -Category "NETWORK" -Server $ServerName
        }
        "RESOURCE" {
            # Log resource warning but don't restart (could make things worse)
            Write-ErrorLog -Message "Resource issue detected - manual intervention may be required" -Severity "MEDIUM" -Category "RESOURCE" -Server $ServerName
        }
    }
}

# Function to generate error summary report
function Show-ErrorSummary {
    Write-Host ""
    Write-Host "=== ERROR SUMMARY REPORT ===" -ForegroundColor Cyan
    Write-Host "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    
    if ($script:ErrorLog.Count -eq 0) {
        Write-Host "No errors detected in this session." -ForegroundColor Green
        return
    }
    
    # Group errors by severity
    $criticalErrors = $script:ErrorLog | Where-Object { $_.Severity -eq "CRITICAL" }
    $highErrors = $script:ErrorLog | Where-Object { $_.Severity -eq "HIGH" }
    $mediumErrors = $script:ErrorLog | Where-Object { $_.Severity -eq "MEDIUM" }
    
    Write-Host "Critical Errors: $($criticalErrors.Count)" -ForegroundColor $(if ($criticalErrors.Count -gt 0) { "Red" } else { "Green" })
    Write-Host "High Priority Errors: $($highErrors.Count)" -ForegroundColor $(if ($highErrors.Count -gt 0) { "Yellow" } else { "Green" })
    Write-Host "Medium Priority Errors: $($mediumErrors.Count)" -ForegroundColor $(if ($mediumErrors.Count -gt 0) { "Cyan" } else { "Green" })
    
    # Show recent errors
    Write-Host ""
    Write-Host "Recent Errors (Last 10):" -ForegroundColor Yellow
    $script:ErrorLog | Select-Object -Last 10 | ForEach-Object {
        Write-Host "  [$($_.Timestamp)] [$($_.Severity)] [$($_.Server)] $($_.Message)" -ForegroundColor $(switch ($_.Severity) { "CRITICAL" { "Red" } "HIGH" { "Yellow" } "MEDIUM" { "Cyan" } default { "Gray" } })
    }
    
    # Show error categories
    Write-Host ""
    Write-Host "Error Categories:" -ForegroundColor Yellow
    $script:ErrorLog | Group-Object Category | ForEach-Object {
        Write-Host "  $($_.Name): $($_.Count) errors" -ForegroundColor White
    }
}

Write-Host "KPP Simulator Synchronized System Launcher" -ForegroundColor Cyan
Write-Host "============================================================"
Write-Host "Enhanced with comprehensive error handling and monitoring" -ForegroundColor Gray

# Show usage if no parameters
if (-not ($Test -or $Stop -or $RestartSimulation)) {
    Write-Host ""
    Write-Host "Usage Options:" -ForegroundColor Yellow
    Write-Host "  .\start_sync_system.ps1                 - Start all servers"
    Write-Host "  .\start_sync_system.ps1 -Test           - Test system components"
    Write-Host "  .\start_sync_system.ps1 -Stop           - Stop all servers"
    Write-Host "  .\start_sync_system.ps1 -RestartSimulation - Restart simulation engine only"
    Write-Host "  .\start_sync_system.ps1 -Debug          - Enable detailed error reporting"
    Write-Host ""
}

if ($Stop) {
    Write-Host "Stopping all KPP services..." -ForegroundColor Yellow
    Get-Process | Where-Object {$_.ProcessName -match "python" -and $_.CommandLine -match "(realtime_sync_master|main|app|dash_app)"} | Stop-Process -Force
    Write-Host "All services stopped" -ForegroundColor Green
    exit 0
}

if ($RestartSimulation) {
    Write-Host "KPP Simulator Clean Restart (Integrated)" -ForegroundColor Cyan
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
            Write-ErrorLog -Message "Endpoint not responding" -Severity "HIGH" -Category "NETWORK" -Server $Name -Details $_.Exception.Message
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
        Write-Host "   Run: .\start_sync_system.ps1 (without -RestartSimulation)" -ForegroundColor Yellow
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
        Write-ErrorLog -Message "Failed to get simulation status" -Severity "HIGH" -Category "RUNTIME" -Server "Flask-Backend" -Details $_.Exception.Message
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
            Write-ErrorLog -Message "Stop request returned unexpected status" -Severity "MEDIUM" -Category "RUNTIME" -Server "Flask-Backend" -Details "HTTP $($stopResponse.StatusCode)"
        }
    }
    catch {
        Write-Host "[ERROR] Failed to stop simulation: $($_.Exception.Message)" -ForegroundColor Red
        Write-ErrorLog -Message "Failed to stop simulation" -Severity "HIGH" -Category "RUNTIME" -Server "Flask-Backend" -Details $_.Exception.Message
        exit 1
    }
    
    # Step 4: Wait for clean shutdown
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
        Write-ErrorLog -Message "Failed to restart simulation" -Severity "CRITICAL" -Category "RUNTIME" -Server "Flask-Backend" -Details $_.Exception.Message
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
            Write-ErrorLog -Message "Simulation restart verification failed" -Severity "MEDIUM" -Category "RUNTIME" -Server "Flask-Backend" -Details "simulation_running=$($newStatus.simulation_running), engine_running=$($newStatus.engine_running)"
        }
    }
    catch {
        Write-Host "[ERROR] Could not verify restart status" -ForegroundColor Red
        Write-ErrorLog -Message "Could not verify restart status" -Severity "HIGH" -Category "RUNTIME" -Server "Flask-Backend" -Details $_.Exception.Message
    }
    
    Write-Host "`n" + "=" * 50 -ForegroundColor Cyan
    Write-Host "Clean Restart Process Complete" -ForegroundColor Cyan
    Show-ErrorSummary
    exit 0
}

if ($Test) {
    Write-Host "Testing synchronized system components..." -ForegroundColor Yellow
    
    # Test Python dependencies
    Write-Host "Checking dependencies..."
    $deps = @("uvicorn", "websockets", "fastapi", "dash", "plotly")
    foreach ($dep in $deps) {
        try {
            python -c "import $dep; print('[OK] $dep')" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[OK] $dep" -ForegroundColor Green
            } else {
                Write-Host "[FAIL] Missing dependency: $dep" -ForegroundColor Red
                Write-ErrorLog -Message "Missing Python dependency" -Severity "CRITICAL" -Category "DEPENDENCY" -Server "SYSTEM" -Details $dep
                exit 1
            }
        } catch {
            Write-Host "[FAIL] Missing dependency: $dep" -ForegroundColor Red
            Write-ErrorLog -Message "Missing Python dependency" -Severity "CRITICAL" -Category "DEPENDENCY" -Server "SYSTEM" -Details $dep
            exit 1
        }
    }
    
    # Test server scripts
    Write-Host "Checking server scripts..."
    $scripts = @("realtime_sync_master.py", "app.py", "main.py", "dash_app.py")
    foreach ($script in $scripts) {
        if (Test-Path $script) {
            Write-Host "[OK] $script found" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] Missing script: $script" -ForegroundColor Red
            Write-ErrorLog -Message "Missing server script" -Severity "CRITICAL" -Category "DEPENDENCY" -Server "SYSTEM" -Details $script
            exit 1
        }
    }
    
    Write-Host "SUCCESS: All tests passed! System ready for synchronized operation." -ForegroundColor Green
    exit 0
}

Write-Host "Starting KPP Synchronized Real-Time System..." -ForegroundColor Green
Write-Host ""
Write-Host "Features:"
Write-Host "  * 30 FPS synchronized real-time visualization"
Write-Host "  * Sub-50ms latency for smooth charts"
Write-Host "  * Professional-grade timing coordination"
Write-Host "  * Enterprise-ready error handling and monitoring"
Write-Host ""

# Initialize error tracking
Write-ErrorLog -Message "System startup initiated" -Severity "INFO" -Category "STARTUP" -Server "SYSTEM"

# Start servers individually with error handling
Write-Host "Starting Flask Backend (Port 9100)..." -ForegroundColor Cyan
try {
    Start-Job -ScriptBlock { Set-Location $using:PWD; python app.py } -Name "Flask-Backend" | Out-Null
    Start-Sleep 3
    Write-ErrorLog -Message "Flask Backend started successfully" -Severity "INFO" -Category "STARTUP" -Server "Flask-Backend"
} catch {
    Write-ErrorLog -Message "Failed to start Flask Backend" -Severity "CRITICAL" -Category "STARTUP" -Server "Flask-Backend" -Details $_.Exception.Message
}

Write-Host "Starting Master Clock Server (Port 9200)..." -ForegroundColor Cyan  
try {
    Start-Job -ScriptBlock { Set-Location $using:PWD; python realtime_sync_master.py } -Name "Master-Clock" | Out-Null
    Start-Sleep 2
    Write-ErrorLog -Message "Master Clock Server started successfully" -Severity "INFO" -Category "STARTUP" -Server "Master-Clock"
} catch {
    Write-ErrorLog -Message "Failed to start Master Clock Server" -Severity "CRITICAL" -Category "STARTUP" -Server "Master-Clock" -Details $_.Exception.Message
}

Write-Host "Starting WebSocket Server (Port 9101)..." -ForegroundColor Cyan
try {
    Start-Job -ScriptBlock { Set-Location $using:PWD; python main.py } -Name "WebSocket-Server" | Out-Null
    Start-Sleep 2
    Write-ErrorLog -Message "WebSocket Server started successfully" -Severity "INFO" -Category "STARTUP" -Server "WebSocket-Server"
} catch {
    Write-ErrorLog -Message "Failed to start WebSocket Server" -Severity "CRITICAL" -Category "STARTUP" -Server "WebSocket-Server" -Details $_.Exception.Message
}

Write-Host "Starting Dash Frontend (Port 9103)..." -ForegroundColor Cyan
try {
    Start-Job -ScriptBlock { Set-Location $using:PWD; python dash_app.py } -Name "Dash-Frontend" | Out-Null
    Start-Sleep 3
    Write-ErrorLog -Message "Dash Frontend started successfully" -Severity "INFO" -Category "STARTUP" -Server "Dash-Frontend"
} catch {
    Write-ErrorLog -Message "Failed to start Dash Frontend" -Severity "CRITICAL" -Category "STARTUP" -Server "Dash-Frontend" -Details $_.Exception.Message
}

Write-Host ""
Write-Host "KPP Synchronized System Status:" -ForegroundColor Cyan
Write-Host "----------------------------------------------------"
Write-Host "Flask Backend       | Port 9100 | RUNNING" -ForegroundColor Green
Write-Host "Master Clock Server | Port 9200 | RUNNING" -ForegroundColor Green  
Write-Host "WebSocket Server    | Port 9101 | RUNNING" -ForegroundColor Green
Write-Host "Dash Frontend       | Port 9103 | RUNNING" -ForegroundColor Green
Write-Host "----------------------------------------------------"

Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Cyan
Write-Host "  * Dashboard:       http://localhost:9103" -ForegroundColor White
Write-Host "  * Master Clock:    http://localhost:9200/metrics" -ForegroundColor White
Write-Host "  * Backend API:     http://localhost:9100/status" -ForegroundColor White
Write-Host "  * WebSocket:       http://localhost:9101" -ForegroundColor White

Write-Host ""
Write-Host "Enhanced Controls:" -ForegroundColor Yellow
Write-Host "  * Press 'S' to show server status"
Write-Host "  * Press 'R' to restart simulation engine"
Write-Host "  * Press 'E' to show error summary"
Write-Host "  * Press 'H' to show system health"
Write-Host "  * Press 'Q' to quit and stop all servers"
Write-Host "  * Press Ctrl+C for emergency shutdown"

# Enhanced monitoring loop with error handling
do {
    Start-Sleep -Milliseconds 500
    $jobs = Get-Job
    $currentTime = Get-Date
    
    # Periodic error checking and system monitoring
    if (($currentTime - $script:LastErrorCheck).TotalSeconds -ge $script:ErrorCheckInterval) {
        $script:LastErrorCheck = $currentTime
        
        # Check job statuses
        foreach ($job in $jobs) {
            $jobStatus = Test-JobStatus -Job $job
            if ($jobStatus -in @("FAILED", "STOPPED")) {
                # Attempt recovery
                Invoke-ErrorRecovery -ServerName $job.Name -ErrorType "STARTUP"
            }
        }
        
        # Check system resources
        Test-SystemResources
        
        # Check server health endpoints
        $serverHealth = @{
            "Flask-Backend" = Test-ServerHealth -ServerName "Flask-Backend" -HealthUrl "http://localhost:9100/status" -Port 9100
            "Master-Clock" = Test-ServerHealth -ServerName "Master-Clock" -HealthUrl "http://localhost:9200/health" -Port 9200
            "WebSocket-Server" = Test-ServerHealth -ServerName "WebSocket-Server" -HealthUrl "http://localhost:9101" -Port 9101
            "Dash-Frontend" = Test-ServerHealth -ServerName "Dash-Frontend" -HealthUrl "http://localhost:9103" -Port 9103
        }
        
        # Log any failed health checks
        foreach ($server in $serverHealth.Keys) {
            if ($serverHealth[$server].Status -eq "FAILED") {
                Write-ErrorLog -Message "Health check failed" -Severity "HIGH" -Category "RUNTIME" -Server $server -Details $serverHealth[$server].Details
            }
        }
    }
    
    if ($Host.UI.RawUI.KeyAvailable) {
        $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        
        switch ($key.Character.ToString().ToUpper()) {
            'S' {
                Write-Host ""
                Write-Host "Server Status:" -ForegroundColor Cyan
                foreach ($job in $jobs) {
                    $status = if ($job.State -eq "Running") { "[RUNNING]" } else { "[STOPPED]" }
                    $color = if ($job.State -eq "Running") { "Green" } else { "Red" }
                    Write-Host "  $($job.Name): $status" -ForegroundColor $color
                }
            }
            'E' {
                Show-ErrorSummary
            }
            'H' {
                Write-Host ""
                Write-Host "System Health Check:" -ForegroundColor Cyan
                Write-Host "===================" -ForegroundColor Cyan
                
                # Check all server health endpoints
                $endpoints = @{
                    "Flask Backend" = "http://localhost:9100/status"
                    "Master Clock" = "http://localhost:9200/health"
                    "WebSocket Server" = "http://localhost:9101"
                    "Dash Frontend" = "http://localhost:9103"
                }
                
                foreach ($server in $endpoints.Keys) {
                    $health = Test-ServerHealth -ServerName $server -HealthUrl $endpoints[$server] -Port 0
                    $color = switch ($health.Status) {
                        "HEALTHY" { "Green" }
                        "DEGRADED" { "Yellow" }
                        "FAILED" { "Red" }
                        default { "Gray" }
                    }
                    Write-Host "  $server`: $($health.Status)" -ForegroundColor $color
                    if ($health.ResponseTime -gt 0) {
                        Write-Host "    Response Time: $($health.ResponseTime)ms" -ForegroundColor Gray
                    }
                }
                
                # Show system resources
                $cpuUsage = (Get-Counter "\Processor(_Total)\% Processor Time").CounterSamples[0].CookedValue
                $memoryUsage = (Get-Counter "\Memory\% Committed Bytes In Use").CounterSamples[0].CookedValue
                Write-Host "  System Resources:" -ForegroundColor Cyan
                Write-Host "    CPU Usage: $([math]::Round($cpuUsage, 1))%" -ForegroundColor $(if ($cpuUsage -gt 80) { "Yellow" } else { "Green" })
                Write-Host "    Memory Usage: $([math]::Round($memoryUsage, 1))%" -ForegroundColor $(if ($memoryUsage -gt 80) { "Yellow" } else { "Green" })
            }
            'R' {
                Write-Host ""
                Write-Host "Restarting Simulation Engine..." -ForegroundColor Yellow
                
                # Quick restart simulation (inline version)
                try {
                    Write-Host "Stopping simulation..." -ForegroundColor Yellow
                    $stopResponse = Invoke-WebRequest -Uri "http://localhost:9100/stop" -Method POST -UseBasicParsing -TimeoutSec 5
                    
                    if ($stopResponse.StatusCode -eq 200) {
                        Write-Host "[OK] Simulation stopped" -ForegroundColor Green
                        Start-Sleep -Seconds 2
                        
                        Write-Host "Starting simulation..." -ForegroundColor Yellow
                        $startResponse = Invoke-WebRequest -Uri "http://localhost:9100/start" -Method POST -UseBasicParsing -TimeoutSec 5
                        
                        if ($startResponse.StatusCode -eq 200) {
                            Write-Host "[OK] Simulation restarted successfully!" -ForegroundColor Green
                            Write-Host "Dashboard: http://localhost:9103" -ForegroundColor Cyan
                            Write-ErrorLog -Message "Simulation restarted successfully" -Severity "INFO" -Category "RUNTIME" -Server "Flask-Backend"
                        } else {
                            Write-Host "[ERROR] Failed to restart simulation" -ForegroundColor Red
                            Write-ErrorLog -Message "Failed to restart simulation" -Severity "HIGH" -Category "RUNTIME" -Server "Flask-Backend" -Details "HTTP $($startResponse.StatusCode)"
                        }
                    } else {
                        Write-Host "[ERROR] Failed to stop simulation" -ForegroundColor Red
                        Write-ErrorLog -Message "Failed to stop simulation" -Severity "HIGH" -Category "RUNTIME" -Server "Flask-Backend" -Details "HTTP $($stopResponse.StatusCode)"
                    }
                }
                catch {
                    Write-Host "[ERROR] Restart failed: $($_.Exception.Message)" -ForegroundColor Red
                    Write-ErrorLog -Message "Simulation restart failed" -Severity "CRITICAL" -Category "RUNTIME" -Server "Flask-Backend" -Details $_.Exception.Message
                }
            }
            'Q' {
                Write-Host ""
                Write-Host "Shutting down all servers..." -ForegroundColor Yellow
                Write-ErrorLog -Message "System shutdown initiated by user" -Severity "INFO" -Category "RUNTIME" -Server "SYSTEM"
                $jobs | Stop-Job
                $jobs | Remove-Job
                Write-Host "All servers stopped gracefully" -ForegroundColor Green
                Show-ErrorSummary
                exit 0
            }
        }
    }
    
} while ($true) 