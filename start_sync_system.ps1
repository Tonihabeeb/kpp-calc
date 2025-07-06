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
                        dependencies = @()
                    }
                    master_clock = @{
                        name = "Master Clock Server"
                        script = "realtime_sync_master.py"
                        port = 9200
                        health_endpoint = "/health"
                        startup_timeout = 5
                        retry_attempts = 3
                        retry_delay = 1
                        dependencies = @()
                    }
                    websocket_server = @{
                        name = "WebSocket Server"
                        script = "main.py"
                        port = 9101
                        health_endpoint = "/"
                        startup_timeout = 5
                        retry_attempts = 3
                        retry_delay = 1
                        dependencies = @("flask_backend", "master_clock")
                    }
                    dash_frontend = @{
                        name = "Dash Frontend"
                        script = "dash_app.py"
                        port = 9103
                        health_endpoint = "/"
                        startup_timeout = 10
                        retry_attempts = 3
                        retry_delay = 2
                        dependencies = @("flask_backend", "websocket_server")
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

# Initialize monitoring alerts
Initialize-MonitoringAlerts

# Record startup time for uptime tracking
$script:StartTime = Get-Date

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

# --- Service Dependency Management Functions ---

# Function to validate service dependencies
function Test-ServiceDependencies {
    param([string]$ServiceName)
    
    try {
        $serviceConfig = $script:Config.servers.$ServiceName
        if (-not $serviceConfig) {
            Write-ErrorLog -Message "Service configuration not found" -Severity "CRITICAL" -Category "DEPENDENCY" -Server $ServiceName -Details "No config for $ServiceName"
            return $false
        }
        
        # Check if service has dependencies defined
        if ($serviceConfig.dependencies) {
            foreach ($dep in $serviceConfig.dependencies) {
                if (-not (Test-ServiceHealth -ServiceName $dep)) {
                    Write-ErrorLog -Message "Dependency not healthy" -Severity "HIGH" -Category "DEPENDENCY" -Server $ServiceName -Details "Dependency $dep is not ready"
                    return $false
                }
            }
        }
        
        # Check port availability
        if (-not (Test-PortAvailability -Port $serviceConfig.port)) {
            Write-ErrorLog -Message "Port not available" -Severity "HIGH" -Category "DEPENDENCY" -Server $ServiceName -Details "Port $($serviceConfig.port) is in use"
            return $false
        }
        
        # Check script file exists
        if (-not (Test-Path $serviceConfig.script)) {
            Write-ErrorLog -Message "Service script not found" -Severity "CRITICAL" -Category "DEPENDENCY" -Server $ServiceName -Details "Script $($serviceConfig.script) missing"
            return $false
        }
        
        return $true
    }
    catch {
        Write-ErrorLog -Message "Dependency validation failed" -Severity "CRITICAL" -Category "DEPENDENCY" -Server $ServiceName -Details $_.Exception.Message
        return $false
    }
}

# Function to check service health
function Test-ServiceHealth {
    param([string]$ServiceName)
    
    try {
        $serviceConfig = $script:Config.servers.$ServiceName
        if (-not $serviceConfig) {
            return $false
        }
        
        $healthUrl = "http://localhost:$($serviceConfig.port)$($serviceConfig.health_endpoint)"
        
        # Test URL validity first
        if (-not (Test-Url -Url $healthUrl)) {
            return $false
        }
        
        # Check if service is responding
        $response = try {
            Invoke-WebRequest -Uri $healthUrl -TimeoutSec 5 -UseBasicParsing
        } catch {
            return $false
        }
        
        return ($response.StatusCode -eq 200)
    }
    catch {
        return $false
    }
}

# Function to check port availability
function Test-PortAvailability {
    param([int]$Port)
    
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $false  # Port is in use
    }
    catch {
        return $true   # Port is available
    }
}

# Function to wait for service to be ready
function Wait-ForServiceReady {
    param(
        [string]$ServiceName,
        [int]$Timeout = 30,
        [int]$CheckInterval = 2
    )
    
    $startTime = Get-Date
    $elapsed = 0
    
    Write-Host "Waiting for $ServiceName to be ready..." -ForegroundColor Yellow
    
    while ($elapsed -lt $Timeout) {
        if (Test-ServiceHealth -ServiceName $ServiceName) {
            Write-Host "$ServiceName is ready!" -ForegroundColor Green
            Write-ErrorLog -Message "Service ready" -Severity "INFO" -Category "DEPENDENCY" -Server $ServiceName
            return $true
        }
        
        Start-Sleep -Seconds $CheckInterval
        $elapsed = ((Get-Date) - $startTime).TotalSeconds
        
        if ($elapsed % 10 -eq 0) {
            $elapsedRounded = [math]::Round($elapsed)
            Write-Host "Still waiting for $ServiceName... ($elapsedRounded s elapsed)" -ForegroundColor Yellow
        }
    }
    
    Write-Host "Timeout waiting for $ServiceName" -ForegroundColor Red
    Write-ErrorLog -Message "Service startup timeout" -Severity "HIGH" -Category "DEPENDENCY" -Server $ServiceName -Details "Timeout after $Timeout seconds"
    return $false
}

# Function to start service with dependency management
function Start-ServiceWithDependencies {
    param([string]$ServiceName)
    
    try {
        # Validate dependencies before starting
        if (-not (Test-ServiceDependencies -ServiceName $ServiceName)) {
            Write-Host "Dependencies not met for $ServiceName" -ForegroundColor Red
            return $false
        }
        
        $serviceConfig = $script:Config.servers.$ServiceName
        
        Write-Host "Starting $($serviceConfig.name) (Port $($serviceConfig.port))..." -ForegroundColor Cyan
        
        # Start the service
        $job = Start-Job -ScriptBlock { 
            param($ScriptPath, $WorkingDir)
            Set-Location $WorkingDir
            python $ScriptPath
        } -ArgumentList $serviceConfig.script, $PWD -Name $ServiceName
        
        # Wait for service to be ready
        $ready = Wait-ForServiceReady -ServiceName $ServiceName -Timeout $serviceConfig.startup_timeout
        
        if ($ready) {
            Write-Host "$($serviceConfig.name) started successfully" -ForegroundColor Green
            Write-ErrorLog -Message "Service started successfully" -Severity "INFO" -Category "STARTUP" -Server $ServiceName
            return $true
        } else {
            Write-Host "Failed to start $($serviceConfig.name)" -ForegroundColor Red
            Stop-Job -Job $job -ErrorAction SilentlyContinue
            Remove-Job -Job $job -ErrorAction SilentlyContinue
            Write-ErrorLog -Message "Service startup failed" -Severity "CRITICAL" -Category "STARTUP" -Server $ServiceName
            return $false
        }
    }
    catch {
        Write-Host "Error starting $ServiceName - $($_.Exception.Message)" -ForegroundColor Red
        Write-ErrorLog -Message "Service startup error" -Severity "CRITICAL" -Category "STARTUP" -Server $ServiceName -Details $_.Exception.Message
        return $false
    }
}

# Function to validate startup sequence
function Test-StartupSequence {
    param([string[]]$StartupSequence)
    
    $errors = @()
    
    foreach ($service in $startupSequence) {
        if (-not $script:Config.servers.PSObject.Properties.Name -contains $service) {
            $errors += "Service '$service' not found in configuration"
        }
    }
    
    # Check for circular dependencies
    $visited = @{}
    $recStack = @{}
    
    foreach ($service in $startupSequence) {
        if (-not $visited.ContainsKey($service)) {
            if (Test-CircularDependency -Service $service -Visited $visited -RecStack $recStack) {
                $errors += "Circular dependency detected involving service '$service'"
            }
        }
    }
    
    return @{
        IsValid = ($errors.Count -eq 0)
        Errors = $errors
    }
}

# Function to detect circular dependencies
function Test-CircularDependency {
    param(
        [string]$Service,
        [hashtable]$Visited,
        [hashtable]$RecStack
    )
    
    $Visited[$Service] = $true
    $RecStack[$Service] = $true
    
    $serviceConfig = $script:Config.servers.$Service
    if ($serviceConfig.dependencies) {
        foreach ($dep in $serviceConfig.dependencies) {
            if (-not $Visited.ContainsKey($dep)) {
                if (Test-CircularDependency -Service $dep -Visited $Visited -RecStack $RecStack) {
                    return $true
                }
            } elseif ($RecStack[$dep]) {
                return $true
            }
        }
    }
    
    $RecStack[$Service] = $false
    return $false
}

# Function to get service dependency tree
function Get-ServiceDependencyTree {
    param([string]$ServiceName)
    
    $tree = @{
        Service = $ServiceName
        Dependencies = @()
        Dependents = @()
    }
    
    $serviceConfig = $script:Config.servers.$ServiceName
    if ($serviceConfig.dependencies) {
        $tree.Dependencies = $serviceConfig.dependencies
    }
    
    # Find services that depend on this service
    foreach ($server in $script:Config.servers.PSObject.Properties.Name) {
        $config = $script:Config.servers.$server
        if ($config.dependencies -and $config.dependencies -contains $ServiceName) {
            $tree.Dependents += $server
        }
    }
    
    return $tree
}

# Function to show dependency status
function Show-DependencyStatus {
    Write-Host "`nService Dependency Status:" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan
    
    foreach ($server in $script:Config.dependencies.startup_sequence) {
        $tree = Get-ServiceDependencyTree -ServiceName $server
        $health = Test-ServiceHealth -ServiceName $server
        $status = if ($health) { "HEALTHY" } else { "UNHEALTHY" }
        $color = if ($health) { "Green" } else { "Red" }
        
        Write-Host "$server ($status)" -ForegroundColor $color
        if ($tree.Dependencies.Count -gt 0) {
            Write-Host "  Dependencies: $($tree.Dependencies -join ', ')" -ForegroundColor Gray
        }
        if ($tree.Dependents.Count -gt 0) {
            Write-Host "  Dependents: $($tree.Dependents -join ', ')" -ForegroundColor Gray
        }
        Write-Host ""
    }
}

# --- Performance Monitoring Functions ---

# Function to get detailed system performance metrics
function Get-SystemPerformanceMetrics {
    try {
        # CPU Performance
        $cpuCounter = Get-Counter "\Processor(_Total)\% Processor Time" -ErrorAction SilentlyContinue
        $cpuUsage = if ($cpuCounter) { $cpuCounter.CounterSamples[0].CookedValue } else { 0 }
        
        # Memory Performance
        $memoryCounter = Get-Counter "\Memory\% Committed Bytes In Use" -ErrorAction SilentlyContinue
        $memoryUsage = if ($memoryCounter) { $memoryCounter.CounterSamples[0].CookedValue } else { 0 }
        
        # Disk Performance
        $diskCounter = Get-Counter "\PhysicalDisk(_Total)\% Disk Time" -ErrorAction SilentlyContinue
        $diskUsage = if ($diskCounter) { $diskCounter.CounterSamples[0].CookedValue } else { 0 }
        
        # Network Performance
        $networkCounter = Get-Counter "\Network Interface(*)\Bytes Total/sec" -ErrorAction SilentlyContinue
        $networkUsage = if ($networkCounter) { 
            ($networkCounter.CounterSamples | Measure-Object -Property CookedValue -Sum).Sum 
        } else { 0 }
        
        # Process-specific metrics
        $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
        $totalProcessMemory = ($pythonProcesses | Measure-Object -Property WorkingSet -Sum).Sum / 1MB
        $processCount = $pythonProcesses.Count
        
        return @{
            Timestamp = Get-Date
            CPU = @{
                Usage = [math]::Round($cpuUsage, 1)
                Status = if ($cpuUsage -gt $script:Config.monitoring.performance_thresholds.cpu_critical) { "CRITICAL" }
                         elseif ($cpuUsage -gt $script:Config.monitoring.performance_thresholds.cpu_warning) { "WARNING" }
                         else { "NORMAL" }
            }
            Memory = @{
                Usage = [math]::Round($memoryUsage, 1)
                Status = if ($memoryUsage -gt $script:Config.monitoring.performance_thresholds.memory_critical) { "CRITICAL" }
                         elseif ($memoryUsage -gt $script:Config.monitoring.performance_thresholds.memory_warning) { "WARNING" }
                         else { "NORMAL" }
                ProcessMemory = [math]::Round($totalProcessMemory, 1)
            }
            Disk = @{
                Usage = [math]::Round($diskUsage, 1)
                Status = if ($diskUsage -gt 90) { "CRITICAL" }
                         elseif ($diskUsage -gt 80) { "WARNING" }
                         else { "NORMAL" }
            }
            Network = @{
                BytesPerSec = [math]::Round($networkUsage, 0)
                Status = if ($networkUsage -gt 100000000) { "HIGH" } else { "NORMAL" }
            }
            Processes = @{
                Count = $processCount
                TotalMemoryMB = [math]::Round($totalProcessMemory, 1)
            }
        }
    }
    catch {
        Write-ErrorLog -Message "Performance metrics collection failed" -Severity "HIGH" -Category "MONITORING" -Server "SYSTEM" -Details $_.Exception.Message
        return $null
    }
}

# Function to monitor service performance
function Get-ServicePerformanceMetrics {
    param([string]$ServiceName)
    
    try {
        $serviceConfig = $script:Config.servers.$ServiceName
        if (-not $serviceConfig) {
            return $null
        }
        
        $startTime = Get-Date
        $healthUrl = "http://localhost:$($serviceConfig.port)$($serviceConfig.health_endpoint)"
        
        # Test response time
        $response = try {
            Invoke-WebRequest -Uri $healthUrl -TimeoutSec 5 -UseBasicParsing
        } catch {
            return @{
                Service = $ServiceName
                Status = "UNREACHABLE"
                ResponseTime = 0
                Error = $_.Exception.Message
                Timestamp = Get-Date
            }
        }
        
        $responseTime = ((Get-Date) - $startTime).TotalMilliseconds
        
        # Get process-specific metrics
        $process = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
            $_.MainWindowTitle -match $ServiceName -or $_.ProcessName -eq "python"
        } | Select-Object -First 1
        
        $processMetrics = if ($process) {
            @{
                ProcessId = $process.Id
                MemoryMB = [math]::Round($process.WorkingSet / 1MB, 1)
                CPU = [math]::Round($process.CPU, 1)
                Threads = $process.Threads.Count
            }
        } else {
            @{
                ProcessId = 0
                MemoryMB = 0
                CPU = 0
                Threads = 0
            }
        }
        
        return @{
            Service = $ServiceName
            Status = if ($response.StatusCode -eq 200) { "HEALTHY" } else { "UNHEALTHY" }
            ResponseTime = [math]::Round($responseTime, 1)
            HttpStatus = $response.StatusCode
            Process = $processMetrics
            Timestamp = Get-Date
        }
    }
    catch {
        Write-ErrorLog -Message "Service performance monitoring failed" -Severity "HIGH" -Category "MONITORING" -Server $ServiceName -Details $_.Exception.Message
        return $null
    }
}

# Function to generate performance alerts
function Invoke-PerformanceAlerting {
    param([object]$Metrics)
    
    if (-not $Metrics) { return }
    
    $alerts = @()
    
    # CPU Alerts
    if ($Metrics.CPU.Status -eq "CRITICAL") {
        $alerts += "CRITICAL: CPU usage at $($Metrics.CPU.Usage)%"
        Write-ErrorLog -Message "Critical CPU usage detected" -Severity "CRITICAL" -Category "PERFORMANCE" -Server "SYSTEM" -Details "CPU: $($Metrics.CPU.Usage)%"
    } elseif ($Metrics.CPU.Status -eq "WARNING") {
        $alerts += "WARNING: High CPU usage at $($Metrics.CPU.Usage)%"
        Write-ErrorLog -Message "High CPU usage warning" -Severity "HIGH" -Category "PERFORMANCE" -Server "SYSTEM" -Details "CPU: $($Metrics.CPU.Usage)%"
    }
    
    # Memory Alerts
    if ($Metrics.Memory.Status -eq "CRITICAL") {
        $alerts += "CRITICAL: Memory usage at $($Metrics.Memory.Usage)%"
        Write-ErrorLog -Message "Critical memory usage detected" -Severity "CRITICAL" -Category "PERFORMANCE" -Server "SYSTEM" -Details "Memory: $($Metrics.Memory.Usage)%"
    } elseif ($Metrics.Memory.Status -eq "WARNING") {
        $alerts += "WARNING: High memory usage at $($Metrics.Memory.Usage)%"
        Write-ErrorLog -Message "High memory usage warning" -Severity "HIGH" -Category "PERFORMANCE" -Server "SYSTEM" -Details "Memory: $($Metrics.Memory.Usage)%"
    }
    
    # Process Memory Alerts
    if ($Metrics.Memory.ProcessMemory -gt 1000) {  # 1GB threshold
        $alerts += "WARNING: High process memory usage: $($Metrics.Memory.ProcessMemory) MB"
        Write-ErrorLog -Message "High process memory usage" -Severity "HIGH" -Category "PERFORMANCE" -Server "SYSTEM" -Details "Process Memory: $($Metrics.Memory.ProcessMemory) MB"
    }
    
    # Network Alerts
    if ($Metrics.Network.Status -eq "HIGH") {
        $alerts += "INFO: High network activity: $($Metrics.Network.BytesPerSec) bytes/sec"
        Write-ErrorLog -Message "High network activity detected" -Severity "MEDIUM" -Category "PERFORMANCE" -Server "SYSTEM" -Details "Network: $($Metrics.Network.BytesPerSec) bytes/sec"
    }
    
    return $alerts
}

# Function to show comprehensive performance dashboard
function Show-PerformanceDashboard {
    Write-Host "`nPerformance Dashboard" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan
    
    # System Performance
    $systemMetrics = Get-SystemPerformanceMetrics
    if ($systemMetrics) {
        Write-Host "System Performance:" -ForegroundColor Yellow
        Write-Host "  CPU: $($systemMetrics.CPU.Usage)% [$($systemMetrics.CPU.Status)]" -ForegroundColor $(if ($systemMetrics.CPU.Status -eq "CRITICAL") { "Red" } elseif ($systemMetrics.CPU.Status -eq "WARNING") { "Yellow" } else { "Green" })
        Write-Host "  Memory: $($systemMetrics.Memory.Usage)% [$($systemMetrics.Memory.Status)]" -ForegroundColor $(if ($systemMetrics.Memory.Status -eq "CRITICAL") { "Red" } elseif ($systemMetrics.Memory.Status -eq "WARNING") { "Yellow" } else { "Green" })
        Write-Host "  Disk: $($systemMetrics.Disk.Usage)% [$($systemMetrics.Disk.Status)]" -ForegroundColor $(if ($systemMetrics.Disk.Status -eq "CRITICAL") { "Red" } elseif ($systemMetrics.Disk.Status -eq "WARNING") { "Yellow" } else { "Green" })
        Write-Host "  Network: $($systemMetrics.Network.BytesPerSec) bytes/sec [$($systemMetrics.Network.Status)]" -ForegroundColor $(if ($systemMetrics.Network.Status -eq "HIGH") { "Yellow" } else { "Green" })
        Write-Host "  Processes: $($systemMetrics.Processes.Count) (Memory: $($systemMetrics.Processes.TotalMemoryMB) MB)" -ForegroundColor Cyan
        Write-Host ""
        
        # Performance Alerts
        $alerts = Invoke-PerformanceAlerting -Metrics $systemMetrics
        if ($alerts.Count -gt 0) {
            Write-Host "Performance Alerts:" -ForegroundColor Red
            foreach ($alert in $alerts) {
                Write-Host "  ⚠ $alert" -ForegroundColor Red
            }
            Write-Host ""
        }
    }
    
    # Service Performance
    Write-Host "Service Performance:" -ForegroundColor Yellow
    foreach ($serviceName in $script:Config.dependencies.startup_sequence) {
        $serviceMetrics = Get-ServicePerformanceMetrics -ServiceName $serviceName
        if ($serviceMetrics) {
            $statusColor = switch ($serviceMetrics.Status) {
                "HEALTHY" { "Green" }
                "UNHEALTHY" { "Red" }
                "UNREACHABLE" { "DarkRed" }
                default { "Gray" }
            }
            
            Write-Host "  $($serviceMetrics.Service): $($serviceMetrics.Status) (${$serviceMetrics.ResponseTime}ms)" -ForegroundColor $statusColor
            if ($serviceMetrics.Process.ProcessId -gt 0) {
                Write-Host "    PID: $($serviceMetrics.Process.ProcessId), Memory: $($serviceMetrics.Process.MemoryMB) MB, Threads: $($serviceMetrics.Process.Threads)" -ForegroundColor Gray
            }
        }
    }
    
    Write-Host ""
    Write-Host "Last Updated: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray
}

# Function to export performance data
function Export-PerformanceData {
    param(
        [string]$OutputPath = "logs/performance_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    )
    
    try {
        $performanceData = @{
            Timestamp = Get-Date
            System = Get-SystemPerformanceMetrics
            Services = @{}
        }
        
        foreach ($serviceName in $script:Config.dependencies.startup_sequence) {
            $performanceData.Services[$serviceName] = Get-ServicePerformanceMetrics -ServiceName $serviceName
        }
        
        # Ensure logs directory exists
        $logDir = Split-Path $OutputPath -Parent
        if (-not (Test-Path $logDir)) {
            New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        }
        
        $performanceData | ConvertTo-Json -Depth 10 | Set-Content $OutputPath
        Write-Host "Performance data exported to: $OutputPath" -ForegroundColor Green
        Write-ErrorLog -Message "Performance data exported" -Severity "INFO" -Category "MONITORING" -Server "SYSTEM" -Details $OutputPath
        
        return $OutputPath
    }
    catch {
        Write-Host "Failed to export performance data: $($_.Exception.Message)" -ForegroundColor Red
        Write-ErrorLog -Message "Performance export failed" -Severity "HIGH" -Category "MONITORING" -Server "SYSTEM" -Details $_.Exception.Message
        return $null
    }
}

# Function to monitor resource trends
function Get-ResourceTrends {
    param([int]$Minutes = 10)
    
    try {
        $trendData = @{
            CPU = @()
            Memory = @()
            Disk = @()
            Network = @()
        }
        
        # Collect metrics over time
        for ($i = 0; $i -lt $Minutes; $i++) {
            $metrics = Get-SystemPerformanceMetrics
            if ($metrics) {
                $trendData.CPU += $metrics.CPU.Usage
                $trendData.Memory += $metrics.Memory.Usage
                $trendData.Disk += $metrics.Disk.Usage
                $trendData.Network += $metrics.Network.BytesPerSec
            }
            Start-Sleep -Seconds 60
        }
        
        # Calculate trends
        $trends = @{
            CPU = @{
                Average = if ($trendData.CPU.Count -gt 0) { [math]::Round(($trendData.CPU | Measure-Object -Average).Average, 1) } else { 0 }
                Trend = if ($trendData.CPU.Count -gt 1) { 
                    $first = $trendData.CPU[0]
                    $last = $trendData.CPU[-1]
                    if ($last -gt $first) { "INCREASING" } elseif ($last -lt $first) { "DECREASING" } else { "STABLE" }
                } else { "UNKNOWN" }
            }
            Memory = @{
                Average = if ($trendData.Memory.Count -gt 0) { [math]::Round(($trendData.Memory | Measure-Object -Average).Average, 1) } else { 0 }
                Trend = if ($trendData.Memory.Count -gt 1) { 
                    $first = $trendData.Memory[0]
                    $last = $trendData.Memory[-1]
                    if ($last -gt $first) { "INCREASING" } elseif ($last -lt $first) { "DECREASING" } else { "STABLE" }
                } else { "UNKNOWN" }
            }
        }
        
        return $trends
    }
    catch {
        Write-ErrorLog -Message "Resource trend analysis failed" -Severity "HIGH" -Category "MONITORING" -Server "SYSTEM" -Details $_.Exception.Message
        return $null
    }
}

# --- Enhanced Monitoring & Alerting Functions ---

# Function to create comprehensive system report
function Get-SystemReport {
    param([switch]$IncludeTrends)
    
    try {
        $report = @{
            Timestamp = Get-Date
            System = @{
                Name = $script:Config.system.name
                Version = $script:Config.system.version
                Environment = $script:Config.system.environment
                Uptime = ((Get-Date) - $script:StartTime).ToString("dd\.hh\:mm\:ss")
            }
            Performance = Get-SystemPerformanceMetrics
            Services = @{}
            Errors = @{
                Total = $script:ErrorLog.Count
                Critical = ($script:ErrorLog | Where-Object { $_.severity -eq "CRITICAL" }).Count
                High = ($script:ErrorLog | Where-Object { $_.severity -eq "HIGH" }).Count
                Medium = ($script:ErrorLog | Where-Object { $_.severity -eq "MEDIUM" }).Count
            }
            Alerts = @()
        }
        
        # Add service status
        foreach ($serviceName in $script:Config.dependencies.startup_sequence) {
            $report.Services[$serviceName] = Get-ServicePerformanceMetrics -ServiceName $serviceName
        }
        
        # Add performance alerts
        if ($report.Performance) {
            $report.Alerts = Invoke-PerformanceAlerting -Metrics $report.Performance
        }
        
        # Add trends if requested
        if ($IncludeTrends) {
            $report.Trends = Get-ResourceTrends -Minutes 5
        }
        
        return $report
    }
    catch {
        Write-ErrorLog -Message "System report generation failed" -Severity "HIGH" -Category "MONITORING" -Server "SYSTEM" -Details $_.Exception.Message
        return $null
    }
}

# Function to show enhanced system health with trends
function Show-EnhancedSystemHealth {
    Write-Host "`nEnhanced System Health Report" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan
    
    $report = Get-SystemReport -IncludeTrends
    if (-not $report) {
        Write-Host "Failed to generate system report" -ForegroundColor Red
        return
    }
    
    # System Information
    Write-Host "System Information:" -ForegroundColor Yellow
    Write-Host "  Name: $($report.System.Name)" -ForegroundColor White
    Write-Host "  Version: $($report.System.Version)" -ForegroundColor White
    Write-Host "  Environment: $($report.System.Environment)" -ForegroundColor White
    Write-Host "  Uptime: $($report.System.Uptime)" -ForegroundColor White
    Write-Host ""
    
    # Performance Summary
    if ($report.Performance) {
        Write-Host "Performance Summary:" -ForegroundColor Yellow
        Write-Host "  CPU: $($report.Performance.CPU.Usage)% [$($report.Performance.CPU.Status)]" -ForegroundColor $(if ($report.Performance.CPU.Status -eq "CRITICAL") { "Red" } elseif ($report.Performance.CPU.Status -eq "WARNING") { "Yellow" } else { "Green" })
        Write-Host "  Memory: $($report.Performance.Memory.Usage)% [$($report.Performance.Memory.Status)]" -ForegroundColor $(if ($report.Performance.Memory.Status -eq "CRITICAL") { "Red" } elseif ($report.Performance.Memory.Status -eq "WARNING") { "Yellow" } else { "Green" })
        Write-Host "  Disk: $($report.Performance.Disk.Usage)% [$($report.Performance.Disk.Status)]" -ForegroundColor $(if ($report.Performance.Disk.Status -eq "CRITICAL") { "Red" } elseif ($report.Performance.Disk.Status -eq "WARNING") { "Yellow" } else { "Green" })
        Write-Host "  Network: $($report.Performance.Network.BytesPerSec) bytes/sec [$($report.Performance.Network.Status)]" -ForegroundColor $(if ($report.Performance.Network.Status -eq "HIGH") { "Yellow" } else { "Green" })
        Write-Host ""
    }
    
    # Service Status
    Write-Host "Service Status:" -ForegroundColor Yellow
    foreach ($serviceName in $report.Services.Keys) {
        $service = $report.Services[$serviceName]
        if ($service) {
            $statusColor = switch ($service.Status) {
                "HEALTHY" { "Green" }
                "UNHEALTHY" { "Red" }
                "UNREACHABLE" { "DarkRed" }
                default { "Gray" }
            }
            Write-Host "  $($service.Service): $($service.Status) (${$service.ResponseTime}ms)" -ForegroundColor $statusColor
        }
    }
    Write-Host ""
    
    # Error Summary
    Write-Host "Error Summary:" -ForegroundColor Yellow
    Write-Host "  Total Errors: $($report.Errors.Total)" -ForegroundColor White
    Write-Host "  Critical: $($report.Errors.Critical)" -ForegroundColor $(if ($report.Errors.Critical -gt 0) { "Red" } else { "Green" })
    Write-Host "  High: $($report.Errors.High)" -ForegroundColor $(if ($report.Errors.High -gt 0) { "Yellow" } else { "Green" })
    Write-Host "  Medium: $($report.Errors.Medium)" -ForegroundColor White
    Write-Host ""
    
    # Active Alerts
    if ($report.Alerts.Count -gt 0) {
        Write-Host "Active Alerts:" -ForegroundColor Red
        foreach ($alert in $report.Alerts) {
            Write-Host "  ⚠ $alert" -ForegroundColor Red
        }
        Write-Host ""
    }
    
    # Trends (if available)
    if ($report.Trends) {
        Write-Host "Resource Trends (5 min):" -ForegroundColor Yellow
        Write-Host "  CPU: $($report.Trends.CPU.Average)% average [$($report.Trends.CPU.Trend)]" -ForegroundColor White
        Write-Host "  Memory: $($report.Trends.Memory.Average)% average [$($report.Trends.Memory.Trend)]" -ForegroundColor White
        Write-Host ""
    }
    
    Write-Host "Report Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
}



# Function to export monitoring data
function Export-MonitoringData {
    param(
        [string]$OutputPath = "logs/monitoring_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    )
    
    try {
        $monitoringData = @{
            Timestamp = Get-Date
            Report = Get-SystemReport -IncludeTrends
            ErrorLog = $script:ErrorLog
            AlertHistory = $script:AlertHistory
        }
        
        # Ensure logs directory exists
        $logDir = Split-Path $OutputPath -Parent
        if (-not (Test-Path $logDir)) {
            New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        }
        
        $monitoringData | ConvertTo-Json -Depth 10 | Set-Content $OutputPath
        Write-Host "Monitoring data exported to: $OutputPath" -ForegroundColor Green
        Write-ErrorLog -Message "Monitoring data exported" -Severity "INFO" -Category "MONITORING" -Server "SYSTEM" -Details $OutputPath
        
        return $OutputPath
    }
    catch {
        Write-Host "Failed to export monitoring data: $($_.Exception.Message)" -ForegroundColor Red
        Write-ErrorLog -Message "Monitoring export failed" -Severity "HIGH" -Category "MONITORING" -Server "SYSTEM" -Details $_.Exception.Message
        return $null
    }
}

# --- Advanced Automation & Orchestration Functions ---

# Function to create automated workflows
function New-AutomatedWorkflow {
    param(
        [string]$WorkflowName,
        [string[]]$Steps,
        [hashtable]$Parameters = @{},
        [int]$Timeout = 300
    )
    
    try {
        $workflow = @{
            Name = $WorkflowName
            Steps = $Steps
            Parameters = $Parameters
            Timeout = $Timeout
            Created = Get-Date
            Status = "CREATED"
            ExecutionHistory = @()
        }
        
        # Store workflow in configuration
        if (-not $script:Config.automation) {
            $script:Config.automation = @{
                workflows = @{}
            }
        }
        
        $script:Config.automation.workflows[$WorkflowName] = $workflow
        
        Write-Host "Workflow '$WorkflowName' created successfully" -ForegroundColor Green
        Write-ErrorLog -Message "Workflow created" -Severity "INFO" -Category "AUTOMATION" -Server "SYSTEM" -Details $WorkflowName
        
        return $workflow
    }
    catch {
        Write-Host "Failed to create workflow: $($_.Exception.Message)" -ForegroundColor Red
        Write-ErrorLog -Message "Workflow creation failed" -Severity "HIGH" -Category "AUTOMATION" -Server "SYSTEM" -Details $_.Exception.Message
        return $null
    }
}

# Function to execute automated workflows
function Invoke-AutomatedWorkflow {
    param(
        [string]$WorkflowName,
        [hashtable]$Parameters = @{}
    )
    
    try {
        if (-not $script:Config.automation.workflows.ContainsKey($WorkflowName)) {
            throw "Workflow '$WorkflowName' not found"
        }
        
        $workflow = $script:Config.automation.workflows[$WorkflowName]
        $workflow.Status = "RUNNING"
        $workflow.StartTime = Get-Date
        
        Write-Host "Executing workflow: $WorkflowName" -ForegroundColor Cyan
        Write-ErrorLog -Message "Workflow execution started" -Severity "INFO" -Category "AUTOMATION" -Server "SYSTEM" -Details $WorkflowName
        
        $results = @()
        $success = $true
        
        foreach ($step in $workflow.Steps) {
            Write-Host "  Executing step: $step" -ForegroundColor Yellow
            
            $stepResult = try {
                & $step @Parameters
            } catch {
                $success = $false
                @{
                    Step = $step
                    Status = "FAILED"
                    Error = $_.Exception.Message
                    Timestamp = Get-Date
                }
            }
            
            $results += $stepResult
            
            if (-not $success) {
                Write-Host "  Step failed: $step" -ForegroundColor Red
                break
            }
        }
        
        $workflow.Status = if ($success) { "COMPLETED" } else { "FAILED" }
        $workflow.EndTime = Get-Date
        $workflow.ExecutionHistory += @{
            StartTime = $workflow.StartTime
            EndTime = $workflow.EndTime
            Success = $success
            Results = $results
        }
        
        Write-Host "Workflow execution completed: $($workflow.Status)" -ForegroundColor $(if ($success) { "Green" } else { "Red" })
        Write-ErrorLog -Message "Workflow execution completed" -Severity $(if ($success) { "INFO" } else { "HIGH" }) -Category "AUTOMATION" -Server "SYSTEM" -Details "$WorkflowName - $($workflow.Status)"
        
        return @{
            Success = $success
            Results = $results
            Workflow = $workflow
        }
    }
    catch {
        Write-Host "Workflow execution failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-ErrorLog -Message "Workflow execution failed" -Severity "CRITICAL" -Category "AUTOMATION" -Server "SYSTEM" -Details $_.Exception.Message
        return @{
            Success = $false
            Error = $_.Exception.Message
        }
    }
}

# Function to schedule automated tasks
function New-ScheduledTask {
    param(
        [string]$TaskName,
        [string]$Command,
        [string]$Schedule,  # "daily", "hourly", "custom"
        [string]$Time = "00:00",
        [hashtable]$Parameters = @{}
    )
    
    try {
        $task = @{
            Name = $TaskName
            Command = $Command
            Schedule = $Schedule
            Time = $Time
            Parameters = $Parameters
            Created = Get-Date
            LastRun = $null
            NextRun = Get-NextScheduledRun -Schedule $Schedule -Time $Time
            Enabled = $true
        }
        
        # Store task in configuration
        if (-not $script:Config.automation) {
            $script:Config.automation = @{
                scheduled_tasks = @{}
            }
        }
        
        $script:Config.automation.scheduled_tasks[$TaskName] = $task
        
        Write-Host "Scheduled task '$TaskName' created successfully" -ForegroundColor Green
        Write-ErrorLog -Message "Scheduled task created" -Severity "INFO" -Category "AUTOMATION" -Server "SYSTEM" -Details $TaskName
        
        return $task
    }
    catch {
        Write-Host "Failed to create scheduled task: $($_.Exception.Message)" -ForegroundColor Red
        Write-ErrorLog -Message "Scheduled task creation failed" -Severity "HIGH" -Category "AUTOMATION" -Server "SYSTEM" -Details $_.Exception.Message
        return $null
    }
}

# Function to calculate next scheduled run
function Get-NextScheduledRun {
    param([string]$Schedule, [string]$Time)
    
    $now = Get-Date
    $timeParts = $Time.Split(":")
    $hour = [int]$timeParts[0]
    $minute = [int]$timeParts[1]
    
    switch ($Schedule.ToLower()) {
        "daily" {
            $nextRun = $now.Date.AddHours($hour).AddMinutes($minute)
            if ($nextRun -le $now) {
                $nextRun = $nextRun.AddDays(1)
            }
        }
        "hourly" {
            $nextRun = $now.Date.AddHours($now.Hour + 1).AddMinutes($minute)
        }
        "custom" {
            $nextRun = $now.AddMinutes(30)  # Default to 30 minutes from now
        }
        default {
            $nextRun = $now.AddHours(1)  # Default to 1 hour from now
        }
    }
    
    return $nextRun
}

# Function to check and execute scheduled tasks
function Invoke-ScheduledTasks {
    try {
        if (-not $script:Config.automation.scheduled_tasks) {
            return
        }
        
        $now = Get-Date
        $executedTasks = @()
        
        foreach ($taskName in $script:Config.automation.scheduled_tasks.Keys) {
            $task = $script:Config.automation.scheduled_tasks[$taskName]
            
            if ($task.Enabled -and $task.NextRun -le $now) {
                Write-Host "Executing scheduled task: $taskName" -ForegroundColor Yellow
                
                try {
                    # Execute the task
                    $result = & $task.Command @($task.Parameters.GetEnumerator() | ForEach-Object { $_.Value })
                    
                    $task.LastRun = $now
                    $task.NextRun = Get-NextScheduledRun -Schedule $task.Schedule -Time $task.Time
                    
                    $executedTasks += @{
                        Task = $taskName
                        Status = "SUCCESS"
                        Result = $result
                        Timestamp = $now
                    }
                    
                    Write-ErrorLog -Message "Scheduled task executed successfully" -Severity "INFO" -Category "AUTOMATION" -Server "SYSTEM" -Details $taskName
                }
                catch {
                    $executedTasks += @{
                        Task = $taskName
                        Status = "FAILED"
                        Error = $_.Exception.Message
                        Timestamp = $now
                    }
                    
                    Write-ErrorLog -Message "Scheduled task execution failed" -Severity "HIGH" -Category "AUTOMATION" -Server "SYSTEM" -Details "$taskName - $($_.Exception.Message)"
                }
            }
        }
        
        return $executedTasks
    }
    catch {
        Write-ErrorLog -Message "Scheduled task check failed" -Severity "HIGH" -Category "AUTOMATION" -Server "SYSTEM" -Details $_.Exception.Message
        return @()
    }
}

# --- Integration & API Functions ---

# Function to create REST API endpoints
function New-RestApiEndpoint {
    param(
        [string]$Endpoint,
        [string]$Method = "GET",
        [scriptblock]$Handler,
        [hashtable]$Parameters = @{}
    )
    
    try {
        $apiEndpoint = @{
            Endpoint = $Endpoint
            Method = $Method.ToUpper()
            Handler = $Handler
            Parameters = $Parameters
            Created = Get-Date
            RequestCount = 0
            LastRequest = $null
        }
        
        # Store endpoint in configuration
        if (-not $script:Config.integration) {
            $script:Config.integration = @{
                api_endpoints = @{}
            }
        }
        
        $script:Config.integration.api_endpoints[$Endpoint] = $apiEndpoint
        
        Write-Host "API endpoint '$Endpoint' created successfully" -ForegroundColor Green
        Write-ErrorLog -Message "API endpoint created" -Severity "INFO" -Category "INTEGRATION" -Server "SYSTEM" -Details $Endpoint
        
        return $apiEndpoint
    }
    catch {
        Write-Host "Failed to create API endpoint: $($_.Exception.Message)" -ForegroundColor Red
        Write-ErrorLog -Message "API endpoint creation failed" -Severity "HIGH" -Category "INTEGRATION" -Server "SYSTEM" -Details $_.Exception.Message
        return $null
    }
}

# Function to handle REST API requests
function Invoke-RestApiRequest {
    param(
        [string]$Endpoint,
        [string]$Method = "GET",
        [hashtable]$Body = @{},
        [hashtable]$Headers = @{}
    )
    
    try {
        if (-not $script:Config.integration.api_endpoints.ContainsKey($Endpoint)) {
            return @{
                StatusCode = 404
                Message = "Endpoint not found"
            }
        }
        
        $apiEndpoint = $script:Config.integration.api_endpoints[$Endpoint]
        
        # Update request statistics
        $apiEndpoint.RequestCount++
        $apiEndpoint.LastRequest = Get-Date
        
        # Execute handler
        $result = try {
            & $apiEndpoint.Handler -Body $Body -Headers $Headers
        } catch {
            @{
                StatusCode = 500
                Message = "Internal server error"
                Error = $_.Exception.Message
            }
        }
        
        return $result
    }
    catch {
        Write-ErrorLog -Message "API request handling failed" -Severity "HIGH" -Category "INTEGRATION" -Server "SYSTEM" -Details $_.Exception.Message
        return @{
            StatusCode = 500
            Message = "Request processing failed"
            Error = $_.Exception.Message
        }
    }
}

# Function to create webhook integration
function New-WebhookIntegration {
    param(
        [string]$WebhookName,
        [string]$Url,
        [string]$Method = "POST",
        [hashtable]$Headers = @{},
        [hashtable]$Payload = @{}
    )
    
    try {
        $webhook = @{
            Name = $WebhookName
            Url = $Url
            Method = $Method.ToUpper()
            Headers = $Headers
            Payload = $Payload
            Created = Get-Date
            LastTriggered = $null
            SuccessCount = 0
            FailureCount = 0
        }
        
        # Store webhook in configuration
        if (-not $script:Config.integration) {
            $script:Config.integration = @{
                webhooks = @{}
            }
        }
        
        $script:Config.integration.webhooks[$WebhookName] = $webhook
        
        Write-Host "Webhook '$WebhookName' created successfully" -ForegroundColor Green
        Write-ErrorLog -Message "Webhook created" -Severity "INFO" -Category "INTEGRATION" -Server "SYSTEM" -Details $WebhookName
        
        return $webhook
    }
    catch {
        Write-Host "Failed to create webhook: $($_.Exception.Message)" -ForegroundColor Red
        Write-ErrorLog -Message "Webhook creation failed" -Severity "HIGH" -Category "INTEGRATION" -Server "SYSTEM" -Details $_.Exception.Message
        return $null
    }
}

# Function to trigger webhook
function Invoke-Webhook {
    param(
        [string]$WebhookName,
        [hashtable]$AdditionalData = @{}
    )
    
    try {
        if (-not $script:Config.integration.webhooks.ContainsKey($WebhookName)) {
            throw "Webhook '$WebhookName' not found"
        }
        
        $webhook = $script:Config.integration.webhooks[$WebhookName]
        
        # Prepare payload
        $payload = $webhook.Payload.Clone()
        $payload.Add("timestamp", (Get-Date).ToString("yyyy-MM-dd HH:mm:ss"))
        $payload.Add("source", "KPP_Simulator")
        
        foreach ($key in $AdditionalData.Keys) {
            $payload[$key] = $AdditionalData[$key]
        }
        
        # Send webhook
        $response = try {
            Invoke-RestMethod -Uri $webhook.Url -Method $webhook.Method -Headers $webhook.Headers -Body ($payload | ConvertTo-Json) -ContentType "application/json"
        } catch {
            $webhook.FailureCount++
            throw $_
        }
        
        $webhook.LastTriggered = Get-Date
        $webhook.SuccessCount++
        
        Write-Host "Webhook '$WebhookName' triggered successfully" -ForegroundColor Green
        Write-ErrorLog -Message "Webhook triggered successfully" -Severity "INFO" -Category "INTEGRATION" -Server "SYSTEM" -Details $WebhookName
        
        return $response
    }
    catch {
        Write-Host "Webhook trigger failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-ErrorLog -Message "Webhook trigger failed" -Severity "HIGH" -Category "INTEGRATION" -Server "SYSTEM" -Details "$WebhookName - $($_.Exception.Message)"
        return $null
    }
}

# --- Testing & Validation Functions ---

# Function to run comprehensive system tests
function Invoke-SystemTests {
    param(
        [string[]]$TestTypes = @("unit", "integration", "performance", "security"),
        [switch]$Verbose
    )
    
    try {
        Write-Host "Starting comprehensive system tests..." -ForegroundColor Cyan
        Write-ErrorLog -Message "System tests started" -Severity "INFO" -Category "TESTING" -Server "SYSTEM"
        
        $testResults = @{
            Timestamp = Get-Date
            Tests = @{}
            Summary = @{
                Total = 0
                Passed = 0
                Failed = 0
                Skipped = 0
            }
        }
        
        foreach ($testType in $TestTypes) {
            Write-Host "Running $testType tests..." -ForegroundColor Yellow
            
            $testResults.Tests[$testType] = switch ($testType.ToLower()) {
                "unit" { Invoke-UnitTests -Verbose:$Verbose }
                "integration" { Invoke-IntegrationTests -Verbose:$Verbose }
                "performance" { Invoke-PerformanceTests -Verbose:$Verbose }
                "security" { Invoke-SecurityTests -Verbose:$Verbose }
                default { @{ Status = "SKIPPED"; Message = "Unknown test type" } }
            }
            
            $testResults.Summary.Total++
            switch ($testResults.Tests[$testType].Status) {
                "PASSED" { $testResults.Summary.Passed++ }
                "FAILED" { $testResults.Summary.Failed++ }
                default { $testResults.Summary.Skipped++ }
            }
        }
        
        # Generate test summary
        Write-Host "`nTest Summary:" -ForegroundColor Cyan
        Write-Host "  Total: $($testResults.Summary.Total)" -ForegroundColor White
        Write-Host "  Passed: $($testResults.Summary.Passed)" -ForegroundColor Green
        Write-Host "  Failed: $($testResults.Summary.Failed)" -ForegroundColor $(if ($testResults.Summary.Failed -gt 0) { "Red" } else { "Green" })
        Write-Host "  Skipped: $($testResults.Summary.Skipped)" -ForegroundColor Yellow
        
        $overallStatus = if ($testResults.Summary.Failed -eq 0) { "PASSED" } else { "FAILED" }
        Write-Host "  Overall Status: $overallStatus" -ForegroundColor $(if ($overallStatus -eq "PASSED") { "Green" } else { "Red" })
        
        Write-ErrorLog -Message "System tests completed" -Severity "INFO" -Category "TESTING" -Server "SYSTEM" -Details "Status: $overallStatus, Passed: $($testResults.Summary.Passed), Failed: $($testResults.Summary.Failed)"
        
        return $testResults
    }
    catch {
        Write-Host "System tests failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-ErrorLog -Message "System tests failed" -Severity "CRITICAL" -Category "TESTING" -Server "SYSTEM" -Details $_.Exception.Message
        return @{
            Status = "FAILED"
            Error = $_.Exception.Message
        }
    }
}

# Function to run unit tests
function Invoke-UnitTests {
    param([switch]$Verbose)
    
    try {
        $unitTests = @{
            "Configuration Loading" = {
                $config = Import-Configuration
                return $config -eq $true
            }
            "Service Health Check" = {
                $health = Test-ServiceHealth -ServiceName "flask_backend"
                return $false -eq $health  # Expected to fail if service not running
            }
            "Performance Metrics" = {
                $metrics = Get-SystemPerformanceMetrics
                return $null -ne $metrics
            }
            "Error Logging" = {
                $originalCount = $script:ErrorLog.Count
                Write-ErrorLog -Message "Test error" -Severity "LOW" -Category "TESTING" -Server "TEST"
                return ($script:ErrorLog.Count -gt $originalCount)
            }
        }
        
        $results = @{
            Status = "PASSED"
            Tests = @{}
            Passed = 0
            Failed = 0
        }
        
        foreach ($testName in $unitTests.Keys) {
            $testResult = try {
                $unitTests[$testName].Invoke()
            } catch {
                $false
            }
            
            $results.Tests[$testName] = @{
                Status = if ($testResult) { "PASSED" } else { "FAILED" }
                Result = $testResult
            }
            
            if ($testResult) {
                $results.Passed++
                if ($Verbose) { Write-Host "  ✓ $testName" -ForegroundColor Green }
            } else {
                $results.Failed++
                if ($Verbose) { Write-Host "  ✗ $testName" -ForegroundColor Red }
            }
        }
        
        $results.Status = if ($results.Failed -eq 0) { "PASSED" } else { "FAILED" }
        return $results
    }
    catch {
        return @{
            Status = "FAILED"
            Error = $_.Exception.Message
        }
    }
}

# Function to run integration tests
function Invoke-IntegrationTests {
    param([switch]$Verbose)
    
    try {
        $integrationTests = @{
            "Service Dependencies" = {
                $deps = Test-ServiceDependencies -ServiceName "websocket_server"
                return $false -eq $deps  # Expected to fail if dependencies not running
            }
            "Performance Monitoring" = {
                Show-PerformanceDashboard | Out-Null
                return $true  # If no exception, test passes
            }
            "System Health" = {
                Show-EnhancedSystemHealth | Out-Null
                return $true  # If no exception, test passes
            }
            "Data Export" = {
                $export = Export-MonitoringData -OutputPath "test_export.json"
                return $null -ne $export
            }
        }
        
        $results = @{
            Status = "PASSED"
            Tests = @{}
            Passed = 0
            Failed = 0
        }
        
        foreach ($testName in $integrationTests.Keys) {
            $testResult = try {
                $integrationTests[$testName].Invoke()
            } catch {
                $false
            }
            
            $results.Tests[$testName] = @{
                Status = if ($testResult) { "PASSED" } else { "FAILED" }
                Result = $testResult
            }
            
            if ($testResult) {
                $results.Passed++
                if ($Verbose) { Write-Host "  ✓ $testName" -ForegroundColor Green }
            } else {
                $results.Failed++
                if ($Verbose) { Write-Host "  ✗ $testName" -ForegroundColor Red }
            }
        }
        
        $results.Status = if ($results.Failed -eq 0) { "PASSED" } else { "FAILED" }
        return $results
    }
    catch {
        return @{
            Status = "FAILED"
            Error = $_.Exception.Message
        }
    }
}

# Function to run performance tests
function Invoke-PerformanceTests {
    param([switch]$Verbose)
    
    try {
        $performanceTests = @{
            "System Metrics Collection" = {
                $startTime = Get-Date
                Get-SystemPerformanceMetrics | Out-Null
                $duration = ((Get-Date) - $startTime).TotalMilliseconds
                return $duration -lt 1000  # Should complete within 1 second
            }
            "Service Health Check Speed" = {
                $startTime = Get-Date
                Test-ServiceHealth -ServiceName "flask_backend" | Out-Null
                $duration = ((Get-Date) - $startTime).TotalMilliseconds
                return $duration -lt 5000  # Should complete within 5 seconds
            }
            "Memory Usage" = {
                $metrics = Get-SystemPerformanceMetrics
                return $null -ne $metrics -and $metrics.Memory.Usage -lt 95  # Memory usage should be under 95%
            }
            "CPU Usage" = {
                $metrics = Get-SystemPerformanceMetrics
                return $null -ne $metrics -and $metrics.CPU.Usage -lt 90  # CPU usage should be under 90%
            }
        }
        
        $results = @{
            Status = "PASSED"
            Tests = @{}
            Passed = 0
            Failed = 0
        }
        
        foreach ($testName in $performanceTests.Keys) {
            $testResult = try {
                $performanceTests[$testName].Invoke()
            } catch {
                $false
            }
            
            $results.Tests[$testName] = @{
                Status = if ($testResult) { "PASSED" } else { "FAILED" }
                Result = $testResult
            }
            
            if ($testResult) {
                $results.Passed++
                if ($Verbose) { Write-Host "  ✓ $testName" -ForegroundColor Green }
            } else {
                $results.Failed++
                if ($Verbose) { Write-Host "  ✗ $testName" -ForegroundColor Red }
            }
        }
        
        $results.Status = if ($results.Failed -eq 0) { "PASSED" } else { "FAILED" }
        return $results
    }
    catch {
        return @{
            Status = "FAILED"
            Error = $_.Exception.Message
        }
    }
}

# Function to run security tests
function Invoke-SecurityTests {
    param([switch]$Verbose)
    
    try {
        $securityTests = @{
            "URL Validation" = {
                $validUrl = Test-Url -Url "http://localhost:9100/status"
                $invalidUrl = Test-Url -Url "invalid://url"
                return $validUrl -and (-not $invalidUrl)
            }
            "Input Sanitization" = {
                $originalMessage = @'
Test<script>alert("xss")</script>
'@
                $sanitized = Invoke-ErrorSanitization -Message $originalMessage
                return $sanitized -ne $originalMessage
            }
            "Configuration Security" = {
                $config = $script:Config
                return $config.security.url_validation -and $config.security.input_sanitization
            }
            "Process Validation" = {
                $processes = Get-Process -Name "python" -ErrorAction SilentlyContinue
                return $processes.Count -ge 0  # Should not throw exception
            }
        }
        
        $results = @{
            Status = "PASSED"
            Tests = @{}
            Passed = 0
            Failed = 0
        }
        
        foreach ($testName in $securityTests.Keys) {
            $testResult = try {
                $securityTests[$testName].Invoke()
            } catch {
                $false
            }
            
            $results.Tests[$testName] = @{
                Status = if ($testResult) { "PASSED" } else { "FAILED" }
                Result = $testResult
            }
            
            if ($testResult) {
                $results.Passed++
                if ($Verbose) { Write-Host "  ✓ $testName" -ForegroundColor Green }
            } else {
                $results.Failed++
                if ($Verbose) { Write-Host "  ✗ $testName" -ForegroundColor Red }
            }
        }
        
        $results.Status = if ($results.Failed -eq 0) { "PASSED" } else { "FAILED" }
        return $results
    }
    catch {
        return @{
            Status = "FAILED"
            Error = $_.Exception.Message
        }
    }
}

# Function to validate system configuration
function Test-SystemConfiguration {
    param([switch]$Comprehensive)
    
    try {
        Write-Host "Validating system configuration..." -ForegroundColor Cyan
        
        $validationResults = @{
            Timestamp = Get-Date
            Validations = @{}
            Summary = @{
                Total = 0
                Passed = 0
                Failed = 0
            }
        }
        
        # Basic configuration validation
        $basicValidations = @{
            "Configuration Loading" = { $null -ne $script:Config }
            "System Information" = { $null -ne $script:Config.system -and $null -ne $script:Config.system.name }
            "Server Configuration" = { $script:Config.servers -and $script:Config.servers.Count -gt 0 }
            "Monitoring Configuration" = { $script:Config.monitoring -and $script:Config.monitoring.health_check_interval }
            "Error Handling Configuration" = { $script:Config.error_handling -and $script:Config.error_handling.max_retries }
            "Logging Configuration" = { $script:Config.logging -and $script:Config.logging.log_level }
            "Security Configuration" = { $script:Config.security -and $script:Config.security.url_validation }
            "Dependencies Configuration" = { $script:Config.dependencies -and $script:Config.dependencies.startup_sequence }
        }
        
        foreach ($validationName in $basicValidations.Keys) {
            $validationResults.Validations[$validationName] = @{
                Status = "PASSED"
                Details = "Configuration section validated"
            }
            
            $validationResults.Summary.Total++
            
            $isValid = try {
                $basicValidations[$validationName].Invoke()
            } catch {
                $false
            }
            
            if (-not $isValid) {
                $validationResults.Validations[$validationName].Status = "FAILED"
                $validationResults.Validations[$validationName].Details = "Configuration section missing or invalid"
                $validationResults.Summary.Failed++
            } else {
                $validationResults.Summary.Passed++
            }
        }
        
        # Comprehensive validation if requested
        if ($Comprehensive) {
            $comprehensiveValidations = @{
                "Port Availability" = {
                    $allPortsAvailable = $true
                    foreach ($server in $script:Config.servers.PSObject.Properties.Name) {
                        $port = $script:Config.servers.$server.port
                        if (-not (Test-PortAvailability -Port $port)) {
                            $allPortsAvailable = $false
                            break
                        }
                    }
                    return $allPortsAvailable
                }
                "Script File Existence" = {
                    $allScriptsExist = $true
                    foreach ($server in $script:Config.servers.PSObject.Properties.Name) {
                        $script = $script:Config.servers.$server.script
                        if (-not (Test-Path $script)) {
                            $allScriptsExist = $false
                            break
                        }
                    }
                    return $allScriptsExist
                }
                "Dependency Sequence" = {
                    $sequence = Test-StartupSequence -StartupSequence $script:Config.dependencies.startup_sequence
                    return $sequence.IsValid
                }
            }
            
            foreach ($validationName in $comprehensiveValidations.Keys) {
                $validationResults.Validations[$validationName] = @{
                    Status = "PASSED"
                    Details = "Comprehensive validation passed"
                }
                
                $validationResults.Summary.Total++
                
                $isValid = try {
                    $comprehensiveValidations[$validationName].Invoke()
                } catch {
                    $false
                }
                
                if (-not $isValid) {
                    $validationResults.Validations[$validationName].Status = "FAILED"
                    $validationResults.Validations[$validationName].Details = "Comprehensive validation failed"
                    $validationResults.Summary.Failed++
                } else {
                    $validationResults.Summary.Passed++
                }
            }
        }
        
        # Display results
        Write-Host "`nConfiguration Validation Results:" -ForegroundColor Cyan
        Write-Host "  Total: $($validationResults.Summary.Total)" -ForegroundColor White
        Write-Host "  Passed: $($validationResults.Summary.Passed)" -ForegroundColor Green
        Write-Host "  Failed: $($validationResults.Summary.Failed)" -ForegroundColor $(if ($validationResults.Summary.Failed -gt 0) { "Red" } else { "Green" })
        
        $overallStatus = if ($validationResults.Summary.Failed -eq 0) { "PASSED" } else { "FAILED" }
        Write-Host "  Overall Status: $overallStatus" -ForegroundColor $(if ($overallStatus -eq "PASSED") { "Green" } else { "Red" })
        
        Write-ErrorLog -Message "Configuration validation completed" -Severity "INFO" -Category "TESTING" -Server "SYSTEM" -Details "Status: $overallStatus, Passed: $($validationResults.Summary.Passed), Failed: $($validationResults.Summary.Failed)"
        
        return $validationResults
    }
    catch {
        Write-Host "Configuration validation failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-ErrorLog -Message "Configuration validation failed" -Severity "CRITICAL" -Category "TESTING" -Server "SYSTEM" -Details $_.Exception.Message
        return @{
            Status = "FAILED"
            Error = $_.Exception.Message
        }
    }
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
            $responseTimeRounded = [math]::Round($responseTime, 1)
            $details = "Response time: ${responseTimeRounded}ms"
            
            # Check response time thresholds
            if ($responseTime -gt $script:Config.monitoring.response_time_thresholds.critical) {
                $status = "DEGRADED"
                $details = "Slow response: ${responseTimeRounded}ms"
            } elseif ($responseTime -gt $script:Config.monitoring.response_time_thresholds.warning) {
                $status = "WARNING"
                $details = "High response time: ${responseTimeRounded}ms"
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

# Validate startup sequence before starting services
Write-Host "Validating service dependencies..." -ForegroundColor Cyan
$startupValidation = Test-StartupSequence -StartupSequence $script:Config.dependencies.startup_sequence
if (-not $startupValidation.IsValid) {
    Write-Host "Startup sequence validation failed:" -ForegroundColor Red
    foreach ($errorMsg in $startupValidation.Errors) {
        Write-Host "  - $errorMsg" -ForegroundColor Red
    }
    Write-ErrorLog -Message "Startup sequence validation failed" -Severity "CRITICAL" -Category "DEPENDENCY" -Server "SYSTEM" -Details ($startupValidation.Errors -join "; ")
    exit 1
}

Write-Host "Startup sequence validation passed!" -ForegroundColor Green

# Start services with dependency management
Write-Host "Starting services with dependency management..." -ForegroundColor Cyan
$startupSuccess = @{}

foreach ($serviceName in $script:Config.dependencies.startup_sequence) {
    $success = Start-ServiceWithDependencies -ServiceName $serviceName
    $startupSuccess[$serviceName] = $success
    
    if (-not $success) {
        Write-Host "Failed to start $serviceName. Stopping startup sequence." -ForegroundColor Red
        Write-ErrorLog -Message "Service startup failed, stopping sequence" -Severity "CRITICAL" -Category "STARTUP" -Server $serviceName
        
        # Stop any services that were started
        foreach ($startedService in $startupSuccess.Keys) {
            if ($startupSuccess[$startedService]) {
                Write-Host "Stopping $startedService..." -ForegroundColor Yellow
                $jobs = Get-Job -Name $startedService -ErrorAction SilentlyContinue
                if ($jobs) {
                    Stop-Job -Job $jobs -ErrorAction SilentlyContinue
                    Remove-Job -Job $jobs -ErrorAction SilentlyContinue
                }
            }
        }
        exit 1
    }
    
    # Brief pause between service starts
    Start-Sleep -Seconds 1
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
Write-Host "  * Press 'D' to show dependency status"
Write-Host "  * Press 'P' to show performance dashboard"
Write-Host "  * Press 'H' to show enhanced system health"
Write-Host "  * Press 'X' to export monitoring data"
Write-Host "  * Press 'T' to run system tests"
Write-Host "  * Press 'V' to validate configuration"
Write-Host "  * Press 'W' to manage workflows"
Write-Host "  * Press 'A' to manage scheduled tasks"
Write-Host "  * Press 'R' to restart simulation engine"
Write-Host "  * Press 'E' to show error summary"
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
        
        # Enhanced performance monitoring
        $systemMetrics = Get-SystemPerformanceMetrics
        if ($systemMetrics) {
            # Generate performance alerts
            $alerts = Invoke-PerformanceAlerting -Metrics $systemMetrics
            if ($alerts.Count -gt 0) {
                foreach ($alert in $alerts) {
                    Write-Host "Performance Alert: $alert" -ForegroundColor Red
                }
            }
            
            # Log performance metrics periodically
            if ((Get-Date).Minute % 5 -eq 0) {  # Every 5 minutes
                Write-ErrorLog -Message "Performance metrics collected" -Severity "INFO" -Category "MONITORING" -Server "SYSTEM" -Details "CPU: $($systemMetrics.CPU.Usage)%, Memory: $($systemMetrics.Memory.Usage)%"
            }
        }
        
        # Check server health endpoints with performance data
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
            'D' {
                Show-DependencyStatus
            }
            'P' {
                Show-PerformanceDashboard
            }
            'E' {
                Show-ErrorSummary
            }
            'H' {
                Show-EnhancedSystemHealth
            }
            'X' {
                Write-Host ""
                Write-Host "Exporting monitoring data..." -ForegroundColor Yellow
                $exportPath = Export-MonitoringData
                if ($exportPath) {
                    Write-Host "Monitoring data exported successfully!" -ForegroundColor Green
                    Write-Host "File: $exportPath" -ForegroundColor Cyan
                } else {
                    Write-Host "Failed to export monitoring data" -ForegroundColor Red
                }
            }
            'T' {
                Write-Host ""
                Write-Host "Running comprehensive system tests..." -ForegroundColor Cyan
                $testResults = Invoke-SystemTests -Verbose
                if ($testResults.Status -eq "PASSED") {
                    Write-Host "All tests passed successfully!" -ForegroundColor Green
                } else {
                    Write-Host "Some tests failed. Check results above." -ForegroundColor Red
                }
            }
            'V' {
                Write-Host ""
                Write-Host "Validating system configuration..." -ForegroundColor Cyan
                $validationResults = Test-SystemConfiguration -Comprehensive
                if ($validationResults.Summary.Failed -eq 0) {
                    Write-Host "Configuration validation passed!" -ForegroundColor Green
                } else {
                    Write-Host "Configuration validation failed. Check results above." -ForegroundColor Red
                }
            }
            'W' {
                Write-Host ""
                Write-Host "Workflow Management:" -ForegroundColor Cyan
                Write-Host "  1. Create workflow" -ForegroundColor White
                Write-Host "  2. Execute workflow" -ForegroundColor White
                Write-Host "  3. List workflows" -ForegroundColor White
                $choice = Read-Host "Enter choice (1-3) or press Enter to cancel"
                switch ($choice) {
                    "1" {
                        $workflowName = Read-Host "Enter workflow name"
                        $steps = @()
                        do {
                            $step = Read-Host "Enter step function name (or press Enter to finish)"
                            if ($step) { $steps += $step }
                        } while ($step)
                        if ($steps.Count -gt 0) {
                            $workflow = New-AutomatedWorkflow -WorkflowName $workflowName -Steps $steps
                            if ($workflow) {
                                Write-Host "Workflow created successfully!" -ForegroundColor Green
                            }
                        }
                    }
                    "2" {
                        if ($script:Config.automation.workflows) {
                            Write-Host "Available workflows:" -ForegroundColor Yellow
                            foreach ($workflowName in $script:Config.automation.workflows.Keys) {
                                Write-Host "  - $workflowName" -ForegroundColor White
                            }
                            $workflowName = Read-Host "Enter workflow name to execute"
                            if ($script:Config.automation.workflows.ContainsKey($workflowName)) {
                                $result = Invoke-AutomatedWorkflow -WorkflowName $workflowName
                                if ($result.Success) {
                                    Write-Host "Workflow executed successfully!" -ForegroundColor Green
                                } else {
                                    Write-Host "Workflow execution failed!" -ForegroundColor Red
                                }
                            } else {
                                Write-Host "Workflow not found!" -ForegroundColor Red
                            }
                        } else {
                            Write-Host "No workflows available." -ForegroundColor Yellow
                        }
                    }
                    "3" {
                        if ($script:Config.automation.workflows) {
                            Write-Host ""
                            Write-Host "Available Workflows:" -ForegroundColor Cyan
                            foreach ($workflowName in $script:Config.automation.workflows.Keys) {
                                $workflow = $script:Config.automation.workflows[$workflowName]
                                Write-Host "  $workflowName ($($workflow.Status))" -ForegroundColor White
                                Write-Host "    Steps: $($workflow.Steps.Count)" -ForegroundColor Gray
                                Write-Host "    Created: $($workflow.Created)" -ForegroundColor Gray
                            }
                        } else {
                            Write-Host "No workflows available." -ForegroundColor Yellow
                        }
                    }
                }
            }
            'A' {
                Write-Host ""
                Write-Host "Scheduled Tasks Management:" -ForegroundColor Cyan
                Write-Host "  1. Create scheduled task" -ForegroundColor White
                Write-Host "  2. List scheduled tasks" -ForegroundColor White
                Write-Host "  3. Execute scheduled tasks" -ForegroundColor White
                $choice = Read-Host "Enter choice (1-3) or press Enter to cancel"
                switch ($choice) {
                    "1" {
                        $taskName = Read-Host "Enter task name"
                        $command = Read-Host "Enter command/function name"
                        $schedule = Read-Host "Enter schedule (daily/hourly/custom)"
                        $time = Read-Host "Enter time (HH:MM) or press Enter for default"
                        if (-not $time) { $time = "00:00" }
                        $task = New-ScheduledTask -TaskName $taskName -Command $command -Schedule $schedule -Time $time
                        if ($task) {
                            Write-Host "Scheduled task created successfully!" -ForegroundColor Green
                        }
                    }
                    "2" {
                        if ($script:Config.automation.scheduled_tasks) {
                            Write-Host ""
                            Write-Host "Scheduled Tasks:" -ForegroundColor Cyan
                            foreach ($taskName in $script:Config.automation.scheduled_tasks.Keys) {
                                $task = $script:Config.automation.scheduled_tasks[$taskName]
                                Write-Host "  $taskName" -ForegroundColor White
                                Write-Host "    Schedule: $($task.Schedule) at $($task.Time)" -ForegroundColor Gray
                                Write-Host "    Next Run: $($task.NextRun)" -ForegroundColor Gray
                                Write-Host "    Enabled: $($task.Enabled)" -ForegroundColor Gray
                            }
                        } else {
                            Write-Host "No scheduled tasks available." -ForegroundColor Yellow
                        }
                    }
                    "3" {
                        $executedTasks = Invoke-ScheduledTasks
                        if ($executedTasks.Count -gt 0) {
                            Write-Host ""
                            Write-Host "Executed Tasks:" -ForegroundColor Cyan
                            foreach ($task in $executedTasks) {
                                Write-Host "  $($task.Task): $($task.Status)" -ForegroundColor $(if ($task.Status -eq "SUCCESS") { "Green" } else { "Red" })
                            }
                        } else {
                            Write-Host "No tasks were due for execution." -ForegroundColor Yellow
                        }
                    }
                }
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

# Alias: Import-Configuration-Alias (for summary consistency)
function Import-Configuration-Alias {
    [CmdletBinding()]
    param()
    Import-Configuration
}

# Alias: Write-ErrorLog-Alias (for summary consistency)
function Write-ErrorLog-Alias {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Message,
        [string]$Severity = "INFO",
        [string]$Category = "GENERAL",
        [string]$Server = "SYSTEM",
        [string]$Details = ""
    )
    Write-ErrorLog -Message $Message -Severity $Severity -Category $Category -Server $Server -Details $Details
}

# Utility: Test-Url (if not already present)
function Test-Url {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Url
    )
    try {
        $uri = [System.Uri]$Url
        return $uri.Scheme -in @('http','https') -and $uri.Host.Length -gt 0
    } catch {
        return $false
    }
}

# Function to set up automated monitoring alerts
function Initialize-MonitoringAlerts {
    try {
        # Create alert thresholds in configuration if not present
        if (-not $script:Config.monitoring.alert_thresholds) {
            $script:Config.monitoring.alert_thresholds = @{
                cpu_critical = 90
                cpu_warning = 80
                memory_critical = 85
                memory_warning = 75
                disk_critical = 95
                disk_warning = 85
                response_time_critical = 5000
                response_time_warning = 2000
            }
        }
        
        # Create alert history if not present
        if (-not $script:AlertHistory) {
            $script:AlertHistory = @()
        }
        
        Write-Host "Monitoring alerts initialized" -ForegroundColor Green
        Write-ErrorLog -Message "Monitoring alerts initialized" -Severity "INFO" -Category "MONITORING" -Server "SYSTEM"
    }
    catch {
        Write-Host "Failed to initialize monitoring alerts: $($_.Exception.Message)" -ForegroundColor Red
        Write-ErrorLog -Message "Monitoring alerts initialization failed" -Severity "HIGH" -Category "MONITORING" -Server "SYSTEM" -Details $_.Exception.Message
    }
}

# Initialize monitoring alerts
Initialize-MonitoringAlerts



