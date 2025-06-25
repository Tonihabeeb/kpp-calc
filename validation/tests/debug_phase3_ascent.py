"""
Debug script for Phase 3 floater ascent issue.
Analyzes why the floater isn't ascending in the integration test.
"""

from simulation.components.floater import Floater
from config.config import G, RHO_WATER

def debug_floater_ascent():
    """Debug the floater ascent dynamics."""
    print("=== Debugging Floater Ascent ===")
    
    # Create floater identical to test
    floater = Floater(
        volume=0.01,        # 10 liters
        mass=8.0,           # 8 kg (heavy when empty)
        area=0.1,
        position=0.0,       # Start at bottom
        tank_height=10.0
    )
    
    print(f"Initial floater state:")
    print(f"  Volume: {floater.volume*1000:.1f} L")
    print(f"  Mass: {floater.mass:.1f} kg")
    print(f"  Weight: {floater.mass * G:.1f} N")
    print(f"  Position: {floater.position:.2f} m")
    
    # Step 1: Set up for injection
    floater.update_pneumatic_state(0.0, bottom_station_pos=0.0)
    print(f"\nAfter position update:")
    print(f"  At bottom station: {floater.at_bottom_station}")
    print(f"  Ready for injection: {floater.ready_for_injection}")
    
    # Step 2: Start injection
    success = floater.start_pneumatic_injection(
        target_volume=0.007,    # 7 liters
        injection_pressure=300000.0,  # 3 bar
        current_time=0.0
    )
    print(f"\nAfter injection start:")
    print(f"  Injection started: {success}")
    print(f"  Fill state: {floater.pneumatic_fill_state}")
    print(f"  Target volume: {floater.target_air_volume*1000:.1f} L")
    print(f"  Injection pressure: {floater.pneumatic_pressure/1000:.1f} kPa")
    print(f"  Injection depth: {floater.injection_depth:.2f} m")
    
    # Step 3: Complete injection
    floater.update_pneumatic_injection(0.007, dt=1.0)
    print(f"\nAfter injection completion:")
    print(f"  Fill state: {floater.pneumatic_fill_state}")
    print(f"  Injection complete: {floater.injection_complete}")
    print(f"  Total air injected: {floater.total_air_injected*1000:.1f} L")
    print(f"  Air fill level: {floater.air_fill_level:.2f}")
    
    # Step 4: Analyze forces
    print(f"\n=== Force Analysis ===")
    
    # Weight forces
    air_mass = 1.225 * floater.total_air_injected  # Air density * volume
    total_weight = (floater.mass + air_mass) * G
    print(f"Floater weight: {floater.mass * G:.1f} N")
    print(f"Air weight: {air_mass * G:.1f} N")
    print(f"Total weight: {total_weight:.1f} N")
    
    # Buoyancy forces
    buoyancy_basic = floater.compute_buoyant_force()
    buoyancy_enhanced = floater.compute_enhanced_buoyant_force()
    print(f"Basic buoyancy: {buoyancy_basic:.1f} N")
    print(f"Enhanced buoyancy: {buoyancy_enhanced:.1f} N")
    
    # Net force
    drag = floater.compute_drag_force()  # Should be zero at rest
    net_force = floater.force
    print(f"Drag force: {drag:.1f} N")
    print(f"Net force: {net_force:.1f} N")
    
    print(f"\nForce balance:")
    print(f"  Buoyancy: {buoyancy_enhanced:.1f} N (up)")
    print(f"  Weight: {-total_weight:.1f} N (down)")
    print(f"  Net: {buoyancy_enhanced - total_weight:.1f} N")
    
    # Calculate required air volume for neutral buoyancy
    required_displaced_water = total_weight / (RHO_WATER * G)
    print(f"\nRequired displaced water volume for neutral buoyancy: {required_displaced_water*1000:.1f} L")
    print(f"Current air volume: {floater.total_air_injected*1000:.1f} L")
    print(f"Floater total volume: {floater.volume*1000:.1f} L")
    
    if buoyancy_enhanced > total_weight:
        print("\n✓ Floater should ascend!")
    else:
        print(f"\n✗ Floater will not ascend. Need {(total_weight - buoyancy_enhanced):.1f} N more buoyancy")
        additional_air = (total_weight - buoyancy_enhanced) / (RHO_WATER * G)
        print(f"  Need {additional_air*1000:.1f} L more displaced water volume")
    
    # Test a few update steps
    print(f"\n=== Simulation Steps ===")
    dt = 0.1
    for step in range(5):
        old_pos = floater.position
        old_vel = floater.velocity
        
        floater.update(dt)
        
        print(f"Step {step+1}: pos={floater.position:.4f} m, vel={floater.velocity:.4f} m/s, "
              f"Δpos={floater.position-old_pos:.4f} m")
        
        if floater.position > old_pos:
            print("  ✓ Ascending!")
            break
        elif floater.velocity > 0:
            print("  → Accelerating upward")
        else:
            print("  ✗ Not moving upward")

if __name__ == "__main__":
    debug_floater_ascent()
