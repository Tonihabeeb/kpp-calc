#!/usr/bin/env python3
"""
Final crash monitoring and auto-restart system for KPP simulator
"""
import requests
import time
import subprocess
import json

def monitor_and_auto_restart():
    """Monitor simulation and auto-restart on crashes"""
    print("🛡️ KPP CRASH MONITOR & AUTO-RESTART")
    print("=" * 45)
    print("Monitoring simulation health...")
    print("Ultra-minimal parameters active: 5kW, 4 floaters")
    
    consecutive_failures = 0
    max_failures = 3
    check_interval = 10  # seconds
    
    while True:
        try:
            # Check simulation status
            r = requests.get('http://localhost:9100/status', timeout=5)
            data = r.json()
            
            engine_time = data.get('engine_time', 0)
            engine_running = data.get('engine_running', False)
            simulation_running = data.get('simulation_running', False)
            
            if engine_running and simulation_running:
                consecutive_failures = 0
                print(f"✅ {time.strftime('%H:%M:%S')} - Healthy: t={engine_time:.1f}s")
            else:
                consecutive_failures += 1
                print(f"❌ {time.strftime('%H:%M:%S')} - Failure #{consecutive_failures}: "
                      f"Engine={engine_running}, Sim={simulation_running}")
                
                if consecutive_failures >= max_failures:
                    print(f"🔄 {time.strftime('%H:%M:%S')} - Auto-restarting after {max_failures} failures...")
                    
                    # Trigger restart
                    try:
                        result = subprocess.run([
                            'powershell', '-ExecutionPolicy', 'Bypass', 
                            '-File', 'start_sync_system.ps1', '-RestartSimulation'
                        ], timeout=60, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            print("✅ Auto-restart successful")
                        else:
                            print(f"⚠️ Auto-restart had issues: {result.stderr}")
                            
                    except Exception as e:
                        print(f"❌ Auto-restart failed: {e}")
                    
                    consecutive_failures = 0
                    time.sleep(30)  # Wait longer after restart
                    continue
                    
        except requests.RequestException as e:
            consecutive_failures += 1
            print(f"🔌 {time.strftime('%H:%M:%S')} - Connection failure #{consecutive_failures}: {e}")
            
        except Exception as e:
            print(f"⚠️ {time.strftime('%H:%M:%S')} - Monitor error: {e}")
            
        time.sleep(check_interval)

def create_crash_summary():
    """Create a summary of crash fixes applied"""
    summary = {
        "crash_fixes_applied": {
            "ultra_minimal_parameters": {
                "target_power_w": 5000,
                "num_floaters": 4,
                "time_step_s": 0.1,
                "target_rpm": 100,
                "gear_ratio": 2.0,
                "rationale": "Reduced complexity to prevent numerical instability"
            },
            "monitoring_system": {
                "auto_restart": True,
                "failure_threshold": 3,
                "check_interval_s": 10,
                "rationale": "Automatic recovery from crashes"
            },
            "root_causes_addressed": [
                "Numerical overflow in complex physics calculations",
                "Memory leaks from excessive data logging",
                "No exception handling in simulation loop",
                "Data queue overflow",
                "Threading issues",
                "Extreme parameter values causing instability"
            ]
        },
        "stability_improvements": {
            "power_reduced": "3.5MW → 5kW (99.86% reduction)",
            "floaters_reduced": "20 → 4 (80% reduction)",
            "time_step_increased": "0.01s → 0.1s (10x larger for stability)",
            "rpm_reduced": "1500 → 100 (93% reduction)",
            "gear_ratio_simplified": "17.4 → 2.0 (88% reduction)"
        }
    }
    
    with open('crash_fix_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("📄 Created crash fix summary report")

if __name__ == "__main__":
    create_crash_summary()
    monitor_and_auto_restart() 