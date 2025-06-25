#!/usr/bin/env python3
"""
Debug script for Phase 3 electrical system synchronization issues
"""

import sys
import os
sys.path.append('.')

from simulation.components.integrated_electrical_system import create_standard_kmp_electrical_system

def debug_synchronization():
    """Debug why the electrical system won't synchronize."""
    print("=== Phase 3 Synchronization Debug ===\n")
    
    # Create electrical system with very relaxed protection
    config = {
        'power_electronics': {
            'max_frequency_deviation': 50.0,   # Very relaxed
            'max_voltage_deviation': 0.5,      # Very relaxed
            'max_current': 10000.0,            # Very high limit
            'frequency_tolerance': 20.0,       # Very relaxed sync
            'sync_time_constant': 0.1          # Very fast sync
        }
    }
    
    electrical_system = create_standard_kmp_electrical_system(config)
    
    # Test with steady conditions near rated
    torque = 8000.0  # N·m (about 60% of rated)
    speed = 39.27    # rad/s (rated speed)
    dt = 0.1         # s
    
    print(f"Test conditions: {torque} N·m, {speed} rad/s")
    print(f"Expected mechanical power: {torque * speed / 1000:.1f} kW\n")
    
    # Run steady state for synchronization
    for i in range(50):  # 5 seconds
        result = electrical_system.update(torque, speed, dt)
        
        if i % 5 == 0:  # Print every 0.5 seconds
            pe_state = electrical_system.power_electronics_state
            grid_state = electrical_system.grid_state
            
            print(f"Step {i+1:2d}: "
                  f"Grid Power: {result['grid_power_output']/1000:6.1f} kW, "
                  f"Sync: {pe_state.get('sync_progress', 0):5.3f}, "
                  f"Synchronized: {pe_state.get('is_synchronized', False)}, "
                  f"Protection: {pe_state.get('protection_active', True)}")
            
            if pe_state.get('protection_active', True):
                print(f"       Protection faults: {pe_state.get('fault_count', 'N/A')}")
    
    # Final detailed state
    print(f"\n=== Final Component States ===")
    print(f"Generator:")
    gen_state = electrical_system.generator_state
    for key in ['electrical_power', 'efficiency', 'frequency', 'voltage']:
        print(f"  {key}: {gen_state.get(key, 'N/A')}")
    
    print(f"\nPower Electronics:")
    pe_state = electrical_system.power_electronics_state
    for key in ['input_power', 'output_power', 'is_synchronized', 'sync_progress', 'protection_active', 'fault_count']:
        print(f"  {key}: {pe_state.get(key, 'N/A')}")
    
    print(f"\nGrid Interface:")
    grid_state = electrical_system.grid_state
    for key in ['voltage', 'frequency', 'is_connected']:
        print(f"  {key}: {grid_state.get(key, 'N/A')}")

if __name__ == "__main__":
    debug_synchronization()
