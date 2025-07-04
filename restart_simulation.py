#!/usr/bin/env python3
"""
KPP Simulator Clean Restart Script
Automatically performs a clean restart of the KPP simulation engine
while keeping all servers running.
"""

import requests
import time
import sys
from typing import Tuple, Dict, Any

def print_colored(message: str, color: str = "white") -> None:
    """Print colored messages (simplified for cross-platform compatibility)"""
    colors = {
        "cyan": "\033[96m",
        "green": "\033[92m", 
        "yellow": "\033[93m",
        "red": "\033[91m",
        "white": "\033[97m",
        "gray": "\033[90m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, '')}{message}{colors['reset']}")

def test_endpoint(url: str, name: str, timeout: int = 5) -> bool:
    """Test if an endpoint is responding"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print_colored(f"✅ {name}: RESPONDING (Status {response.status_code})", "green")
            return True
        else:
            print_colored(f"⚠️ {name}: Status {response.status_code}", "yellow")
            return False
    except requests.exceptions.RequestException as e:
        print_colored(f"❌ {name}: NOT RESPONDING - {str(e)}", "red")
        return False

def get_simulation_status() -> Tuple[bool, Dict[str, Any]]:
    """Get current simulation status"""
    try:
        response = requests.get("http://localhost:9100/status", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, {}
    except requests.exceptions.RequestException:
        return False, {}

def stop_simulation() -> bool:
    """Stop the simulation cleanly"""
    try:
        response = requests.post("http://localhost:9100/stop", timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def start_simulation() -> Tuple[bool, Dict[str, Any]]:
    """Start the simulation"""
    try:
        response = requests.post("http://localhost:9100/start", timeout=10)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, {}
    except requests.exceptions.RequestException:
        return False, {}

def main():
    """Main restart process"""
    print_colored("🔄 KPP Simulator Clean Restart", "cyan")
    print_colored("=" * 50, "cyan")
    
    # Step 1: Check server status
    print_colored("\n🔍 Step 1: Checking server status...", "yellow")
    
    backend_ok = test_endpoint("http://localhost:9100/status", "Flask Backend (9100)")
    websocket_ok = test_endpoint("http://localhost:9101", "WebSocket Server (9101)")
    dash_ok = test_endpoint("http://localhost:9103", "Dash Frontend (9103)")
    
    if not (backend_ok and websocket_ok and dash_ok):
        print_colored("❌ Some servers are not running. Please start them first.", "red")
        print_colored("   Run: python app.py, python main.py, python dash_app.py", "yellow")
        sys.exit(1)
    
    # Step 2: Get current status
    print_colored("\n📊 Step 2: Getting current simulation status...", "yellow")
    
    status_ok, status = get_simulation_status()
    if status_ok:
        print_colored(f"   Current Engine Time: {status.get('engine_time', 'Unknown')} seconds", "white")
        print_colored(f"   Simulation Running: {status.get('simulation_running', 'Unknown')}", "white")
        print_colored(f"   Engine Initialized: {status.get('engine_initialized', 'Unknown')}", "white")
    else:
        print_colored("❌ Could not get simulation status", "red")
        sys.exit(1)
    
    # Step 3: Stop simulation
    print_colored("\n🛑 Step 3: Stopping simulation cleanly...", "yellow")
    
    if stop_simulation():
        print_colored("✅ Simulation stopped successfully", "green")
    else:
        print_colored("❌ Failed to stop simulation", "red")
        sys.exit(1)
    
    # Step 4: Wait for clean shutdown
    print_colored("\n⏳ Step 4: Waiting for clean shutdown...", "yellow")
    time.sleep(2)
    print_colored("✅ Shutdown wait complete", "green")
    
    # Step 5: Restart simulation
    print_colored("\n🚀 Step 5: Restarting simulation...", "yellow")
    
    start_ok, start_data = start_simulation()
    if start_ok:
        print_colored("✅ Simulation restarted successfully", "green")
        print_colored(f"   Message: {start_data.get('message', 'Started')}", "white")
        print_colored(f"   Trace ID: {start_data.get('trace_id', 'N/A')}", "gray")
    else:
        print_colored("❌ Failed to restart simulation", "red")
        sys.exit(1)
    
    # Step 6: Verify restart
    print_colored("\n✅ Step 6: Verifying restart...", "yellow")
    time.sleep(2)
    
    new_status_ok, new_status = get_simulation_status()
    if new_status_ok:
        print_colored("📊 New Status:", "cyan")
        print_colored(f"   Backend Status: {new_status.get('backend_status', 'Unknown')}", "white")
        print_colored(f"   Engine Running: {new_status.get('engine_running', 'Unknown')}", "white")
        print_colored(f"   Engine Time: {new_status.get('engine_time', 'Unknown')} seconds", "white")
        print_colored(f"   Has Data: {new_status.get('has_data', 'Unknown')}", "white")
        
        if new_status.get('simulation_running') and new_status.get('engine_running'):
            print_colored("\n🎉 RESTART SUCCESSFUL!", "green")
            print_colored("   Simulation is running with fresh data", "green")
            print_colored("   Dashboard: http://localhost:9103", "cyan")
            print_colored("   Backend API: http://localhost:9100/status", "cyan")
        else:
            print_colored("\n⚠️ Restart completed but simulation may not be running properly", "yellow")
    else:
        print_colored("❌ Could not verify restart status", "red")
    
    print_colored("\n" + "=" * 50, "cyan")
    print_colored("🔄 Clean Restart Process Complete", "cyan")

if __name__ == "__main__":
    main() 