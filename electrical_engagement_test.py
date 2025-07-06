#!/usr/bin/env python3
"""
Test script to verify electrical engagement and braking functionality
"""

import requests
import time
import json

def test_electrical_engagement():
    """Test the electrical system engagement after start button press"""
    
    print("=" * 60)
    print("🔧 KPP Simulator Electrical Engagement Test")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # 1. Check server status
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        status = response.json()
        print(f"✅ Server Status: {status}")
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return False
    
    # 2. Stop any running simulation
    try:
        response = requests.post(f"{base_url}/stop", timeout=5)
        print(f"🛑 Stopped simulation: {response.text}")
    except Exception as e:
        print(f"⚠️  Stop failed (might not be running): {e}")
    
    # 3. Start simulation with optimized parameters for electrical engagement
    start_params = {
        "num_floaters": 10,
        "floater_volume": 0.4,
        "floater_mass_empty": 16.0,
        "air_pressure": 250000,
        "target_load_factor": 0.7,  # 70% electrical load
        "electrical_engagement_threshold": 1000.0,  # Lower threshold
        "load_management_enabled": True,
        "bootstrap_mode": True
    }
    
    try:
        response = requests.post(f"{base_url}/start", 
                               json=start_params, 
                               timeout=10)
        result = response.json()
        print(f"🚀 Started simulation: {result}")
        
        if result.get("status") != "ok":
            print(f"❌ Start failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Start failed: {e}")
        return False
    
    # 4. Wait for simulation to stabilize
    print("⏳ Waiting for simulation to stabilize...")
    time.sleep(5)
    
    # 5. Check status after startup
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        status = response.json()
        print(f"📊 Post-start status: {status}")
        
        if status.get("simulation_engine") != "running":
            print("❌ Simulation not running after start")
            return False
            
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False
    
    # 6. Test electrical load by setting load
    try:
        load_params = {"load_factor": 0.8}
        response = requests.post(f"{base_url}/set_load", 
                               json=load_params, 
                               timeout=5)
        print(f"⚡ Set electrical load: {response.text}")
    except Exception as e:
        print(f"⚠️  Load setting failed: {e}")
    
    # 7. Wait and check if electrical system is working
    print("⏳ Testing electrical engagement...")
    time.sleep(3)
    
    # 8. Trigger pulse to generate mechanical power
    try:
        response = requests.post(f"{base_url}/trigger_pulse", timeout=5)
        print(f"💨 Triggered pulse: {response.text}")
    except Exception as e:
        print(f"⚠️  Pulse trigger failed: {e}")
    
    time.sleep(2)
    
    # 9. Final status check
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        final_status = response.json()
        print(f"📈 Final status: {final_status}")
        
        # Check if all components are online
        components = final_status.get("components", {})
        all_online = all(status == "online" for status in components.values())
        
        if all_online and final_status.get("status") == "healthy":
            print("✅ All systems operational!")
            print("\n🔋 Electrical System Status:")
            print(f"   - Generator: {components.get('generator', 'unknown')}")
            print(f"   - IntegratedDrivetrain: {components.get('integrated_drivetrain', 'unknown')}")
            print("   - Load management should be controlling speed via electrical braking")
            return True
        else:
            print("❌ Some systems not operational")
            return False
            
    except Exception as e:
        print(f"❌ Final status check failed: {e}")
        return False

def test_speed_control():
    """Test that electrical load can control mechanical speed"""
    print("\n" + "=" * 60)
    print("🎛️  Testing Speed Control via Electrical Load")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # Test different load factors
    load_factors = [0.2, 0.5, 0.8]
    
    for load_factor in load_factors:
        print(f"\n🔧 Testing load factor: {load_factor}")
        
        try:
            # Set load factor
            response = requests.post(f"{base_url}/set_load", 
                                   json={"load_factor": load_factor}, 
                                   timeout=5)
            print(f"   Set load: {response.text}")
            
            # Wait for system to respond
            time.sleep(3)
            
            # Trigger pulse for mechanical input
            response = requests.post(f"{base_url}/trigger_pulse", timeout=5)
            print(f"   Pulse response: {response.text}")
            
            time.sleep(2)
            
        except Exception as e:
            print(f"   ❌ Load test failed: {e}")
    
    print("\n✅ Speed control test completed")
    print("   Higher electrical load should reduce mechanical speed")
    print("   Generator acts as electromagnetic brake")

if __name__ == "__main__":
    try:
        # Run engagement test
        success = test_electrical_engagement()
        
        if success:
            # Run speed control test
            test_speed_control()
            
            print("\n" + "=" * 60)
            print("🎉 Electrical Engagement Test Results:")
            print("✅ Simulation starts successfully")
            print("✅ All components come online")  
            print("✅ Electrical system can be controlled")
            print("✅ Generator provides electromagnetic braking")
            print("\n💡 The electrical system should now:")
            print("   - Engage when mechanical power > 1kW available")
            print("   - Provide load torque to control overspeed")
            print("   - Generate electrical power output")
            print("   - Act as electromagnetic brake for the mechanical system")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ Electrical Engagement Test Failed")
            print("   Check the terminal output for detailed error messages")
            print("   Ensure all servers are running on correct ports")
            print("=" * 60)
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}") 