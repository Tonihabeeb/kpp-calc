#!/usr/bin/env python3
"""
Find optimal electrical load for maximum power generation
"""

import requests
import time

def find_optimal_load():
    """Find the optimal electrical load for maximum power generation"""
    
    print("🎯 FINDING OPTIMAL ELECTRICAL LOAD")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # Test range of load torques
    test_loads = [0, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300]
    results = []
    
    for load_torque in test_loads:
        try:
            # Set load
            requests.post(f"{base_url}/set_load", json={"user_load_torque": load_torque})
            time.sleep(3)  # Wait for system to stabilize
            
            # Get results
            response = requests.get(f"{base_url}/data/live")
            data = response.json()["data"][-1]
            
            power = data['power']
            torque = data['torque']
            efficiency = data['overall_efficiency'] * 100
            
            results.append({
                'load': load_torque,
                'power': power,
                'torque': torque,
                'efficiency': efficiency
            })
            
            print(f"Load {load_torque:3d} Nm: Power={power:7.1f}W ({power/1000:5.2f}kW), Torque={torque:6.1f}Nm, Eff={efficiency:5.1f}%")
            
        except Exception as e:
            print(f"Load {load_torque:3d} Nm: ERROR - {e}")
    
    print()
    
    # Find optimal points
    max_power_result = max(results, key=lambda x: x['power'])
    max_efficiency_result = max(results, key=lambda x: x['efficiency'])
    
    print("📊 OPTIMAL OPERATING POINTS:")
    print(f"🔋 Maximum Power: {max_power_result['power']:.1f}W at {max_power_result['load']}Nm load")
    print(f"⚡ Maximum Efficiency: {max_efficiency_result['efficiency']:.1f}% at {max_efficiency_result['load']}Nm load")
    
    # Calculate mechanical power available
    chain_speed_rad_s = 477.5 * 2 * 3.14159 / 60  # Convert RPM to rad/s
    mechanical_power = 231.1 * chain_speed_rad_s
    print(f"🔧 Available Mechanical Power: {mechanical_power:.0f}W ({mechanical_power/1000:.1f}kW)")
    
    # Set to optimal power point
    optimal_load = max_power_result['load']
    requests.post(f"{base_url}/set_load", json={"user_load_torque": optimal_load})
    time.sleep(3)
    
    # Final test
    response = requests.get(f"{base_url}/data/live")
    data = response.json()["data"][-1]
    
    print()
    print("🎯 FINAL OPTIMAL SETTING:")
    print(f"Load Torque: {optimal_load} Nm")
    print(f"Electrical Power: {data['power']:.0f}W ({data['power']/1000:.2f}kW)")
    print(f"Efficiency: {data['overall_efficiency']*100:.1f}%")
    print(f"Power Factor: {mechanical_power/1000:.1f}kW → {data['power']/1000:.2f}kW = {data['power']/mechanical_power*100:.1f}% conversion")

if __name__ == "__main__":
    find_optimal_load() 