"""
Debug the pulse jet force calculation that's causing the massive force.
"""

from simulation.components.floater import Floater
from config.config import G, RHO_WATER
import math

def debug_pulse_jet():
    print("=== Debugging Pulse Jet Force ===")
    
    # Create floater and set it up
    floater = Floater(
        volume=0.01,        # 10 liters
        mass=8.0,           # 8 kg
        area=0.1,
        position=0.0,
        tank_height=10.0
    )
    
    # Simulate injection completion
    floater.update_pneumatic_state(0.0, bottom_station_pos=0.0)
    floater.start_pneumatic_injection(0.007, 300000.0, 0.0)
    floater.update_pneumatic_injection(0.007, dt=1.0)
    
    print(f"Floater state after injection:")
    print(f"  Fill progress: {floater.fill_progress:.3f}")
    print(f"  Is filled: {floater.is_filled}")
    print(f"  Air pressure: {floater.air_pressure:.0f} Pa")
    print(f"  Air flow rate: {floater.air_flow_rate:.3f} m³/s")
    print(f"  Jet efficiency: {floater.jet_efficiency:.3f}")
    
    # Check pulse jet conditions
    print(f"\nPulse jet conditions:")
    print(f"  0 < fill_progress < 1.0? {0 < floater.fill_progress < 1.0}")
    print(f"  Fill progress = {floater.fill_progress}")
    
    # Calculate pulse jet force manually
    if 0 < floater.fill_progress < 1.0:
        v_jet = math.sqrt(2 * floater.air_pressure / RHO_WATER)
        water_displacement_rate = floater.air_flow_rate
        F_jet = floater.jet_efficiency * RHO_WATER * water_displacement_rate * v_jet
        
        print(f"\nPulse jet calculation:")
        print(f"  v_jet = sqrt(2 * {floater.air_pressure} / {RHO_WATER}) = {v_jet:.2f} m/s")
        print(f"  water_displacement_rate = {water_displacement_rate} m³/s")
        print(f"  F_jet = {floater.jet_efficiency} * {RHO_WATER} * {water_displacement_rate} * {v_jet} = {F_jet:.2f} N")
    else:
        print(f"\nNo pulse jet force (fill_progress not in range)")
    
    # Get the actual calculated force
    actual_jet_force = floater.compute_pulse_jet_force()
    print(f"\nActual pulse jet force: {actual_jet_force:.2f} N")
    
    # Check all forces
    print(f"\n=== All Forces ===")
    F_buoy = floater.compute_buoyant_force()
    F_jet = floater.compute_pulse_jet_force()
    air_mass = 1.225 * floater.volume * floater.fill_progress  # RHO_AIR * volume * fill_progress
    F_gravity = -(floater.mass + air_mass) * G
    F_drag = floater.compute_drag_force()
    F_net = F_buoy + F_gravity + F_drag + F_jet
    
    print(f"  Buoyancy: {F_buoy:.2f} N")
    print(f"  Jet: {F_jet:.2f} N")
    print(f"  Gravity: {F_gravity:.2f} N")
    print(f"  Drag: {F_drag:.2f} N")
    print(f"  Net: {F_net:.2f} N")
    
    # What should the air mass be?
    print(f"\n=== Air Mass Analysis ===")
    print(f"  Air volume * fill_progress: {floater.volume * floater.fill_progress:.6f} m³")
    print(f"  Air density: {1.225:.3f} kg/m³")
    print(f"  Calculated air mass: {air_mass:.6f} kg")
    print(f"  Total air injected: {floater.total_air_injected:.6f} m³")
    
    # The issue might be that we're using fill_progress (0.7) instead of actual air fraction
    # for the jet calculation when it should be 0 for completed injection

if __name__ == "__main__":
    debug_pulse_jet()
