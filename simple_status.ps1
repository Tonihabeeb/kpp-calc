Write-Host "📊 KPP Synchronized System Status:" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Test Backend
try {
    $backend = Invoke-WebRequest -Uri "http://localhost:9100/status" -UseBasicParsing -TimeoutSec 3
    Write-Host "✅ Flask Backend`t| Port 9100 | 🟢 HEALTHY" -ForegroundColor Green
    $backendStatus = $backend.Content | ConvertFrom-Json
} catch {
    Write-Host "❌ Flask Backend`t| Port 9100 | 🔴 OFFLINE" -ForegroundColor Red
}

# Test Master Clock
try {
    $masterClock = Invoke-WebRequest -Uri "http://localhost:9200/health" -UseBasicParsing -TimeoutSec 3
    Write-Host "✅ Master Clock`t| Port 9200 | 🟢 HEALTHY" -ForegroundColor Green
} catch {
    Write-Host "❌ Master Clock`t| Port 9200 | 🔴 OFFLINE" -ForegroundColor Red
}

# Test WebSocket
try {
    $websocket = Invoke-WebRequest -Uri "http://localhost:9101" -UseBasicParsing -TimeoutSec 3
    Write-Host "✅ WebSocket Server`t| Port 9101 | 🟢 HEALTHY" -ForegroundColor Green
} catch {
    Write-Host "❌ WebSocket Server`t| Port 9101 | 🔴 OFFLINE" -ForegroundColor Red
}

# Test Dash Frontend
try {
    $dash = Invoke-WebRequest -Uri "http://localhost:9103" -UseBasicParsing -TimeoutSec 3
    Write-Host "✅ Dash Frontend`t| Port 9103 | 🟢 HEALTHY" -ForegroundColor Green
} catch {
    Write-Host "❌ Dash Frontend`t| Port 9103 | 🔴 OFFLINE" -ForegroundColor Red
}

Write-Host "-" * 50 -ForegroundColor Gray

# Show backend details if available
if ($backendStatus) {
    Write-Host "`n📈 Backend Details:" -ForegroundColor Cyan
    Write-Host "   Backend Status:     $($backendStatus.backend_status)" -ForegroundColor White
    Write-Host "   Engine Initialized: $($backendStatus.engine_initialized)" -ForegroundColor White
    Write-Host "   Engine Running:     $($backendStatus.engine_running)" -ForegroundColor White
    Write-Host "   Simulation Running: $($backendStatus.simulation_running)" -ForegroundColor White
    Write-Host "   Engine Time:        $($backendStatus.engine_time) seconds" -ForegroundColor White
}

Write-Host "`n🌐 Access URLs:" -ForegroundColor Cyan
Write-Host "  • Dashboard:       http://localhost:9103" -ForegroundColor White
Write-Host "  • Backend API:     http://localhost:9100/status" -ForegroundColor White
Write-Host "  • Master Clock:    http://localhost:9200/metrics" -ForegroundColor White
Write-Host "  • WebSocket:       http://localhost:9101" -ForegroundColor White

Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "KPP Simulator Status Check Complete" -ForegroundColor Cyan 