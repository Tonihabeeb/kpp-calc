#!/usr/bin/env python3
"""
Debug script to understand why the compressor isn't starting.
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

def debug_control_logic():
    """Debug the control logic step by step."""
    print("=== Debugging Pneumatic Control Logic ===")
    
    # Create systems
    air_system = create_standard_kpp_compressor()
    control_system = create_standard_kpp_pressure_controller(2.5)  # 2.5 bar target
    control_system.set_air_compressor(air_system)
    
    print(f"Initial tank pressure: {air_system.tank_pressure:.0f} Pa ({air_system.tank_pressure/100000:.2f} bar)")
    
    # Check control settings
    settings = control_system.settings
    print(f"Target pressure: {settings.target_pressure:.0f} Pa ({settings.target_pressure/100000:.2f} bar)")
    print(f"Low setpoint: {settings.low_pressure_setpoint:.0f} Pa ({settings.low_pressure_setpoint/100000:.2f} bar)")
    print(f"High setpoint: {settings.high_pressure_setpoint:.0f} Pa ({settings.high_pressure_setpoint/100000:.2f} bar)")
      # Check if compressor should start
    current_time = 0.0
    current_pressure = air_system.tank_pressure
    
    print(f"\nChecking if compressor should start:")
    print(f"Current pressure: {current_pressure:.0f} Pa")
    print(f"Low setpoint: {settings.low_pressure_setpoint:.0f} Pa")
    print(f"Pressure below setpoint? {current_pressure < settings.low_pressure_setpoint}")
    
    # Check each condition manually
    print(f"Safety level check: {control_system.safety_level}")
    print(f"Min cycle time: {settings.min_cycle_time}s")
    print(f"Time since last stop: {current_time - control_system.last_stop_time}s")
    print(f"Emergency stop active: {control_system.emergency_stop_active}")
    print(f"Manual override: {control_system.manual_override}")
    
    should_start = control_system.should_start_compressor(current_pressure, current_time)
    print(f"Should start compressor? {should_start}")
    
    # Check safety level
    safety_level = control_system.check_safety_conditions(current_pressure)
    print(f"Safety level: {safety_level}")
    print(f"Safety warnings: {control_system.safety_warnings}")
      # Run a few control steps
    print(f"\n=== Running Control Steps ===")
    dt = 1.0
    for i in range(10):  # Run more steps to see progress
        print(f"\n--- Step {i+1} ---")
        results = control_system.control_step(dt, current_time)
        current_time += dt
        
        print(f"Compressor state: {results['compressor_state']}")
        print(f"Tank pressure: {results['tank_pressure']:.0f} Pa ({results['tank_pressure']/100000:.2f} bar)")
        print(f"Safety level: {results['safety_level']}")
        
        compressor_results = results['compressor_results']
        print(f"Compressor running: {compressor_results.get('running', False)}")
        if compressor_results.get('running', False):
            print(f"  Power consumed: {compressor_results.get('power_consumed', 0):.0f} W")
            print(f"  Air compressed: {compressor_results.get('air_compressed', 0)*1000:.1f} L")
            print(f"  Flow rate: {compressor_results.get('flow_rate', 0)*1000:.1f} L/s")
        
        if results['compressor_state'] == 'running' and compressor_results.get('running', False):
            print("✓ Compressor is running and producing air!")
            break
    else:
        print("✗ Compressor never reached full running state")
    
    print(f"\n=== System Status ===")
    air_status = air_system.get_system_status()
    control_status = control_system.get_control_status()
    
    print(f"Air system: {air_status}")
    print(f"Control system: {control_status}")

if __name__ == "__main__":
    debug_control_logic()
