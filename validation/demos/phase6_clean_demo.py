#!/usr/bin/env python3
"""
Phase 6 Clean Demo: Pneumatic Control System Integration
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.pneumatics.pneumatic_coordinator import (
    create_standard_kpp_pneumatic_coordinator,
)


def run_phase6_clean_demo():
    """Run the clean Phase 6 demonstration."""
    print("=" * 60)
    print("PHASE 6 CLEAN DEMO: Pneumatic Control Integration")
    print("=" * 60)

    print("\n1. Creating KPP pneumatic control coordinator...")
    coordinator = create_standard_kpp_pneumatic_coordinator(
        enable_thermodynamics=True, enable_optimization=True
    )

    print(
        f"   ✓ Target pressure: {coordinator.control_params.target_pressure/100000:.1f} bar"
    )
    print(f"   ✓ Thermodynamics enabled: {coordinator.enable_thermodynamics}")
    print(
        f"   ✓ Power optimization: {coordinator.control_params.power_optimization_enabled}"
    )

    print("\n2. Starting control loop...")
    coordinator.start_control_loop()
    time.sleep(0.3)
    print("   ✓ Control loop started and running")

    print("\n3. Checking system status...")
    status = coordinator.get_system_status()
    print(f"   ✓ Current state: {status['state']}")
    print(
        f"   ✓ Tank pressure: {coordinator.sensors.tank_pressure.value/100000:.2f} bar"
    )
    print(f"   ✓ Active faults: {len(status['faults'])}")

    print("\n4. Testing thermal efficiency calculation...")
    if coordinator.enable_thermodynamics:
        efficiency = coordinator.calculate_thermal_efficiency(
            coordinator.sensors.compressor_temp.value,
            coordinator.sensors.water_temp.value,
        )
        print(f"   ✓ Thermal efficiency: {efficiency:.4f}")

    print("\n5. Testing optimal pressure calculation...")
    if coordinator.enable_thermodynamics:
        optimal_p = coordinator.calculate_optimal_pressure(
            coordinator.sensors.compressor_temp.value,
            coordinator.sensors.water_temp.value,
        )
        print(f"   ✓ Optimal pressure: {optimal_p/100000:.2f} bar")

    print("\n6. Testing control algorithms...")
    coordinator.pressure_control_algorithm()
    coordinator.injection_control_algorithm()
    coordinator.thermal_control_algorithm()
    coordinator.performance_optimization_algorithm()
    print("   ✓ All control algorithms executed successfully")

    print("\n7. Testing injection parameters...")
    injection_params = coordinator.calculate_injection_parameters()
    print(f"   ✓ Injection duration: {injection_params['duration']:.2f} s")
    print(f"   ✓ Injection pressure: {injection_params['pressure']/100000:.2f} bar")

    print("\n8. Testing emergency stop...")
    coordinator.emergency_stop()
    final_status = coordinator.get_system_status()
    print(f"   ✓ State after emergency stop: {final_status['state']}")

    print("\n9. System reset...")
    coordinator.reset_system()
    coordinator.stop_control_loop()
    print("   ✓ System reset and control loop stopped")

    print("\n" + "=" * 60)
    print("PHASE 6 CLEAN DEMO COMPLETE")
    print("✓ Control coordinator fully operational")
    print("✓ PLC-style control algorithms working")
    print("✓ Thermodynamic integration active")
    print("✓ Emergency procedures functional")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_phase6_clean_demo()
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback

        traceback.print_exc()
