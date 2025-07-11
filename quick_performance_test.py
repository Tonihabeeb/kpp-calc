#!/usr/bin/env python3
"""
Quick performance test to verify optimizations
"""

import time
import requests
import json

def test_performance():
    """Test current performance"""
    print("Testing Performance After Optimizations...")
    
    try:
        # Test API endpoint
        response = requests.get('http://127.0.0.1:5000/api/performance', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response Received")
            
            # Check simulation performance
            sim_perf = data.get('simulation_performance', {})
            if sim_perf.get('status') == 'active':
                current_perf = sim_perf.get('current_performance', {})
                print(f"📊 Current Performance:")
                print(f"   - Average Step Time: {current_perf.get('avg_step_time_ms', 0):.1f}ms")
                print(f"   - Target FPS: {current_perf.get('target_fps', 0)}Hz")
                print(f"   - Actual FPS: {current_perf.get('actual_fps', 0):.1f}Hz")
                
                # Check if performance improved
                step_time = current_perf.get('avg_step_time_ms', 0)
                if step_time < 50:
                    print("✅ Performance is good (<50ms step time)")
                elif step_time < 100:
                    print("⚠️ Performance is acceptable (<100ms step time)")
                else:
                    print("❌ Performance needs improvement (>100ms step time)")
            else:
                print(f"ℹ️ Simulation status: {sim_perf.get('status', 'unknown')}")
            
            # Check system metrics
            sys_metrics = data.get('system_metrics', {})
            print(f"💻 System Metrics:")
            print(f"   - CPU Usage: {sys_metrics.get('cpu_percent', 0):.1f}%")
            print(f"   - Memory Usage: {sys_metrics.get('memory_percent', 0):.1f}%")
            
        else:
            print(f"❌ API returned status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print("\n🎯 Performance Test Complete!")

if __name__ == "__main__":
    test_performance() 