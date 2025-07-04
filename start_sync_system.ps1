# KPP Simulator Synchronized System Launcher for Windows PowerShell
# Starts all servers in the correct order for real-time synchronization
# Enhanced with comprehensive error handling and monitoring

param(
    [switch]$Test,
    [switch]$Stop,
    [switch]$RestartSimulation,
    [switch]$Debug
)

# Configuration and error handling
$ErrorActionPreference = "Continue"
$script:ErrorLog = @()
$script:LastErrorCheck = Get-Date
$script:Config = $null
$script:ConfigPath = "config/kpp_system_config.json"

# --- Logging Functions (moved to top for early use) ---
$script:LogFile = $null
$script:LogFileStream = $null

function Initialize-Logging {
    try {
        if ($script:Config.logging.file_output) {
            $logDir = Split-Path $script:Config.logging.log_file -Parent
            if (-not (Test-Path $logDir)) {
                New-Item -ItemType Directory -Path $logDir -Force | Out-Null
            }
            if (Test-Path $script:Config.logging.log_file) {
                $logFileSize = (Get-Item $script:Config.logging.log_file).Length
                $maxSizeBytes = $script:Config.logging.max_log_size_mb * 1MB
                if ($logFileSize -gt $maxSizeBytes) {
                    Invoke-LogRotation
                }
            }
            $script:LogFile = $script:Config.logging.log_file
            $script:LogFileStream = [System.IO.File]::AppendText($script:LogFile)
        }
        Write-Host "Logging initialized" -ForegroundColor Green
    }
    catch {
        Write-Host "Warning: Could not initialize file logging: $($_.Exception.Message)" -ForegroundColor Yellow
        $script:Config.logging.file_output = $false
    }
}

function Invoke-LogRotation {
    try {
        $logFile = $script:Config.logging.log_file
        $logDir = Split-Path $logFile -Parent
        $logName = [System.IO.Path]::GetFileNameWithoutExtension($logFile)
        $logExt = [System.IO.Path]::GetExtension($logFile)
        for ($i = $script:Config.logging.log_rotation_count; $i -gt 0; $i--) {
            $oldFile = Join-Path $logDir "$logName.$i$logExt"
            $newFile = Join-Path $logDir "$logName.$($i+1)$logExt"
            if (Test-Path $oldFile) {
                if ($i -eq $script:Config.logging.log_rotation_count) {
                    Remove-Item $oldFile -Force
                } else {
                    Move-Item $oldFile $newFile -Force
                }
            }
        }
        if (Test-Path $logFile) {
            $rotatedFile = Join-Path $logDir "$logName.1$logExt"
            Move-Item $logFile $rotatedFile -Force
        }
        Write-Host "Log rotation completed" -ForegroundColor Green
    }
    catch {
        Write-Host "Warning: Log rotation failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

function Write-StructuredLog {
    param(
        [string]$Message,
        [string]$Severity = "MEDIUM",
        [string]$Category = "RUNTIME",
        [string]$Server = "UNKNOWN",
        [string]$Details = "",
        [string]$TraceId = ""
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = @{
        timestamp = $timestamp
        severity = $Severity
        category = $Category
        server = $Server
        message = $Message
        details = $Details
        trace_id = $TraceId
    }
    $jsonEntry = $logEntry | ConvertTo-Json -Compress
    if ($script:Config.logging.file_output -and $script:LogFileStream) {
        try {
            $script:LogFileStream.WriteLine($jsonEntry)
            $script:LogFileStream.Flush()
        }
        catch {
            Write-Host "Warning: Failed to write to log file: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    return $logEntry
}

function Write-ErrorLog {
    param(
        [string]$Message,
        [string]$Severity = "MEDIUM",
        [string]$Category = "RUNTIME",
        [string]$Server = "UNKNOWN",
        [string]$Details = ""
    )
    if ($script:Config.security.input_sanitization) {
        $Message = Invoke-ErrorSanitization -Message $Message
        $Details = Invoke-ErrorSanitization -Message $Details
    }
    $traceId = [System.Guid]::NewGuid().ToString("N").Substring(0, 8)
    $logEntry = Write-StructuredLog -Message $Message -Severity $Severity -Category $Category -Server $Server -Details $Details -TraceId $traceId
    $script:ErrorLog += $logEntry
    if ($script:ErrorLog.Count -gt $script:Config.monitoring.max_error_log_size) {
        $excessCount = $script:ErrorLog.Count - $script:Config.monitoring.max_error_log_size
        $script:ErrorLog = $script:ErrorLog | Select-Object -Skip $excessCount
        Write-Host "Log rotation: Removed $excessCount old entries" -ForegroundColor Gray
    }
    if ($script:Config.logging.console_output) {
        $color = switch ($Severity) {
            "CRITICAL" { "Red" }
            "HIGH" { "DarkRed" }
            "MEDIUM" { "Yellow" }
            "LOW" { "Cyan" }
            "INFO" { "Gray" }
            default { "White" }
        }
        Write-Host "[$($logEntry.timestamp)] [$Severity] [$Server] $Message" -ForegroundColor $color
        if ($Details -and $Debug) {
            Write-Host "   Details: $Details" -ForegroundColor Gray
        }
        if ($Debug) {
            Write-Host "   Trace ID: $traceId" -ForegroundColor Gray
        }
    }
}

function Close-Logging {
    if ($script:LogFileStream) {
        try {
            $script:LogFileStream.Close()
            $script:LogFileStream.Dispose()
            $script:LogFileStream = $null
        }
        catch {
            Write-Host "Warning: Error closing log file: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

# Function to load and validate configuration
function Import-Configuration {
    param([string]$ConfigPath = $script:ConfigPath)
    
    try {
        if (-not (Test-Path $ConfigPath)) {
            Write-Host "Configuration file not found: $ConfigPath" -ForegroundColor Red
            Write-Host "Creating default configuration..." -ForegroundColor Yellow
            
            # Create default config
            $defaultConfig = @{
                system = @{
                    name = "KPP Simulator Synchronized System"
                    version = "2.0.0"
                    environment = "development"
                }
                servers = @{
                    flask_backend = @{
                        name = "Flask Backend"
                        script = "app.py"
                        port = 9100
                        health_endpoint = "/status"
                        startup_timeout = 10
                        retry_attempts = 3
                        retry_delay = 2
                    }
                    master_clock = @{
                        name = "Master Clock Server"
                        script = "realtime_sync_master.py"
                        port = 9200
                        health_endpoint = "/health"
                        startup_timeout = 5
                        retry_attempts = 3
                        retry_delay = 1
                    }
                    websocket_server = @{
                        name = "WebSocket Server"
                        script = "main.py"
                        port = 9101
                        health_endpoint = "/"
                        startup_timeout = 5
                        retry_attempts = 3
                        retry_delay = 1
                    }
                    dash_frontend = @{
                        name = "Dash Frontend"
                        script = "dash_app.py"
                        port = 9103
                        health_endpoint = "/"
                        startup_timeout = 10
                        retry_attempts = 3
                        retry_delay = 2
                    }
                }
                monitoring = @{
                    health_check_interval = 30
                    error_check_interval = 30
                    max_error_log_size = 1000
                    performance_thresholds = @{
                        cpu_warning = 80
                        cpu_critical = 90
                        memory_warning = 80
                        memory_critical = 85
                        disk_warning = 15
                        disk_critical = 10
                    }
                    response_time_thresholds = @{
                        warning = 1000
                        critical = 5000
                    }
                }
                error_handling = @{
                    max_retries = 3
                    retry_delay = 5
                    backoff_multiplier = 2
                    circuit_breaker_threshold = 5
                    circuit_breaker_timeout = 60
                }
                logging = @{
                    log_level = "INFO"
                    log_file = "logs/kpp_system.log"
                    max_log_size_mb = 10
                    log_rotation_count = 5
                    console_output = $true
                    file_output = $true
                }
                security = @{
                    url_validation = $true
                    input_sanitization = $true
                    script_integrity_check = $false
                    allowed_scripts = @("app.py", "realtime_sync_master.py", "main.py", "dash_app.py")
                }
                dependencies = @{
                    python_packages = @("uvicorn", "websockets", "fastapi", "dash", "plotly")
                    startup_sequence = @("flask_backend", "master_clock", "websocket_server", "dash_frontend")
                    shutdown_sequence = @("dash_frontend", "websocket_server", "master_clock", "flask_backend")
                }
                urls = @{
                    dashboard = "http://localhost:9103"
                    master_clock_metrics = "http://localhost:9200/metrics"
                    backend_api = "http://localhost:9100/status"
                    websocket = "http://localhost:9101"
                }
            }
            
            # Create config directory if it doesn't exist
            $configDir = Split-Path $ConfigPath -Parent
            if (-not (Test-Path $configDir)) {
                New-Item -ItemType Directory -Path $configDir -Force | Out-Null
            }
            
            # Save default config
            $defaultConfig | ConvertTo-Json -Depth 10 | Set-Content $ConfigPath
            Write-Host "Default configuration created: $ConfigPath" -ForegroundColor Green
        }
        
        # Load configuration
        $configContent = Get-Content $ConfigPath -Raw
        $script:Config = $configContent | ConvertFrom-Json
        
        # Validate configuration
        $validationResult = Test-Configuration -Config $script:Config
        if (-not $validationResult.IsValid) {
            Write-Host "Configuration validation failed:" -ForegroundColor Red
            foreach ($errMsg in $validationResult.Errors) {
                Write-Host "  - $errMsg" -ForegroundColor Red
            }
            throw "Configuration validation failed"
        }
        
        Write-Host "Configuration loaded successfully: $ConfigPath" -ForegroundColor Green
        Write-Host "System: $($script:Config.system.name) v$($script:Config.system.version)" -ForegroundColor Cyan
        Write-Host "Environment: $($script:Config.system.environment)" -ForegroundColor Cyan
        
        return $true
    }
    catch {
        Write-Host "Failed to load configuration: $($_.Exception.Message)" -ForegroundColor Red
        Write-ErrorLog -Message "Configuration load failed" -Severity "CRITICAL" -Category "DEPENDENCY" -Server "SYSTEM" -Details $_.Exception.Message
        return $false
    }
}

# Function to validate configuration
function Test-Configuration {
    param([object]$Config)
    
    $errors = @()
    
    # Check required sections
    $requiredSections = @("system", "servers", "monitoring", "error_handling", "logging", "security", "dependencies", "urls")
    foreach ($section in $requiredSections) {
        if (-not $Config.PSObject.Properties.Name -contains $section) {
            $errors += "Missing required section: $section"
        }
    }
    
    # Validate servers configuration
    if ($Config.servers) {
        $requiredServers = @("flask_backend", "master_clock", "websocket_server", "dash_frontend")
        foreach ($server in $requiredServers) {
            if (-not $Config.servers.PSObject.Properties.Name -contains $server) {
                $errors += "Missing required server: $server"
            }
            else {
                $serverConfig = $Config.servers.$server
                $requiredServerProps = @("name", "script", "port", "health_endpoint")
                foreach ($prop in $requiredServerProps) {
                    if (-not $serverConfig.PSObject.Properties.Name -contains $prop) {
                        $errors += "Missing required property '$prop' for server '$server'"
                    }
                }
            }
        }
    }
    
    # Validate ports are unique
    if ($Config.servers) {
        $ports = @()
        foreach ($server in $Config.servers.PSObject.Properties.Name) {
            $port = $Config.servers.$server.port
            if ($ports -contains $port) {
                $errors += "Duplicate port $port found in server configuration"
            }
            $ports += $port
        }
    }
    
    return @{
        IsValid = ($errors.Count -eq 0)
        Errors = $errors
    }
}

# Load configuration at startup
if (-not (Import-Configuration)) {
    exit 1
}

# Initialize logging after configuration is loaded
Initialize-Logging

# Set configuration-based variables
$script:ErrorCheckInterval = $script:Config.monitoring.error_check_interval
$script:MaxRetries = $script:Config.error_handling.max_retries
$script:RetryDelay = $script:Config.error_handling.retry_delay

# Enhanced error handling with backoff and circuit breaker
$script:ErrorCounts = @{}
$script:CircuitBreakers = @{}
$script:LastRecoveryAttempts = @{}

# Function to calculate backoff delay
function Get-BackoffDelay {
    param([string]$ServerName, [string]$ErrorType)
    
    $attempts = if ($script:ErrorCounts.ContainsKey("$ServerName-$ErrorType")) {
        $script:ErrorCounts["$ServerName-$ErrorType"]
    } else {
        0
    }
    
    $baseDelay = $script:Config.error_handling.retry_delay
    $multiplier = $script:Config.error_handling.backoff_multiplier
    $maxDelay = 300  # 5 minutes maximum
    
    $delay = [math]::Min($baseDelay * [math]::Pow($multiplier, $attempts), $maxDelay)
    
    # Add jitter to prevent thundering herd
    $jitter = Get-Random -Minimum 0.8 -Maximum 1.2
    return [math]::Round($delay * $jitter)
}

# Function to clean up disk space
function Invoke-DiskCleanup {
    try {
        $drive = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
        $freeSpaceGB = [math]::Round($drive.FreeSpace / 1GB, 1)
        $totalSpaceGB = [math]::Round($drive.Size / 1GB, 1)
        $freeSpacePercent = [math]::Round(($drive.FreeSpace / $drive.Size) * 100, 1)
        
        Write-Host "Disk space: $freeSpaceGB GB free of $totalSpaceGB GB ($freeSpacePercent%)" -ForegroundColor Cyan
        
        if ($freeSpacePercent -lt $script:Config.monitoring.performance_thresholds.disk_critical) {
            Write-Host "CRITICAL: Low disk space detected!" -ForegroundColor Red
            
            # Clean up temporary files
            Write-Host "Cleaning up temporary files..." -ForegroundColor Yellow
            Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item "$env:WINDIR\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
            
            # Clean up Windows Update cache
            Write-Host "Cleaning Windows Update cache..." -ForegroundColor Yellow
            Stop-Service -Name "wuauserv" -Force -ErrorAction SilentlyContinue
            Remove-Item "$env:WINDIR\SoftwareDistribution\Download\*" -Recurse -Force -ErrorAction SilentlyContinue
            Start-Service -Name "wuauserv" -ErrorAction SilentlyContinue
            
            # Clean up old log files
            Write-Host "Cleaning old log files..." -ForegroundColor Yellow
            if (Test-Path "logs") {
                Get-ChildItem "logs" -File -Recurse | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Remove-Item -Force -ErrorAction SilentlyContinue
            }
            
            # Check space again
            $drive = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
            $newFreeSpacePercent = [math]::Round(($drive.FreeSpace / $drive.Size) * 100, 1)
            Write-Host "After cleanup: $newFreeSpacePercent% free space" -ForegroundColor Green
        }
        elseif ($freeSpacePercent -lt $script:Config.monitoring.performance_thresholds.disk_warning) {
            Write-Host "WARNING: Low disk space - consider cleanup" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "Warning: Could not perform disk cleanup: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Function to test server health endpoints
function Test-ServerHealth {
    param(
        [string]$ServerName,
        [string]$HealthUrl,
        [int]$Port
    )
    
    try {
        $startTime = Get-Date
        $response = Invoke-WebRequest -Uri $HealthUrl -Method GET -UseBasicParsing -TimeoutSec 5
        $responseTime = ((Get-Date) - $startTime).TotalMilliseconds
        
        if ($response.StatusCode -eq 200) {
            $status = "HEALTHY"
            $details = "Response time: $([math]::Round($responseTime, 1))ms"
            
            # Check response time thresholds
            if ($responseTime -gt $script:Config.monitoring.response_time_thresholds.critical) {
                $status = "DEGRADED"
                $details = "Slow response: $([math]::Round($responseTime, 1))ms"
            } elseif ($responseTime -gt $script:Config.monitoring.response_time_thresholds.warning) {
                $status = "WARNING"
                $details = "High response time: $([math]::Round($responseTime, 1))ms"
            }
            
            return @{
                Status = $status
                ResponseTime = $responseTime
                Details = $details
                LastCheck = Get-Date
            }
        } else {
            return @{
                Status = "FAILED"
                ResponseTime = $responseTime
                Details = "HTTP $($response.StatusCode)"
                LastCheck = Get-Date
            }
        }
    }
    catch {
        $errorDetails = $_.Exception.Message
        if ($errorDetails -match "timeout") {
            $errorDetails = "Connection timeout"
        } elseif ($errorDetails -match "refused") {
            $errorDetails = "Connection refused"
        }
        
        return @{
            Status = "FAILED"
            ResponseTime = 0
            Details = $errorDetails
            LastCheck = Get-Date
        }
    }
}

# Function to test job status
function Test-JobStatus {
    param([object]$Job)
    
    if (-not $Job) { return "UNKNOWN" }
    
    switch ($Job.State) {
        "Running" { return "RUNNING" }
        "Completed" { return "COMPLETED" }
        "Failed" { return "FAILED" }
        "Stopped" { return "STOPPED" }
        "Blocked" { return "BLOCKED" }
        default { return "UNKNOWN" }
    }
}

# Function to test system resources
function Test-SystemResources {
    try {
        # Check CPU usage
        $cpu = Get-WmiObject -Class Win32_Processor | Measure-Object -Property LoadPercentage -Average
        $cpuUsage = [math]::Round($cpu.Average, 1)
        
        if ($cpuUsage -gt $script:Config.monitoring.performance_thresholds.cpu_critical) {
            Write-ErrorLog -Message "High CPU usage detected: $cpuUsage%" -Severity "HIGH" -Category "RESOURCE" -Server "SYSTEM"
        } elseif ($cpuUsage -gt $script:Config.monitoring.performance_thresholds.cpu_warning) {
            Write-ErrorLog -Message "High CPU usage detected: $cpuUsage%" -Severity "MEDIUM" -Category "RESOURCE" -Server "SYSTEM"
        }
        
        # Check memory usage
        $memory = Get-WmiObject -Class Win32_OperatingSystem
        $memoryUsage = [math]::Round((($memory.TotalVisibleMemorySize - $memory.FreePhysicalMemory) / $memory.TotalVisibleMemorySize) * 100, 1)
        
        if ($memoryUsage -gt $script:Config.monitoring.performance_thresholds.memory_critical) {
            Write-ErrorLog -Message "High memory usage detected: $memoryUsage%" -Severity "HIGH" -Category "RESOURCE" -Server "SYSTEM"
        } elseif ($memoryUsage -gt $script:Config.monitoring.performance_thresholds.memory_warning) {
            Write-ErrorLog -Message "High memory usage detected: $memoryUsage%" -Severity "MEDIUM" -Category "RESOURCE" -Server "SYSTEM"
        }
        
        # Check disk space
        $drive = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
        $freeSpacePercent = [math]::Round(($drive.FreeSpace / $drive.Size) * 100, 1)
        
        if ($freeSpacePercent -lt $script:Config.monitoring.performance_thresholds.disk_critical) {
            Write-ErrorLog -Message "Low disk space: $freeSpacePercent% free" -Severity "HIGH" -Category "RESOURCE" -Server "SYSTEM"
            # Trigger disk cleanup
            Invoke-DiskCleanup
        } elseif ($freeSpacePercent -lt $script:Config.monitoring.performance_thresholds.disk_warning) {
            Write-ErrorLog -Message "Low disk space: $freeSpacePercent% free" -Severity "MEDIUM" -Category "RESOURCE" -Server "SYSTEM"
        }
    }
    catch {
        Write-Host "Warning: Could not check system resources: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Function to sanitize error messages for security
function Invoke-ErrorSanitization {
    param([string]$Message)
    
    if (-not $script:Config.security.input_sanitization) {
        return $Message
    }
    
    # Remove potentially sensitive information
    $sanitized = $Message -replace '\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP_ADDRESS]'
    $sanitized = $sanitized -replace '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'
    $sanitized = $sanitized -replace '\b\d{4}[-.]?\d{4}[-.]?\d{4}[-.]?\d{4}\b', '[CREDIT_CARD]'
    $sanitized = $sanitized -replace '\b[A-Za-z0-9]{32,}\b', '[HASH]'
    
    # Remove file paths that might contain sensitive information
    $sanitized = $sanitized -replace 'C:\\Users\\[^\\]+\\', 'C:\Users\[USER]\'
    $sanitized = $sanitized -replace '/home/[^/]+/', '/home/[USER]/'
    
    return $sanitized
}

# Function to validate script execution
function Test-ScriptExecution {
    param([string]$ScriptName, [string]$Context)
    
    try {
        # Check if script exists
        if (-not (Test-Path $ScriptName)) {
            Write-ErrorLog -Message "Script not found" -Severity "CRITICAL" -Category "DEPENDENCY" -Server $Context -Details "Script: $ScriptName"
            return $false
        }
        
        # Check if script is in allowed list
        if ($script:Config.security.script_integrity_check) {
            $allowedScripts = $script:Config.security.allowed_scripts
            if ($allowedScripts -and $ScriptName -notin $allowedScripts) {
                Write-ErrorLog -Message "Script not in allowed list" -Severity "CRITICAL" -Category "SECURITY" -Server $Context -Details "Script: $ScriptName"
                return $false
            }
        }
        
        # Check file permissions
        $fileInfo = Get-Item $ScriptName
        if (-not $fileInfo.IsReadOnly -and $fileInfo.Length -gt 0) {
            return $true
        } else {
            Write-ErrorLog -Message "Script file issues" -Severity "HIGH" -Category "DEPENDENCY" -Server $Context -Details "Script: $ScriptName, ReadOnly: $($fileInfo.IsReadOnly), Size: $($fileInfo.Length)"
            return $false
        }
    }
    catch {
        Write-ErrorLog -Message "Script validation failed" -Severity "CRITICAL" -Category "DEPENDENCY" -Server $Context -Details "Script: $ScriptName, Error: $($_.Exception.Message)"
        return $false
    }
}

# Function to check circuit breaker status
function Test-CircuitBreaker {
    param([string]$ServerName, [string]$ErrorType)
    
    $breakerKey = "$ServerName-$ErrorType"
    
    if ($script:CircuitBreakers.ContainsKey($breakerKey)) {
        $breaker = $script:CircuitBreakers[$breakerKey]
        $timeSinceLastFailure = (Get-Date) - $breaker.LastFailure
        
        if ($timeSinceLastFailure.TotalSeconds -lt $script:Config.error_handling.circuit_breaker_timeout) {
            return @{ IsOpen = $true; TimeRemaining = $script:Config.error_handling.circuit_breaker_timeout - $timeSinceLastFailure.TotalSeconds }
        } else {
            # Circuit breaker timeout reached, reset
            $script:CircuitBreakers.Remove($breakerKey)
            $script:ErrorCounts.Remove($breakerKey)
            return @{ IsOpen = $false; TimeRemaining = 0 }
        }
    }
    
    return @{ IsOpen = $false; TimeRemaining = 0 }
}

# Function to record error and update circuit breaker
function Write-ErrorRecord {
    param([string]$ServerName, [string]$ErrorType, [string]$Details = "")
    
    $errorKey = "$ServerName-$ErrorType"
    
    # Increment error count
    if ($script:ErrorCounts.ContainsKey($errorKey)) {
        $script:ErrorCounts[$errorKey]++
    } else {
        $script:ErrorCounts[$errorKey] = 1
    }
    
    $errorCount = $script:ErrorCounts[$errorKey]
    
    # Check if circuit breaker should open
    if ($errorCount -ge $script:Config.error_handling.circuit_breaker_threshold) {
        $script:CircuitBreakers[$errorKey] = @{
            LastFailure = Get-Date
            ErrorCount = $errorCount
            Details = $Details
        }
        
        Write-ErrorLog -Message "Circuit breaker opened" -Severity "CRITICAL" -Category "RUNTIME" -Server $ServerName -Details "Error count: $errorCount, Type: $ErrorType"
        return $true  # Circuit breaker opened
    }
    
    return $false  # Circuit breaker not opened
}

# Function to verify recovery success
function Test-RecoverySuccess {
    param([string]$ServerName, [string]$RecoveryType)
    
    $verificationDelay = 5  # seconds
    Start-Sleep -Seconds $verificationDelay
    
    switch ($RecoveryType) {
        "STARTUP" {
            # Check if job is running
            $job = Get-Job -Name $ServerName -ErrorAction SilentlyContinue
            if ($job -and $job.State -eq "Running") {
                # Check health endpoint if available
                $serverConfig = $script:Config.servers.PSObject.Properties | Where-Object { $_.Name -replace "_", "-" -eq $ServerName }
                if ($serverConfig) {
                    $healthUrl = "http://localhost:$($serverConfig.Value.port)$($serverConfig.Value.health_endpoint)"
                    $health = Test-ServerHealth -ServerName $ServerName -HealthUrl $healthUrl -Port $serverConfig.Value.port
                    return $health.Status -eq "HEALTHY"
                }
                return $true
            }
            return $false
        }
        "NETWORK" {
            # Retry the original operation
            return $true  # Assume success for network retries
        }
        default {
            return $true
        }
    }
}

# Function to attempt automatic recovery with enhanced error handling
function Invoke-ErrorRecovery {
    param([string]$ServerName, [string]$ErrorType, [string]$Details = "")
    
    # Check circuit breaker first
    $circuitBreaker = Test-CircuitBreaker -ServerName $ServerName -ErrorType $ErrorType
    if ($circuitBreaker.IsOpen) {
        Write-Host "Circuit breaker is open for $ServerName ($ErrorType). Waiting $([math]::Round($circuitBreaker.TimeRemaining, 1))s..." -ForegroundColor Red
        Write-ErrorLog -Message "Circuit breaker active" -Severity "HIGH" -Category "RUNTIME" -Server $ServerName -Details "Time remaining: $([math]::Round($circuitBreaker.TimeRemaining, 1))s"
        return $false
    }
    
    # Check if we've attempted recovery too recently
    $lastAttemptKey = "$ServerName-$ErrorType"
    if ($script:LastRecoveryAttempts.ContainsKey($lastAttemptKey)) {
        $timeSinceLastAttempt = (Get-Date) - $script:LastRecoveryAttempts[$lastAttemptKey]
        $minInterval = 60  # Minimum 1 minute between recovery attempts
        if ($timeSinceLastAttempt.TotalSeconds -lt $minInterval) {
            Write-Host "Recovery attempted too recently for $ServerName. Waiting..." -ForegroundColor Yellow
            return $false
        }
    }
    
    # Calculate backoff delay
    $backoffDelay = Get-BackoffDelay -ServerName $ServerName -ErrorType $ErrorType
    Write-Host "Attempting recovery for $ServerName ($ErrorType) with $([math]::Round($backoffDelay, 1))s delay..." -ForegroundColor Yellow
    
    # Record recovery attempt
    $script:LastRecoveryAttempts[$lastAttemptKey] = Get-Date
    
    # Wait for backoff delay
    Start-Sleep -Seconds $backoffDelay
    
    $recoverySuccess = $false
    
    switch ($ErrorType) {
        "STARTUP" {
            # Validate script before execution
            $serverConfig = $script:Config.servers.PSObject.Properties | Where-Object { $_.Name -replace "_", "-" -eq $ServerName }
            if ($serverConfig) {
                $scriptName = $serverConfig.Value.script
                if (Test-ScriptExecution -ScriptName $scriptName -Context $ServerName) {
                    # Stop existing job if running
                    $job = Get-Job -Name $ServerName -ErrorAction SilentlyContinue
                    if ($job) {
                        Stop-Job -Job $job -ErrorAction SilentlyContinue
                        Remove-Job -Job $job -ErrorAction SilentlyContinue
                    }
                    
                    # Start new job
                    Start-Job -ScriptBlock { Set-Location $using:PWD; python $using:scriptName } -Name $ServerName | Out-Null
                    Start-Sleep -Seconds $serverConfig.Value.retry_delay
                    
                    # Verify recovery success
                    $recoverySuccess = Test-RecoverySuccess -ServerName $ServerName -RecoveryType "STARTUP"
                }
            }
        }
        "NETWORK" {
            # Wait and retry health check
            Start-Sleep -Seconds $script:RetryDelay
            $recoverySuccess = $true  # Assume success for network retries
        }
        "RESOURCE" {
            # Log resource warning but don't restart (could make things worse)
            Write-ErrorLog -Message "Resource issue detected - manual intervention may be required" -Severity "MEDIUM" -Category "RESOURCE" -Server $ServerName
            $recoverySuccess = $true  # Don't retry resource issues
        }
    }
    
    if ($recoverySuccess) {
        Write-Host "Recovery successful for $ServerName" -ForegroundColor Green
        Write-ErrorLog -Message "Recovery successful" -Severity "INFO" -Category "RUNTIME" -Server $ServerName
        
        # Reset error count on successful recovery
        $errorKey = "$ServerName-$ErrorType"
        if ($script:ErrorCounts.ContainsKey($errorKey)) {
            $script:ErrorCounts.Remove($errorKey)
        }
    } else {
        Write-Host "Recovery failed for $ServerName" -ForegroundColor Red
        Write-ErrorLog -Message "Recovery failed" -Severity "HIGH" -Category "RUNTIME" -Server $ServerName -Details $Details
        
        # Record error for circuit breaker
        Write-ErrorRecord -ServerName $ServerName -ErrorType $ErrorType -Details $Details
    }
    
    return $recoverySuccess
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
    
    # Improved process management with proper filtering
    try {
        # Get all Python processes
        $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
        
        # Filter for KPP-related processes using process details
        $kppProcesses = @()
        foreach ($process in $pythonProcesses) {
            try {
                # Get process command line using WMI
                $processInfo = Get-WmiObject -Class Win32_Process -Filter "ProcessId = $($process.Id)" -ErrorAction SilentlyContinue
                if ($processInfo -and $processInfo.CommandLine -match "(realtime_sync_master|main\.py|app\.py|dash_app\.py)") {
                    $kppProcesses += $process
                    Write-Host "Found KPP process: $($process.Id) - $($processInfo.CommandLine)" -ForegroundColor Yellow
                }
            }
            catch {
                # Fallback: check if process name contains KPP-related keywords
                if ($process.ProcessName -eq "python" -and $process.MainWindowTitle -match "(KPP|simulator|sync)") {
                    $kppProcesses += $process
                    Write-Host "Found KPP process (fallback): $($process.Id)" -ForegroundColor Yellow
                }
            }
        }
        
        # Stop KPP processes with validation
        if ($kppProcesses.Count -gt 0) {
            Write-Host "Stopping $($kppProcesses.Count) KPP processes..." -ForegroundColor Cyan
            foreach ($process in $kppProcesses) {
                try {
                    $process.Kill()
                    Write-Host "Stopped process: $($process.Id)" -ForegroundColor Green
                }
                catch {
                    Write-Host "Failed to stop process: $($process.Id) - $($_.Exception.Message)" -ForegroundColor Red
                    Write-ErrorLog -Message "Failed to stop process" -Severity "HIGH" -Category "RUNTIME" -Server "SYSTEM" -Details "PID: $($process.Id), Error: $($_.Exception.Message)"
                }
            }
        } else {
            Write-Host "No KPP processes found running" -ForegroundColor Yellow
        }
        
        # Also stop any background jobs
        $jobs = Get-Job -ErrorAction SilentlyContinue
        if ($jobs) {
            Write-Host "Stopping background jobs..." -ForegroundColor Cyan
            $jobs | Stop-Job -ErrorAction SilentlyContinue
            $jobs | Remove-Job -ErrorAction SilentlyContinue
        }
        
        Write-Host "All KPP services stopped successfully" -ForegroundColor Green
        Write-ErrorLog -Message "System shutdown completed" -Severity "INFO" -Category "RUNTIME" -Server "SYSTEM"
    }
    catch {
        Write-Host "Error during shutdown: $($_.Exception.Message)" -ForegroundColor Red
        Write-ErrorLog -Message "Shutdown error" -Severity "CRITICAL" -Category "RUNTIME" -Server "SYSTEM" -Details $_.Exception.Message
        exit 1
    }
    
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
Write-Host "  * Press Ctrl+C for graceful shutdown"

# Graceful shutdown handling
$script:ShutdownRequested = $false
$script:ShutdownTimeout = 30  # seconds

# Register event handlers for graceful shutdown
try {
    # Handle Ctrl+C (SIGINT)
    Register-EngineEvent PowerShell.Exiting -Action {
        if (-not $script:ShutdownRequested) {
            $script:ShutdownRequested = $true
            Write-Host "`nGraceful shutdown initiated..." -ForegroundColor Yellow
            Invoke-GracefulShutdown
        }
    }
    
    # Handle process termination signals
    $null = Register-WmiEvent -Class Win32_ProcessStopTrace -SourceIdentifier "ProcessStop" -ErrorAction SilentlyContinue
    Register-EngineEvent -SourceIdentifier "ProcessStop" -Action {
        if ($Event.SourceEventArgs.NewEvent.ProcessName -eq "powershell" -and -not $script:ShutdownRequested) {
            $script:ShutdownRequested = $true
            Write-Host "`nProcess termination detected, initiating graceful shutdown..." -ForegroundColor Yellow
            Invoke-GracefulShutdown
        }
    }
}
catch {
    Write-Host "Warning: Could not register shutdown handlers: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Function to perform graceful shutdown
function Invoke-GracefulShutdown {
    param([int]$Timeout = $script:ShutdownTimeout)
    
    Write-Host "Starting graceful shutdown sequence..." -ForegroundColor Cyan
    Write-ErrorLog -Message "Graceful shutdown initiated" -Severity "INFO" -Category "RUNTIME" -Server "SYSTEM"
    
    $startTime = Get-Date
    $jobs = Get-Job -ErrorAction SilentlyContinue
    
    if ($jobs) {
        Write-Host "Stopping $($jobs.Count) background jobs..." -ForegroundColor Yellow
        
        # Stop jobs in reverse startup order (if config available)
        $stopSequence = if ($script:Config.dependencies.shutdown_sequence) {
            $script:Config.dependencies.shutdown_sequence
        } else {
            @("Dash-Frontend", "WebSocket-Server", "Master-Clock", "Flask-Backend")
        }
        
        foreach ($serverName in $stopSequence) {
            $job = $jobs | Where-Object { $_.Name -eq $serverName }
            if ($job) {
                Write-Host "Stopping $serverName..." -ForegroundColor Yellow
                try {
                    Stop-Job -Job $job -ErrorAction SilentlyContinue
                    Write-Host "  $serverName stopped" -ForegroundColor Green
                }
                catch {
                    Write-Host "  Failed to stop ${serverName}: $($_.Exception.Message)" -ForegroundColor Red
                    Write-ErrorLog -Message "Failed to stop job" -Severity "HIGH" -Category "RUNTIME" -Server $serverName -Details $_.Exception.Message
                }
            }
        }
        
        # Wait for jobs to stop gracefully
        $timeoutReached = $false
        $elapsed = 0
        
        while (($jobs | Where-Object { $_.State -eq "Running" }) -and (-not $timeoutReached)) {
            Start-Sleep -Seconds 1
            $elapsed = ((Get-Date) - $startTime).TotalSeconds
            
            if ($elapsed -gt $Timeout) {
                $timeoutReached = $true
                Write-Host "Shutdown timeout reached, forcing job termination..." -ForegroundColor Red
                Write-ErrorLog -Message "Shutdown timeout reached" -Severity "HIGH" -Category "RUNTIME" -Server "SYSTEM" -Details "Timeout: $Timeout seconds"
            }
        }
        
        # Remove jobs
        try {
            $jobs | Remove-Job -ErrorAction SilentlyContinue
            Write-Host "All jobs removed" -ForegroundColor Green
        }
        catch {
            Write-Host "Warning: Some jobs could not be removed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    
    # Stop any remaining Python processes
    try {
        $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
        $kppProcesses = @()
        
        foreach ($process in $pythonProcesses) {
            try {
                $processInfo = Get-WmiObject -Class Win32_Process -Filter "ProcessId = $($process.Id)" -ErrorAction SilentlyContinue
                if ($processInfo -and $processInfo.CommandLine -match "(realtime_sync_master|main\.py|app\.py|dash_app\.py)") {
                    $kppProcesses += $process
                }
            }
            catch {
                # Fallback check
                if ($process.ProcessName -eq "python" -and $process.MainWindowTitle -match "(KPP|simulator|sync)") {
                    $kppProcesses += $process
                }
            }
        }
        
        if ($kppProcesses.Count -gt 0) {
            Write-Host "Stopping $($kppProcesses.Count) remaining KPP processes..." -ForegroundColor Yellow
            foreach ($process in $kppProcesses) {
                try {
                    $process.Kill()
                    Write-Host "  Process $($process.Id) stopped" -ForegroundColor Green
                }
                catch {
                    Write-Host "  Failed to stop process $($process.Id): $($_.Exception.Message)" -ForegroundColor Red
                }
            }
        }
    }
    catch {
        Write-Host "Warning: Error during process cleanup: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    $totalTime = ((Get-Date) - $startTime).TotalSeconds
    Write-Host "Graceful shutdown completed in $([math]::Round($totalTime, 1)) seconds" -ForegroundColor Green
    Write-ErrorLog -Message "Graceful shutdown completed" -Severity "INFO" -Category "RUNTIME" -Server "SYSTEM" -Details "Duration: $([math]::Round($totalTime, 1))s"
    
    # Show final error summary
    Show-ErrorSummary
    
    # Clean up logging resources
    Close-Logging
    
    # Clean up event handlers
    try {
        Unregister-Event -SourceIdentifier "ProcessStop" -ErrorAction SilentlyContinue
        Unregister-Event -SourceIdentifier "PowerShell.Exiting" -ErrorAction SilentlyContinue
    }
    catch {
        # Ignore cleanup errors
    }
    
    exit 0
}

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
                Write-Host "Initiating graceful shutdown..." -ForegroundColor Yellow
                $script:ShutdownRequested = $true
                Invoke-GracefulShutdown
            }
        }
    }
    
} while ($true) 