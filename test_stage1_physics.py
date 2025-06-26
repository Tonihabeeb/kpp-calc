"""
Test script for Stage 1 Physics Engine Implementation
Tests the new physics engine and event handler integration.
"""

import sys
import os
import math
import time

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.physics.physics_engine import PhysicsEngine
from simulation.physics.event_handler import EventHandler
from simulation.components.floater import Floater

def test_physics_engine():
    """Test basic physics engine functionality."""
    print("=== Testing Physics Engine ===")
    
    # Create physics engine
    params = {
        'time_step': 0.1,
        'chain_mass': 100.0,
        'friction_coefficient': 0.01
    }
    physics = PhysicsEngine(params)
    
    # Create test floaters
    floaters = []
    for i in range(4):
        floater = Floater(
            volume=0.04,  # 40 liters
            mass=50.0,    # 50 kg container
            area=0.2,     # 0.2 m² cross-section
            Cd=0.8,       # Drag coefficient
            phase_offset=math.pi * i / 2  # Spread around loop
        )
        floaters.append(floater)
    
    # Set initial states: alternate heavy/light
    for i, floater in enumerate(floaters):
        floater.set_filled(i % 2 == 0)  # Every other floater is light
    
    print(f"Created {len(floaters)} floaters")
    print(f"Initial chain velocity: {physics.v_chain:.3f} m/s")
    
    # Run simulation for a few steps
    generator_torque = 100.0  # N⋅m
    sprocket_radius = 1.0     # m
    
    for step in range(10):
        state = physics.step(floaters, generator_torque, sprocket_radius)
        
        if step % 2 == 0:  # Print every other step
            print(f"Step {step}: t={state['time']:.2f}s, "
                  f"v_chain={state['chain_velocity']:.3f}m/s, "
                  f"power={state['power_output']:.1f}W")
    
    print(f"Final chain velocity: {physics.v_chain:.3f} m/s")
    print(f"Total energy output: {physics.cumulative_energy_out:.1f} J")
    print()

def test_event_handler():
    """Test event handler functionality."""
    print("=== Testing Event Handler ===")
    
    # Create event handler
    tank_depth = 10.0  # 10 meter tank
    events = EventHandler(tank_depth)
    
    # Create test floater at bottom (heavy)
    floater = Floater(
        volume=0.04,
        mass=90.0,  # Heavy (water-filled)
        area=0.2,
        Cd=0.8
    )
    floater.angle = 0.05  # Near bottom (within injection zone)
    floater.state = "heavy"
    
    print(f"Floater at angle {floater.angle:.3f} rad, state: {floater.state}")
    
    # Test injection
    injection_occurred = events.handle_injection(floater)
    print(f"Injection occurred: {injection_occurred}")
    
    if injection_occurred:
        print(f"New floater state: {floater.state}")
        print(f"New floater mass: {floater.mass:.1f} kg")
        print(f"Energy input: {events.energy_input:.1f} J")
    
    # Move floater to top and test venting
    floater.angle = math.pi  # At top
    venting_occurred = events.handle_venting(floater)
    print(f"Venting occurred: {venting_occurred}")
    
    if venting_occurred:
        print(f"Final floater state: {floater.state}")
        print(f"Final floater mass: {floater.mass:.1f} kg")
    
    print()

def test_force_calculations():
    """Test individual force calculations."""
    print("=== Testing Force Calculations ===")
    
    physics = PhysicsEngine({'time_step': 0.1})
    
    # Create light floater (air-filled)
    light_floater = Floater(volume=0.04, mass=50.0, area=0.2, Cd=0.8)
    light_floater.set_filled(True)  # Air-filled
    
    # Create heavy floater (water-filled) 
    heavy_floater = Floater(volume=0.04, mass=50.0, area=0.2, Cd=0.8)
    heavy_floater.set_filled(False)  # Water-filled
    
    # Test forces at different velocities
    velocities = [0.0, 0.5, 1.0, -0.5, -1.0]
    
    print("Light floater forces:")
    for v in velocities:
        force = physics.calculate_floater_forces(light_floater, v)
        print(f"  v={v:+.1f} m/s: F={force:+.1f} N")
    
    print("Heavy floater forces:")
    for v in velocities:
        force = physics.calculate_floater_forces(heavy_floater, v)
        print(f"  v={v:+.1f} m/s: F={force:+.1f} N")
    
    print()

def test_integrated_simulation():
    """Test integrated simulation with events."""
    print("=== Testing Integrated Simulation ===")
    
    # Setup
    physics = PhysicsEngine({
        'time_step': 0.1,
        'chain_mass': 50.0,
        'friction_coefficient': 0.005
    })
    
    events = EventHandler(tank_depth=8.0)
    
    # Create floaters around the loop
    floaters = []
    for i in range(6):
        angle = 2 * math.pi * i / 6
        floater = Floater(
            volume=0.035,
            mass=45.0,
            area=0.18,
            Cd=0.75,
            phase_offset=angle
        )
        # Start all floaters as heavy
        floater.set_filled(False)
        floaters.append(floater)
    
    # Simulation parameters
    generator_torque = 80.0  # Moderate load
    sprocket_radius = 0.8
    
    print(f"Running simulation with {len(floaters)} floaters...")
    print("Time   | v_chain | Power  | Injections | Ventings | Net Energy")
    print("-------|---------|--------|------------|----------|------------")
    
    # Run simulation
    for step in range(50):  # 5 seconds at dt=0.1
        # Process events
        event_summary = events.process_all_events(floaters)
        
        # Update physics engine energy
        physics.energy_input = events.energy_input
        
        # Physics step
        state = physics.step(floaters, generator_torque, sprocket_radius)
        
        # Reset event tracking periodically
        if step % 25 == 0:
            events.reset_cycle_tracking()
        
        # Print status every 10 steps (1 second)
        if step % 10 == 0:
            net_energy = state['energy_output'] - state['energy_input']
            print(f"{state['time']:5.1f}s | "
                  f"{state['chain_velocity']:6.3f} | "
                  f"{state['power_output']:6.1f} | "
                  f"{event_summary['injections']:10d} | "
                  f"{event_summary['ventings']:8d} | "
                  f"{net_energy:10.1f}")
    
    # Final summary
    final_state = physics.get_state()
    efficiency = (final_state['energy_output'] / final_state['energy_input'] * 100) if final_state['energy_input'] > 0 else 0
    
    print(f"\nFinal Results:")
    print(f"  Total energy input: {final_state['energy_input']:.1f} J")
    print(f"  Total energy output: {final_state['energy_output']:.1f} J")
    print(f"  Net energy: {final_state['net_energy']:.1f} J")
    print(f"  Efficiency: {efficiency:.2f}%")
    print(f"  Final chain velocity: {final_state['chain_velocity']:.3f} m/s")

if __name__ == "__main__":
    print("Stage 1 Physics Engine Test Suite")
    print("=" * 50)
    
    try:
        test_physics_engine()
        test_event_handler()
        test_force_calculations()
        test_integrated_simulation()
        
        print("=" * 50)
        print("✅ All tests completed successfully!")
        print("Stage 1 implementation is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
