Write-Host "🎯 KPP Simulator Status:" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# Test Backend
Write-Host "Backend (9100):" -ForegroundColor White -NoNewline
try {
    $backend = Invoke-WebRequest -Uri "http://localhost:9100/status" -UseBasicParsing -TimeoutSec 3
    Write-Host " ✅ HEALTHY" -ForegroundColor Green
    $data = $backend.Content | ConvertFrom-Json
    Write-Host "   • Engine: $($data.engine_initialized)" -ForegroundColor Gray
    Write-Host "   • Simulation: $($data.simulation_running)" -ForegroundColor Gray
} catch {
    Write-Host " ❌ OFFLINE" -ForegroundColor Red
}

# Test Master Clock
Write-Host "Master Clock (9200):" -ForegroundColor White -NoNewline
try {
    $master = Invoke-WebRequest -Uri "http://localhost:9200/health" -UseBasicParsing -TimeoutSec 3
    Write-Host " ✅ HEALTHY" -ForegroundColor Green
} catch {
    Write-Host " ❌ OFFLINE" -ForegroundColor Red
}

# Test WebSocket
Write-Host "WebSocket (9101):" -ForegroundColor White -NoNewline
try {
    $ws = Invoke-WebRequest -Uri "http://localhost:9101" -UseBasicParsing -TimeoutSec 3
    Write-Host " ✅ HEALTHY" -ForegroundColor Green
} catch {
    Write-Host " ❌ OFFLINE" -ForegroundColor Red
}

# Test Dashboard
Write-Host "Dashboard (9103):" -ForegroundColor White -NoNewline
try {
    $dash = Invoke-WebRequest -Uri "http://localhost:9103" -UseBasicParsing -TimeoutSec 3
    Write-Host " ✅ HEALTHY" -ForegroundColor Green
} catch {
    Write-Host " ❌ OFFLINE" -ForegroundColor Red
}

Write-Host "=" * 50 -ForegroundColor Cyan
Write-Host "🌐 Access URLs:" -ForegroundColor Yellow
Write-Host "  • Dashboard: http://localhost:9103" -ForegroundColor White
Write-Host "  • Backend API: http://localhost:9100" -ForegroundColor White
Write-Host "  • Master Clock: http://localhost:9200" -ForegroundColor White
Write-Host "  • WebSocket: http://localhost:9101" -ForegroundColor White 