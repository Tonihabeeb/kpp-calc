#!/usr/bin/env python3
"""
Test script for Phase 7 pneumatic system integration.
This script tests the new API endpoints and UI integration.
"""

import sys
import os
import json
import time

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from simulation.engine import SimulationEngine

def test_pneumatic_endpoints():
    """Test the new pneumatic system endpoints"""
    
    print("=== Phase 7 Pneumatic System Integration Test ===")
    print()
    
    with app.test_client() as client:
        print("1. Testing /data/pneumatic_status endpoint...")
        try:
            # Start a brief simulation to generate data
            response = client.post('/start', json={})
            print(f"   Start simulation response: {response.status_code}")
            
            # Wait a moment for data generation
            time.sleep(2)
            
            # Test pneumatic status endpoint
            response = client.get('/data/pneumatic_status')
            if response.status_code == 200:
                data = response.get_json()
                print(f"   ✓ Pneumatic status endpoint working")
                print(f"   Tank pressure: {data.get('tank_pressure', 0):.2f} Pa")
                print(f"   Performance data available: {'performance' in data}")
                print(f"   Energy data available: {'energy' in data}")
            else:
                print(f"   ✗ Pneumatic status endpoint failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ✗ Error testing pneumatic status: {e}")
        
        print()
        print("2. Testing /data/optimization_recommendations endpoint...")
        try:
            response = client.get('/data/optimization_recommendations')
            if response.status_code == 200:
                data = response.get_json()
                print(f"   ✓ Optimization recommendations endpoint working")
                print(f"   Recommendation count: {data.get('count', 0)}")
                if data.get('recommendations'):
                    for i, rec in enumerate(data['recommendations'][:3]):
                        print(f"     {i+1}. {rec.get('target', 'Unknown')}: {rec.get('description', 'No description')}")
                else:
                    print("     No recommendations available (normal for new system)")
            else:
                print(f"   ✗ Optimization recommendations endpoint failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ✗ Error testing optimization recommendations: {e}")
        
        print()
        print("3. Testing /data/energy_balance endpoint...")
        try:
            response = client.get('/data/energy_balance')
            if response.status_code == 200:
                data = response.get_json()
                print(f"   ✓ Energy balance endpoint working")
                if 'energy_summary' in data:
                    summary = data['energy_summary']
                    print(f"   Total input energy: {summary.get('total_input_energy', 0):.2f} J")
                    print(f"   Total output energy: {summary.get('total_output_energy', 0):.2f} J")
                    print(f"   Overall efficiency: {summary.get('overall_efficiency', 0)*100:.2f}%")
                if 'conservation' in data:
                    conservation = data['conservation']
                    print(f"   Energy conservation valid: {conservation.get('conservation_valid', 'Unknown')}")
            else:
                print(f"   ✗ Energy balance endpoint failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ✗ Error testing energy balance: {e}")
        
        print()
        print("4. Testing updated /data/summary endpoint (should include pneumatic data)...")
        try:
            response = client.get('/data/summary')
            if response.status_code == 200:
                data = response.get_json()
                print(f"   ✓ Summary endpoint working")
                print(f"   Tank pressure available: {'tank_pressure' in data}")
                print(f"   Pneumatic performance available: {'pneumatic_performance' in data}")
                print(f"   Pneumatic energy available: {'pneumatic_energy' in data}")
                print(f"   Pneumatic optimization available: {'pneumatic_optimization' in data}")
            else:
                print(f"   ✗ Summary endpoint failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ✗ Error testing summary endpoint: {e}")
        
        # Stop simulation
        try:
            client.post('/stop')
            print("\n   Simulation stopped")
        except:
            pass
    
    print()
    print("=== Integration Test Complete ===")
    print()
    print("Next steps:")
    print("1. Start the Flask app with: python app.py")
    print("2. Navigate to http://localhost:5000")
    print("3. Verify the new Phase 7 pneumatic sections appear")
    print("4. Start a simulation and watch the pneumatic metrics update")

if __name__ == "__main__":
    test_pneumatic_endpoints()
