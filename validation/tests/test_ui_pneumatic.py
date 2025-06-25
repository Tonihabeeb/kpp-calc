#!/usr/bin/env python3
"""
Test script to verify Phase 7 pneumatic system UI integration.
This script tests the pneumatic endpoints and simulates the data flow.
"""

import requests
import json
import time
import sys
from threading import Thread

def test_pneumatic_endpoints():
    """Test all pneumatic endpoints to ensure they return proper data"""
    base_url = "http://localhost:5000"
    endpoints = [
        "/data/pneumatic_status",
        "/data/optimization_recommendations", 
        "/data/energy_balance",
        "/data/summary"
    ]
    
    print("Testing pneumatic endpoints...")
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            print(f"\n{endpoint}: Status {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Response keys: {list(data.keys())}")
                if endpoint == "/data/pneumatic_status":
                    # Check for expected pneumatic data structure
                    expected_keys = ["tank_pressure", "pneumatic_performance", "pneumatic_energy", "pneumatic_optimization"]
                    for key in expected_keys:
                        if key in data:
                            print(f"  ✓ {key} present")
                        else:
                            print(f"  ✗ {key} missing")
            else:
                print(f"  Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"  ✗ Connection failed - Flask app not running?")
        except Exception as e:
            print(f"  ✗ Error: {e}")

def test_ui_update_simulation():
    """Simulate UI updates by starting simulation and checking data changes"""
    base_url = "http://localhost:5000"
    
    print("\nTesting UI update simulation...")
    
    try:
        # Start simulation
        start_response = requests.post(f"{base_url}/start", timeout=5)
        print(f"Start simulation: Status {start_response.status_code}")
        
        if start_response.status_code == 200:
            print("  ✓ Simulation started successfully")
            
            # Wait a few seconds for data to accumulate
            print("  Waiting 5 seconds for simulation data...")
            time.sleep(5)
            
            # Check pneumatic status for real data
            status_response = requests.get(f"{base_url}/data/pneumatic_status", timeout=5)
            if status_response.status_code == 200:
                data = status_response.json()
                print(f"  Pneumatic data after simulation:")
                
                if data.get("status") != "no_data":
                    print("  ✓ Pneumatic data is being generated")
                    
                    # Check specific metrics
                    if "tank_pressure" in data and data["tank_pressure"] > 0:
                        print(f"    Tank pressure: {data['tank_pressure']:.2f} Pa")
                    
                    if "pneumatic_performance" in data:
                        perf = data["pneumatic_performance"]
                        print(f"    Average efficiency: {perf.get('average_efficiency', 0)*100:.2f}%")
                        print(f"    Peak efficiency: {perf.get('peak_efficiency', 0)*100:.2f}%")
                        
                    if "pneumatic_energy" in data:
                        energy = data["pneumatic_energy"]
                        print(f"    Total input energy: {energy.get('total_input_energy', 0):.2f} J")
                        print(f"    Overall efficiency: {energy.get('overall_efficiency', 0)*100:.2f}%")
                        
                    if "pneumatic_optimization" in data:
                        opt = data["pneumatic_optimization"]
                        rec_count = opt.get("recommendation_count", 0)
                        print(f"    Active recommendations: {rec_count}")
                        
                else:
                    print("  ✗ No pneumatic data available yet")
            
            # Stop simulation
            stop_response = requests.post(f"{base_url}/stop", timeout=5)
            print(f"  Stop simulation: Status {stop_response.status_code}")
            
        else:
            print(f"  ✗ Failed to start simulation: {start_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("  ✗ Connection failed - Flask app not running?")
    except Exception as e:
        print(f"  ✗ Error: {e}")

def main():
    print("Phase 7 Pneumatic System UI Integration Test")
    print("=" * 50)
    
    # Test endpoints first
    test_pneumatic_endpoints()
    
    # Test simulation and UI updates
    test_ui_update_simulation()
    
    print("\nTest completed!")
    print("\nTo manually test the UI:")
    print("1. Open http://localhost:5000 in your browser")
    print("2. Click 'Start' to begin simulation") 
    print("3. Observe the 'Phase 7 Pneumatic System Analysis' section")
    print("4. Check that metrics update every 2 seconds")
    print("5. Look for optimization recommendations")

if __name__ == "__main__":
    main()
