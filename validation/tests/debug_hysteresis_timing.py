#!/usr/bin/env python3
"""
Debug script to understand how long it takes to reach high pressure setpoint.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.pneumatics import (
    create_standard_kpp_compressor,
    create_standard_kpp_pressure_controller,
    CompressorState,
    SafetyLevel
)

def debug_hysteresis_timing():
    """Debug the hysteresis timing issue."""
    print("=== Debugging Hysteresis Timing ===")
    
    # Create systems exactly like the test
    air_system = create_standard_kpp_compressor()
    control_system = create_standard_kpp_pressure_controller(2.5)  # 2.5 bar target
    control_system.set_air_compressor(air_system)
      # Set starting conditions like the test
    dt = 0.1
    current_time = 0.0
    start_pressure = control_system.settings.low_pressure_setpoint - 5000.0
    air_system.set_tank_pressure(start_pressure)  # Use proper method
    
    print(f"Starting pressure: {start_pressure:.0f} Pa ({start_pressure/100000:.2f} bar)")
    print(f"Low setpoint: {control_system.settings.low_pressure_setpoint:.0f} Pa ({control_system.settings.low_pressure_setpoint/100000:.2f} bar)")
    print(f"High setpoint: {control_system.settings.high_pressure_setpoint:.0f} Pa ({control_system.settings.high_pressure_setpoint/100000:.2f} bar)")
    print(f"Target pressure: {control_system.settings.target_pressure:.0f} Pa ({control_system.settings.target_pressure/100000:.2f} bar)")
    
    # Run until compressor starts
    print(f"\n=== Waiting for compressor to start ===")
    for i in range(10):
        results = control_system.control_step(dt, current_time)
        current_time += dt
        print(f"Step {i+1}: state={results['compressor_state']}, pressure={results['tank_pressure']:.0f} Pa")
        if results['compressor_state'] in ['starting', 'running']:
            print(f"✓ Compressor started at step {i+1}")
            break
    else:
        print("✗ Compressor never started")
        return
    
    # Run until high setpoint reached
    print(f"\n=== Running until high setpoint reached ===")
    target_pressure = control_system.settings.high_pressure_setpoint
    
    for i in range(200):  # Run longer to see if it reaches target
        results = control_system.control_step(dt, current_time)
        current_time += dt
        
        current_pressure = results['tank_pressure']
        
        # Print progress every 20 steps (2 seconds)
        if i % 20 == 0:
            print(f"Step {i}: pressure={current_pressure:.0f} Pa ({current_pressure/100000:.2f} bar), "
                  f"state={results['compressor_state']}, "
                  f"progress={100*current_pressure/target_pressure:.1f}%")
        
        if current_pressure >= target_pressure:
            print(f"✓ High setpoint reached at step {i}! ({current_time:.1f}s)")
            print(f"  Final pressure: {current_pressure:.0f} Pa ({current_pressure/100000:.2f} bar)")
            return
    
    print(f"✗ High setpoint not reached after {200*dt:.1f} seconds")
    print(f"  Final pressure: {results['tank_pressure']:.0f} Pa ({results['tank_pressure']/100000:.2f} bar)")
    print(f"  Target pressure: {target_pressure:.0f} Pa ({target_pressure/100000:.2f} bar)")
    print(f"  Progress: {100*results['tank_pressure']/target_pressure:.1f}%")

if __name__ == "__main__":
    debug_hysteresis_timing()
