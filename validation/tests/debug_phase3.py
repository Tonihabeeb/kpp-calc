#!/usr/bin/env python3
"""
Debug script to understand Phase 3 electrical system behavior
"""

import sys
import os
sys.path.append('.')

from simulation.components.integrated_electrical_system import create_standard_kmp_electrical_system

def debug_electrical_system():
    """Debug the electrical system to understand why power isn't being generated."""
    print("=== Phase 3 Electrical System Debug ===\n")
    
    # Create electrical system with very relaxed protection
    config = {
        'power_electronics': {
            'max_frequency_deviation': 50.0,  # Very relaxed
            'max_voltage_deviation': 0.5,     # Very relaxed
            'max_current': 5000.0,            # Very high limit
            'frequency_tolerance': 10.0,      # Very relaxed sync
            'sync_time_constant': 0.1         # Fast sync
        }
    }
    
    electrical_system = create_standard_kmp_electrical_system(config)
      # Test conditions close to rated
    torque = 13000.0  # N·m (closer to generator rated torque)
    speed = 39.27     # rad/s (375 RPM)
    dt = 0.1          # s
    
    print(f"Test input: {torque} N·m, {speed} rad/s")
    print(f"Expected mechanical power: {torque * speed / 1000:.1f} kW\n")
    
    # Run multiple updates to allow synchronization
    for i in range(50):  # 5 seconds
        result = electrical_system.update(torque, speed, dt)
        
        if i % 10 == 0:  # Print every second
            print(f"Step {i+1:2d}: "
                  f"Mech Power: {result['mechanical_power_input']/1000:6.1f} kW, "
                  f"Elec Power: {result['electrical_power_output']/1000:6.1f} kW, "
                  f"Grid Power: {result['grid_power_output']/1000:6.1f} kW, "
                  f"Efficiency: {result['system_efficiency']:5.3f}")
    
    print(f"\nFinal result details:")
    for key, value in result.items():
        if isinstance(value, (int, float)):
            if 'power' in key.lower() and value > 1000:
                print(f"  {key}: {value/1000:.1f} kW")
            elif 'efficiency' in key.lower() or 'factor' in key.lower():
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    # Check individual component states
    print(f"\n=== Component Debug ===")
    print(f"Generator state:")
    gen_state = electrical_system.generator_state
    for key, value in gen_state.items():
        if isinstance(value, (int, float)):
            if 'power' in key.lower() and value > 1000:
                print(f"  {key}: {value/1000:.1f} kW")
            else:
                print(f"  {key}: {value:.3f}")
    
    print(f"\nPower Electronics state:")
    pe_state = electrical_system.power_electronics_state
    for key, value in pe_state.items():
        if isinstance(value, (int, float)):
            if 'power' in key.lower() and value > 1000:
                print(f"  {key}: {value/1000:.1f} kW")
            else:
                print(f"  {key}: {value:.3f}")
    
    print(f"\nGrid state:")
    grid_state = electrical_system.grid_state
    for key, value in grid_state.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value:.3f}")

if __name__ == "__main__":
    debug_electrical_system()
