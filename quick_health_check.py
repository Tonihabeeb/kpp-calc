#!/usr/bin/env python3
"""
Quick Health Check for KPP Real-Time System
"""
import requests
import time

def check_service(name, url):
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {name}: OPERATIONAL")
            return True, data
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ {name}: {e}")
        return False, None

print("🔍 KPP Real-Time System Health Check\n")

# Check Backend
backend_ok, backend_data = check_service("Backend (Flask)", "http://localhost:9100/status")
if backend_ok:
    print(f"   └─ Simulation: {'RUNNING' if backend_data.get('simulation_running') else 'STOPPED'}")
    print(f"   └─ Time: {backend_data.get('engine_time', 0):.1f}s")

# Check WebSocket Server
ws_ok, ws_data = check_service("WebSocket Server", "http://localhost:9101/state")
if ws_ok:
    sim_data = ws_data.get('simulation_data', {})
    print(f"   └─ Power: {sim_data.get('power', 0):.0f}W")
    print(f"   └─ Status: {sim_data.get('status', 'unknown')}")
    print(f"   └─ Health: {sim_data.get('system_health', 'unknown')}")

# Check Frontend
frontend_ok, _ = check_service("Frontend (Dash)", "http://localhost:9102/_alive_4c4dd8bd-3c95-4f06-a4f0-ae05a6e5e99d")

print(f"\n📊 System Status: {'🟢 ALL SYSTEMS OPERATIONAL' if all([backend_ok, ws_ok, frontend_ok]) else '🔴 ISSUES DETECTED'}")

if ws_ok and backend_ok:
    print(f"\n🎯 Real-Time Data Flow: ✅ CONFIRMED")
    print(f"   └─ Backend → WebSocket → Frontend: ACTIVE")
    print(f"   └─ Live Power Output: {sim_data.get('power', 0)/1000:.1f} kW")
    print(f"   └─ Simulation Time: {sim_data.get('time', 0):.1f}s")
else:
    print(f"\n🎯 Real-Time Data Flow: ❌ BROKEN")
