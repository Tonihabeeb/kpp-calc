# KPP Simulator Integrated Restart Functionality

## Overview

The restart automation has been successfully integrated into the main KPP Simulator server launcher (`start_sync_system.ps1`), providing seamless restart capabilities without separate scripts.

## New Integrated Features

### 🎯 Command Line Option
```powershell
powershell -ExecutionPolicy Bypass -File start_sync_system.ps1 -RestartSimulation
```

**What it does:**
- ✅ Checks all server status
- ✅ Cleanly stops simulation engine
- ✅ Waits for proper shutdown
- ✅ Restarts simulation with fresh state
- ✅ Verifies successful restart
- ✅ Shows comprehensive status report

### 🔄 Interactive Restart (NEW)
When running the main server launcher normally:
```powershell
powershell -ExecutionPolicy Bypass -File start_sync_system.ps1
```

**Interactive Controls:**
- Press **'R'** - Instant simulation restart
- Press **'S'** - Show server status  
- Press **'Q'** - Quit all servers

### 📁 Easy Batch Wrapper
```cmd
restart_simulation_integrated.bat
```
Double-click to run the integrated restart functionality.

## Usage Scenarios

### Scenario 1: Simulation Crashes During Development
```powershell
# Quick restart without stopping servers
powershell -ExecutionPolicy Bypass -File start_sync_system.ps1 -RestartSimulation
```

### Scenario 2: Server Monitoring with On-Demand Restart
```powershell
# Start monitoring mode
powershell -ExecutionPolicy Bypass -File start_sync_system.ps1

# When simulation needs restart, press 'R'
# Continue monitoring without interruption
```

### Scenario 3: Simple User Operation
```cmd
# Double-click from Windows Explorer
restart_simulation_integrated.bat
```

## Comparison: Standalone vs Integrated

| Feature | Standalone Scripts | Integrated Option |
|---------|-------------------|-------------------|
| **Command** | `restart_simulation.ps1` | `start_sync_system.ps1 -RestartSimulation` |
| **Server Status Check** | ✅ Yes | ✅ Yes |
| **Error Handling** | ✅ Full | ✅ Full |
| **Interactive Mode** | ❌ No | ✅ **Yes (Press 'R')** |
| **Unified Interface** | ❌ Separate | ✅ **Integrated** |
| **Maintenance** | Multiple files | Single main launcher |

## Files Modified/Created

### Modified:
- `start_sync_system.ps1` - Added `-RestartSimulation` parameter and interactive 'R' key

### Created:
- `restart_simulation_integrated.bat` - Batch wrapper for integrated option

### Existing (still available):
- `restart_simulation.ps1` - Standalone PowerShell
- `restart_simulation.py` - Standalone Python  
- `restart_simulation.bat` - Standalone batch

## Benefits of Integration

1. **Single Point of Control** - Everything through main launcher
2. **Interactive Restart** - Press 'R' anytime during monitoring
3. **Consistent Interface** - Same familiar launcher for all operations
4. **Reduced Complexity** - No need to remember multiple scripts
5. **Better User Experience** - Seamless workflow integration

## Updated Help System

The main launcher now shows all options:
```
Usage Options:
  .\start_sync_system.ps1                 - Start all servers
  .\start_sync_system.ps1 -Test           - Test system components  
  .\start_sync_system.ps1 -Stop           - Stop all servers
  .\start_sync_system.ps1 -RestartSimulation - Restart simulation engine only
```

## Migration Path

### Current Users:
- **Keep using standalone scripts** - They still work perfectly
- **Gradually migrate** to integrated option for better experience

### New Users:
- **Start with integrated option** - Most comprehensive and user-friendly
- **Use interactive mode** for ongoing monitoring and development

## Next Steps

1. **Test integrated functionality** - Verify it works in your environment
2. **Update workflows** - Consider switching to integrated option
3. **Documentation** - Update team procedures to use new integrated features
4. **Feedback** - Report any issues or suggestions for improvement

---

🎯 **Recommendation**: Use the integrated option for the best experience. The standalone scripts remain available for specific use cases or backward compatibility.

## Quick Commands

```powershell
# Start servers and enable interactive restart
powershell -ExecutionPolicy Bypass -File start_sync_system.ps1

# Direct restart (servers must be running)  
powershell -ExecutionPolicy Bypass -File start_sync_system.ps1 -RestartSimulation

# Simple batch file
restart_simulation_integrated.bat
```

The KPP Simulator now provides a unified, professional interface for all server management and restart operations! 🚀 