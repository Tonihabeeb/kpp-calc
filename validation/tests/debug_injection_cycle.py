#!/usr/bin/env python3
"""
Debug script for the coordinated injection cycle.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.pneumatics import (
    create_standard_kpp_compressor,
    create_standard_kpp_pressure_controller,
    create_standard_kpp_injection_controller,
    FloaterInjectionRequest
)
from simulation.components.floater import Floater

def debug_coordinated_injection():
    """Debug the coordinated injection cycle."""
    print("=== Debugging Coordinated Injection Cycle ===")
    
    # Create integrated pneumatic system
    air_system = create_standard_kpp_compressor()
    pressure_controller = create_standard_kpp_pressure_controller(2.5)
    injection_controller = create_standard_kpp_injection_controller()
    
    # Connect components
    pressure_controller.set_air_compressor(air_system)
    
    # Build up pressure first
    print("Building up system pressure...")
    dt = 1.0
    current_time = 0.0
    
    for i in range(60):
        pressure_controller.control_step(dt, current_time)
        current_time += dt
        
        if i % 10 == 0:
            print(f"Step {i}: pressure={air_system.tank_pressure/1000:.1f} kPa")
        
        if air_system.tank_pressure >= 250000.0:  # 2.5 bar
            print(f"✓ Adequate pressure reached at step {i}: {air_system.tank_pressure/1000:.1f} kPa")
            break
    
    # Create floater and injection request
    floater = Floater(volume=0.1, mass=10.0, area=0.5, position=0.0)
    floater.update_pneumatic_state(0.0, 0.0, 10.0, 0.1)  # At bottom station
    
    print(f"Floater ready for injection: {floater.ready_for_injection}")
    
    request = FloaterInjectionRequest(
        floater_id="test_floater",
        depth=5.0,
        target_volume=0.05,  # 50L
        position=0.0,
        timestamp=0.0
    )
    
    # Add injection request
    success = injection_controller.add_injection_request(request)
    print(f"Injection request added: {success}")
    print(f"Queue length: {len(injection_controller.injection_queue)}")
    print(f"Required pressure: {request.injection_pressure/1000:.1f} kPa")
    print(f"Supply pressure: {air_system.tank_pressure/1000:.1f} kPa")
    print(f"Can supply pressure: {injection_controller.can_supply_injection_pressure(air_system.tank_pressure, request.injection_pressure)}")
    
    # Simulate coordinated operation
    dt = 0.1
    current_time = 60.0  # Continue from pressure buildup
    
    print(f"\n=== Starting Injection Simulation ===")
    
    for i in range(100):  # 10 seconds maximum
        # Update pressure control
        pressure_results = pressure_controller.control_step(dt, current_time)
        
        # Update injection control
        injection_results = injection_controller.injection_step(
            dt, current_time, air_system.tank_pressure)
        
        # Print status every 10 steps
        if i % 10 == 0:
            print(f"Step {i}: valve_state={injection_results['valve_state']}, "
                  f"active_injection={injection_results['active_injection']}, "
                  f"flow_rate={injection_results['current_flow_rate']*1000:.1f} L/s, "
                  f"floater_state={floater.pneumatic_fill_state}")        # Update floater if injection is active
        if injection_results['active_injection'] == "test_floater":
            # Start floater injection if not already started
            if floater.pneumatic_fill_state == 'empty':
                floater.start_pneumatic_injection(
                    request.target_volume, 
                    request.injection_pressure, 
                    current_time
                )
            
            air_consumed = injection_results['air_consumed']
            floater.update_pneumatic_injection(air_consumed, dt)
            
            # Consume air from tank
            if air_consumed > 0:
                air_system.consume_air_from_tank(air_consumed)
        elif floater.pneumatic_fill_state == 'filling':
            # Injection controller finished, complete floater injection
            floater.complete_pneumatic_injection()
        
        current_time += dt
        
        # Check if injection completed
        if floater.injection_complete:
            print(f"✓ Injection completed at step {i}!")
            print(f"Final air injected: {floater.total_air_injected*1000:.1f}L")
            break
    else:
        print("✗ Injection did not complete within time limit")
        print(f"Floater state: {floater.pneumatic_fill_state}")
        print(f"Air injected: {floater.total_air_injected*1000:.1f}L of {floater.target_air_volume*1000:.1f}L")
        print(f"Injection controller status: {injection_controller.get_injection_status()}")

if __name__ == "__main__":
    debug_coordinated_injection()
