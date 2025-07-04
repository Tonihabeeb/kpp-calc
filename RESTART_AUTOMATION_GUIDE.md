# KPP Simulator Clean Restart Automation Guide

This guide covers the automated clean restart scripts for the KPP Simulator system.

## Overview

When the KPP simulation "crashes" or gets stuck, these scripts automatically perform a clean restart:
1. **Stop** the simulation engine cleanly
2. **Wait** for proper shutdown
3. **Restart** the simulation with fresh state
4. **Verify** successful restart

**Note**: These scripts restart only the **simulation engine**, not the servers. All backend servers (Flask, WebSocket, Dash, Master Clock) continue running.

## Available Scripts

### 🎯 Integrated Main Server Launcher (NEW - Recommended)
```powershell
powershell -ExecutionPolicy Bypass -File start_sync_system.ps1 -RestartSimulation
```

**Features:**
- ✅ **Integrated into main server launcher**
- ✅ Full server status checking
- ✅ Detailed step-by-step output
- ✅ Error handling and validation
- ✅ Colorized output
- ✅ Comprehensive status reporting
- ✅ **Interactive restart during server monitoring (Press 'R')**

### 🔷 PowerShell Script (Standalone)
```powershell
powershell -ExecutionPolicy Bypass -File restart_simulation.ps1
```

**Features:**
- ✅ Full server status checking
- ✅ Detailed step-by-step output
- ✅ Error handling and validation
- ✅ Colorized output
- ✅ Comprehensive status reporting

### 🐍 Python Script (Cross-platform)
```bash
python restart_simulation.py
```

**Features:**
- ✅ Works on Windows, Linux, macOS
- ✅ Colored terminal output
- ✅ Full error handling
- ✅ Status validation
- ✅ Requires `requests` library

### 📁 Batch File - Integrated (NEW)
```cmd
restart_simulation_integrated.bat
# or
cmd /c restart_simulation_integrated.bat
```

**Features:**
- ✅ Uses integrated main launcher
- ✅ Simple double-click operation
- ✅ Full error checking and validation
- ✅ Professional output

### 📁 Batch File - Standalone (Simple)
```cmd
restart_simulation.bat
# or
cmd /c restart_simulation.bat
```

**Features:**
- ✅ Simple and fast
- ✅ No dependencies
- ✅ Basic error checking
- ✅ Minimal output

## When to Use

### Use Restart Automation When:
- ❌ Simulation shows "System Stopped"
- ❌ Charts stop updating
- ❌ Dashboard shows stale data
- ❌ Simulation engine appears frozen
- ❌ Data flow issues between components

### Don't Use When:
- 🛑 Servers are not running
- 🛑 Backend (port 9100) is down
- 🛑 Network connectivity issues
- 🛑 Port conflicts

## Usage Examples

### Quick Restart (Integrated - Recommended)
```powershell
# Using main server launcher - most comprehensive
powershell -ExecutionPolicy Bypass -File start_sync_system.ps1 -RestartSimulation

# Or using batch wrapper
restart_simulation_integrated.bat
```

### Interactive Restart (During Server Monitoring)
```powershell
# Start the server system and monitor
powershell -ExecutionPolicy Bypass -File start_sync_system.ps1

# Then press 'R' anytime to restart simulation
# Press 'S' to show server status
# Press 'Q' to quit all servers
```

### Quick Restart (Standalone Scripts)
```powershell
# PowerShell standalone
powershell -ExecutionPolicy Bypass -File restart_simulation.ps1

# Python cross-platform
python restart_simulation.py

# Simple batch file
restart_simulation.bat
```

## Expected Output

### Successful Restart
```
KPP Simulator Clean Restart
==================================================

Step 1: Checking server status...
[OK] Flask Backend (9100) : RESPONDING (Status 200)
[OK] WebSocket Server (9101) : RESPONDING (Status 200)
[OK] Dash Frontend (9102) : RESPONDING (Status 200)

Step 2: Getting current simulation status...
   Current Engine Time: 45.2 seconds
   Simulation Running: True

Step 3: Stopping simulation cleanly...
[OK] Simulation stopped successfully

Step 4: Waiting for clean shutdown...
[OK] Shutdown wait complete

Step 5: Restarting simulation...
[OK] Simulation restarted successfully

Step 6: Verifying restart...
New Status:
   Backend Status: running
   Engine Running: True
   Engine Time: 2.1 seconds
   Has Data: True

[SUCCESS] RESTART SUCCESSFUL!
   Simulation is running with fresh data
   Dashboard: http://localhost:9102

==================================================
Clean Restart Process Complete
```

### Failed Restart
```
Step 1: Checking server status...
[ERROR] Flask Backend (9100) : NOT RESPONDING

[ERROR] Some servers are not running. Please start them first.
   Run: python app.py, python main.py, python dash_app.py
```

## Troubleshooting

### Script Fails to Run
```bash
# For PowerShell execution policy issues:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# For Python missing requests:
pip install requests

# For batch file in PowerShell:
cmd /c restart_simulation.bat
```

### Servers Not Running
If the restart script reports servers not running:
```bash
# Start all servers manually:
python app.py           # Terminal 1
python main.py          # Terminal 2  
python dash_app.py      # Terminal 3
python realtime_sync_master.py  # Terminal 4

# Then run restart script
```

### Simulation Won't Start
If restart fails repeatedly:
1. Check backend logs: `Get-Content simulation.log -Tail 20`
2. Verify server status: `http://localhost:9100/status`
3. Restart all servers if needed
4. Check for port conflicts

## Integration with Monitoring

### Automated Monitoring (Optional)
Create a monitoring script that runs restart automatically:

```powershell
# monitor_and_restart.ps1
while ($true) {
    $status = Invoke-WebRequest "http://localhost:9100/status" | ConvertFrom-Json
    if (-not $status.simulation_running) {
        Write-Host "Simulation stopped - auto-restarting..."
        .\restart_simulation.ps1
    }
    Start-Sleep 30
}
```

## Performance Impact

- **Restart Time**: ~5-10 seconds
- **Data Loss**: Current simulation state is reset
- **Server Impact**: Minimal (only simulation engine restarts)
- **Memory Usage**: Clears simulation memory, reduces RAM usage

## Files Created

- `restart_simulation.ps1` - PowerShell automation
- `restart_simulation.py` - Python automation  
- `restart_simulation.bat` - Batch file automation
- `RESTART_AUTOMATION_GUIDE.md` - This guide

## Quick Reference

| Method | Command | Platform | Features |
|--------|---------|----------|----------|
| **Integrated (Recommended)** | `powershell -ExecutionPolicy Bypass -File start_sync_system.ps1 -RestartSimulation` | Windows | **Most comprehensive** |
| **Interactive** | Press 'R' during server monitoring | Windows | **Real-time restart** |
| **Batch Integrated** | `restart_simulation_integrated.bat` | Windows | **Easy double-click** |
| PowerShell Standalone | `powershell -ExecutionPolicy Bypass -File restart_simulation.ps1` | Windows | Full-featured |
| Python | `python restart_simulation.py` | Cross-platform | Portable |
| Batch Simple | `restart_simulation.bat` | Windows | Basic |

---

🎯 **Remember**: These scripts only restart the simulation engine. If you need to restart all servers, use the full system startup scripts instead. 