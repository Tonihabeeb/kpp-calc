"""
Phase 3 Demonstration: Enhanced Buoyancy and Ascent Dynamics

This script demonstrates the new Phase 3 features:
- Pressure expansion physics during ascent
- Enhanced buoyancy calculations with depth effects
- Gas dissolution and release modeling
- Integration with pneumatic injection system
"""

import time

from config.config import RHO_WATER, G
from simulation.components.floater import Floater
from simulation.pneumatics.pressure_expansion import PressureExpansionPhysics


def demonstrate_phase3_features():
    """Demonstrate Phase 3 enhanced buoyancy physics."""
    print("=" * 60)
    print("PHASE 3 DEMONSTRATION: Enhanced Buoyancy and Ascent Dynamics")
    print("=" * 60)

    # Create a floater with realistic parameters
    floater = Floater(
        volume=0.012,  # 12 liters total volume
        mass=6.0,  # 6 kg (lighter floater)
        area=0.08,  # 0.08 m² cross-sectional area
        position=0.0,  # Start at bottom
        tank_height=10.0,  # 10m tank
        expansion_mode="mixed",  # Use mixed expansion model
    )

    print(f"\n1. FLOATER INITIALIZATION")
    print(f"   Total Volume: {floater.volume*1000:.1f} L")
    print(f"   Mass: {floater.mass:.1f} kg")
    print(f"   Weight: {floater.mass * G:.1f} N")
    print(f"   Tank Height: {floater.tank_height:.1f} m")
    print(f"   Expansion Mode: {floater.expansion_mode}")

    # Position at injection station
    floater.update_pneumatic_state(0.0, bottom_station_pos=0.0)

    print(f"\n2. PNEUMATIC INJECTION")
    print(f"   Ready for injection: {floater.ready_for_injection}")

    # Start injection with sufficient air for buoyancy
    target_air = 0.009  # 9 liters - should provide buoyancy
    injection_pressure = 250000.0  # 2.5 bar

    success = floater.start_pneumatic_injection(
        target_volume=target_air,
        injection_pressure=injection_pressure,
        current_time=0.0,
    )

    if success:
        print(
            f"   ✓ Injection started: {target_air*1000:.1f}L at {injection_pressure/1000:.1f} kPa"
        )
        print(f"   Injection depth: {floater.injection_depth:.2f} m")
        print(f"   Initial pressure: {floater.initial_air_pressure/1000:.1f} kPa")

    # Complete injection
    floater.update_pneumatic_injection(target_air, dt=1.0)

    print(f"   ✓ Injection complete: {floater.total_air_injected*1000:.1f}L injected")
    print(f"   Air fill level: {floater.air_fill_level*100:.1f}%")

    # Calculate initial forces
    print(f"\n3. FORCE ANALYSIS AT INJECTION DEPTH")
    basic_buoyancy = RHO_WATER * G * floater.total_air_injected
    enhanced_buoyancy = floater.compute_enhanced_buoyant_force()
    total_weight = floater.mass * G
    net_force = enhanced_buoyancy - total_weight

    print(f"   Basic buoyancy (no expansion): {basic_buoyancy:.1f} N")
    print(f"   Enhanced buoyancy: {enhanced_buoyancy:.1f} N")
    print(f"   Total weight: {total_weight:.1f} N")
    print(f"   Net force: {net_force:.1f} N")

    if net_force > 0:
        print(f"   ✓ Floater will ascend!")
    else:
        print(f"   ✗ Floater needs {-net_force:.1f} N more buoyancy")

    # Simulate ascent with expansion effects
    print(f"\n4. ASCENT SIMULATION WITH EXPANSION PHYSICS")
    print(
        f"   {'Time':<6} {'Pos':<8} {'Depth':<8} {'Press':<8} {'AirVol':<8} {'Buoy':<8} {'ExpRatio':<8}"
    )
    print(
        f"   {'(s)':<6} {'(m)':<8} {'(m)':<8} {'(bar)':<8} {'(L)':<8} {'(N)':<8} {'(-)':<8}"
    )
    print(f"   {'-'*64}")

    dt = 0.2  # 0.2 second time steps
    simulation_time = 0.0

    for step in range(50):  # 10 seconds of simulation
        position = floater.position

        # Calculate physics parameters
        depth = floater.pressure_physics.get_depth_from_position(
            position, floater.tank_height
        )
        current_pressure = floater.pressure_physics.get_pressure_at_depth(depth)

        # Get enhanced buoyancy with expansion
        buoyancy = floater.compute_enhanced_buoyant_force()

        # Get expansion state
        expansion_ratio = floater.expansion_state.get("expansion_ratio", 1.0)
        expanded_volume = floater.expansion_state.get(
            "expanded_volume", floater.total_air_injected
        )

        # Print status every few steps
        if step % 5 == 0:
            print(
                f"   {simulation_time:<6.1f} {position:<8.2f} {depth:<8.2f} {current_pressure/100000:<8.2f} "
                f"{expanded_volume*1000:<8.1f} {buoyancy:<8.1f} {expansion_ratio:<8.3f}"
            )

        # Update floater dynamics
        floater.update(dt)
        simulation_time += dt

        # Stop if floater reaches near top
        if position >= 9.5:
            print(
                f"   {simulation_time:<6.1f} {floater.position:<8.2f} {depth:<8.2f} {current_pressure/100000:<8.2f} "
                f"{expanded_volume*1000:<8.1f} {buoyancy:<8.1f} {expansion_ratio:<8.3f}"
            )
            print(f"   ✓ Floater reached top in {simulation_time:.1f} seconds!")
            break

    # Final state analysis
    print(f"\n5. FINAL STATE ANALYSIS")
    final_depth = floater.pressure_physics.get_depth_from_position(
        floater.position, floater.tank_height
    )
    final_pressure = floater.pressure_physics.get_pressure_at_depth(final_depth)
    final_buoyancy = floater.compute_enhanced_buoyant_force()

    print(f"   Final position: {floater.position:.2f} m")
    print(f"   Final depth: {final_depth:.2f} m")
    print(f"   Final pressure: {final_pressure/1000:.1f} kPa")
    print(f"   Final buoyancy: {final_buoyancy:.1f} N")

    if len(floater.expansion_state) > 0:
        initial_vol = floater.expansion_state.get("initial_volume", 0)
        final_vol = floater.expansion_state.get("expanded_volume", 0)
        expansion_ratio = floater.expansion_state.get("expansion_ratio", 1)

        print(f"   Air volume change: {initial_vol*1000:.1f}L → {final_vol*1000:.1f}L")
        print(f"   Expansion ratio: {expansion_ratio:.3f}")
        print(f"   Volume gain: {(final_vol-initial_vol)*1000:.1f}L")

    # Dissolution effects
    print(
        f"   Dissolved air fraction: {floater.dissolved_air_fraction_enhanced*100:.2f}%"
    )

    print(f"\n6. PHASE 3 FEATURES DEMONSTRATED")
    print(f"   ✓ Pressure expansion physics (isothermal/adiabatic/mixed)")
    print(f"   ✓ Depth-dependent pressure calculations")
    print(f"   ✓ Enhanced buoyancy with air expansion effects")
    print(f"   ✓ Gas dissolution modeling (Henry's Law)")
    print(f"   ✓ Integration with pneumatic injection system")
    print(f"   ✓ Realistic ascent velocity control")

    print(f"\n" + "=" * 60)
    print("PHASE 3 DEMONSTRATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_phase3_features()
