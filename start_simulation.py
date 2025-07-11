#!/usr/bin/env python3
"""
Simple script to start the KPP simulation
"""

import requests
import time
import json

def start_simulation():
    """Start the KPP simulation"""
    try:
        # Start the simulation
        response = requests.post(
            "http://localhost:9100/api/simulation/control",
            json={"action": "start"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Simulation started successfully!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Failed to start simulation: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to simulation API. Make sure the backend is running on port 9100.")
    except Exception as e:
        print(f"❌ Error starting simulation: {e}")

def start_compressor():
    """Start the compressor"""
    try:
        response = requests.post(
            "http://localhost:9100/api/simulation/compressor",
            json={"action": "start"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Compressor started successfully!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Failed to start compressor: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to simulation API. Make sure the backend is running on port 9100.")
    except Exception as e:
        print(f"❌ Error starting compressor: {e}")

def check_status():
    """Check simulation status"""
    try:
        response = requests.get("http://localhost:9100/api/simulation/state", timeout=5)
        if response.status_code == 200:
            state = response.json()
            print("📊 Current Simulation Status:")
            print(f"   Status: {state.get('status', 'unknown')}")
            print(f"   Power: {state.get('power', 0):.1f} W")
            print(f"   Torque: {state.get('torque', 0):.1f} N·m")
            print(f"   RPM: {state.get('rpm', 0):.1f}")
            print(f"   Efficiency: {state.get('efficiency', 0):.1%}")
        else:
            print(f"❌ Failed to get status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking status: {e}")

if __name__ == "__main__":
    print("🚀 KPP Simulation Control")
    print("=" * 30)
    
    # Check if API is running
    try:
        response = requests.get("http://localhost:9100/status", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API is running")
        else:
            print("❌ Backend API is not responding properly")
            exit(1)
    except:
        print("❌ Backend API is not running. Please start it first with: python app.py")
        exit(1)
    
    print("\n1. Starting simulation...")
    start_simulation()
    
    print("\n2. Starting compressor...")
    start_compressor()
    
    print("\n3. Checking status...")
    check_status()
    
    print("\n🎉 Simulation should now be running!")
    print("Access the dashboard at: http://localhost:9100/simulation") 