# KPP Simulator System Status Display
Write-Host "📊 KPP Synchronized System Status:" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Function to test endpoint
function Test-ServerEndpoint {
    param([string]$Url, [string]$Name, [string]$Port)
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -UseBasicParsing -TimeoutSec 3
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $Name`t| Port $Port | 🟢 HEALTHY" -ForegroundColor Green
            return $true
        } else {
            Write-Host "⚠️ $Name`t| Port $Port | 🟡 DEGRADED (Status $($response.StatusCode))" -ForegroundColor Yellow
            return $false
        }
    }
    catch {
        Write-Host "❌ $Name`t| Port $Port | 🔴 OFFLINE" -ForegroundColor Red
        return $false
    }
}

# Test all servers
Write-Host "`n🔍 Server Health Check:" -ForegroundColor Yellow
Write-Host "-" * 50 -ForegroundColor Gray

$backendOk = Test-ServerEndpoint "http://localhost:9100/status" "Flask Backend" "9100"
$masterClockOk = Test-ServerEndpoint "http://localhost:9200/health" "Master Clock" "9200"
$websocketOk = Test-ServerEndpoint "http://localhost:9101" "WebSocket Server" "9101"
$dashOk = Test-ServerEndpoint "http://localhost:9103" "Dash Frontend" "9103"

Write-Host "-" * 50 -ForegroundColor Gray

# Show detailed backend status
if ($backendOk) {
    Write-Host "`n📈 Backend Details:" -ForegroundColor Cyan
    try {
        $status = Invoke-WebRequest -Uri "http://localhost:9100/status" -UseBasicParsing | ConvertFrom-Json
        Write-Host "   Backend Status:     $($status.backend_status)" -ForegroundColor White
        Write-Host "   Engine Initialized: $($status.engine_initialized)" -ForegroundColor White
        Write-Host "   Engine Running:     $($status.engine_running)" -ForegroundColor White
        Write-Host "   Simulation Running: $($status.simulation_running)" -ForegroundColor White
        Write-Host "   Engine Time:        $($status.engine_time) seconds" -ForegroundColor White
        Write-Host "   Has Data:           $($status.has_data)" -ForegroundColor White
    }
    catch {
        Write-Host "   Could not retrieve detailed status" -ForegroundColor Red
    }
}

# Show access URLs
Write-Host "`n🌐 Access URLs:" -ForegroundColor Cyan
Write-Host "-" * 50 -ForegroundColor Gray
Write-Host "  • Dashboard:       http://localhost:9103" -ForegroundColor White
Write-Host "  • Backend API:     http://localhost:9100/status" -ForegroundColor White
Write-Host "  • Master Clock:    http://localhost:9200/metrics" -ForegroundColor White
Write-Host "  • WebSocket:       http://localhost:9101" -ForegroundColor White
Write-Host "-" * 50 -ForegroundColor Gray

# Show system summary
$healthyCount = @($backendOk, $masterClockOk, $websocketOk, $dashOk) | Where-Object { $_ } | Measure-Object | Select-Object -ExpandProperty Count
$totalCount = 4

Write-Host "`n📊 System Summary:" -ForegroundColor Cyan
Write-Host "   Healthy Servers: $healthyCount/$totalCount" -ForegroundColor $(if ($healthyCount -eq $totalCount) { "Green" } else { "Yellow" })
Write-Host "   System Status:   $(if ($healthyCount -eq $totalCount) { "🟢 FULLY OPERATIONAL" } else { "🟡 PARTIALLY OPERATIONAL" })" -ForegroundColor $(if ($healthyCount -eq $totalCount) { "Green" } else { "Yellow" })

Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "KPP Simulator Status Check Complete" -ForegroundColor Cyan 