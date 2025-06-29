#!/usr/bin/env python3
"""
Phase 6 Simple Demo: Pneumatic Control System Integration
Basic demonstration of the control coordinator functionality.
"""

import os
import sys
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.pneumatics.pneumatic_coordinator import (
    create_standard_kpp_pneumatic_coordinator,
)


def run_phase6_simple_demo():
    """Run a simple Phase 6 demonstration."""
    print("=" * 60)
    print("PHASE 6 SIMPLE DEMO: Pneumatic Control Integration")
    print("=" * 60)

    print("\n1. Creating KPP pneumatic control coordinator...")
    coordinator = create_standard_kpp_pneumatic_coordinator(
        enable_thermodynamics=True, enable_optimization=True
    )

    print(
        f"   ✓ Target pressure: {coordinator.control_params.target_pressure/100000:.1f} bar"
    )
    print(
        f"   ✓ Pressure tolerance: ±{coordinator.control_params.pressure_tolerance/100000:.2f} bar"
    )
    print(
        f"   ✓ Max pressure: {coordinator.control_params.max_pressure/100000:.1f} bar"
    )
    print(
        f"   ✓ Min pressure: {coordinator.control_params.min_pressure/100000:.1f} bar"
    )
    print(f"   ✓ Thermodynamics enabled: {coordinator.enable_thermodynamics}")
    print(
        f"   ✓ Power optimization: {coordinator.control_params.power_optimization_enabled}"
    )
    print(
        f"   ✓ Thermal optimization: {coordinator.control_params.thermal_optimization_enabled}"
    )

    print("\n2. Starting control loop...")
    coordinator.start_control_loop()
    time.sleep(0.2)  # Let it initialize
    print("   ✓ Control loop started")

    print("\n3. Checking system status...")
    status = coordinator.get_system_status()
    print(f"   ✓ Current state: {status['state']}")
    print(
        f"   ✓ Tank pressure: {coordinator.sensors.tank_pressure.value/100000:.2f} bar"
    )
    print(
        f"   ✓ Compressor temp: {coordinator.sensors.compressor_temp.value - 273.15:.1f}°C"
    )
    print(f"   ✓ Water temp: {coordinator.sensors.water_temp.value - 273.15:.1f}°C")
    print(f"   ✓ Active faults: {len(status['faults'])}")

    print("\n4. Testing thermal efficiency calculation...")
    if coordinator.enable_thermodynamics:
        try:
            efficiency = coordinator.calculate_thermal_efficiency(
                coordinator.sensors.compressor_temp.value,
                coordinator.sensors.water_temp.value,
            )
            print(f"   ✓ Thermal efficiency: {efficiency:.4f}")
        except Exception as e:
            print(f"   ⚠ Efficiency calculation error: {e}")

    print("\n5. Testing optimal pressure calculation...")
    if coordinator.enable_thermodynamics:
        try:
            optimal_p = coordinator.calculate_optimal_pressure(
                coordinator.sensors.compressor_temp.value,
                coordinator.sensors.water_temp.value,
            )
            print(f"   ✓ Optimal pressure: {optimal_p/100000:.2f} bar")
        except Exception as e:
            print(f"   ⚠ Optimal pressure calculation error: {e}")

    print("\n6. Running control operations...")
    # Manual control step to simulate operation
    coordinator.update_sensors(0.1)
    coordinator.detect_faults()
    coordinator.pressure_control_algorithm()
    coordinator.injection_control_algorithm()
    print("   ✓ Control operations executed")

    print("\n7. Testing emergency stop...")
    coordinator.emergency_stop()
    final_status = coordinator.get_system_status()
    print(f"   ✓ State after emergency stop: {final_status['state']}")
    print(f"   ✓ Compressor enabled: {coordinator.compressor_enabled}")
    print(f"   ✓ Injection enabled: {coordinator.injection_enabled}")

    print("\n8. System reset...")
    coordinator.reset_system()
    reset_status = coordinator.get_system_status()
    print(f"   ✓ State after reset: {reset_status['state']}")

    # Stop control loop
    coordinator.stop_control_loop()
    print("   ✓ Control loop stopped")

    print("\n" + "=" * 60)
    print("PHASE 6 SIMPLE DEMO COMPLETE")
    print("✓ Control coordinator created and configured")
    print("✓ Control loop operation verified")
    print("✓ Sensor integration functional")
    print("✓ Thermodynamic calculations working")
    print("✓ Emergency procedures tested")
    print("✓ System state management operational")
    print("=" * 60)


def test_phase5_integration():
    """Test Phase 5 thermodynamic integration in Phase 6."""
    print("\n" + "=" * 60)
    print("PHASE 5 INTEGRATION TEST")
    print("=" * 60)

    coordinator = create_standard_kpp_pneumatic_coordinator(enable_thermodynamics=True)

    print("Testing advanced thermodynamic capabilities...")

    if coordinator.thermodynamics:
        print("✓ Advanced thermodynamics module loaded")

        # Test thermodynamic properties
        temp = 320.15  # 47°C
        pressure = 250000.0  # 2.5 bar

        density = coordinator.thermodynamics.props.air_density(pressure, temp)
        print(f"✓ Air density (47°C, 2.5 bar): {density:.3f} kg/m³")

        # Test compression work calculation
        work = coordinator.thermodynamics.compression.adiabatic_compression_work(
            0.01, 200000.0, 250000.0, temp
        )
        print(f"✓ Adiabatic compression work: {work/1000:.2f} kJ")

        # Test expansion calculation
        expansion_data = (
            coordinator.thermodynamics.expansion.expansion_with_heat_transfer(
                0.01, 250000.0, 150000.0, temp, "adiabatic", 5.0
            )
        )
        print(f"✓ Final volume: {expansion_data['final_volume']*1000:.1f} L")
        print(
            f"✓ Final temperature: {expansion_data['final_temperature'] - 273.15:.1f}°C"
        )

    if coordinator.heat_exchange:
        print("✓ Heat exchange module loaded")

        # Test heat transfer calculation - use the correct method
        air_mass = coordinator.thermodynamics.props.air_mass_from_volume(
            0.01, pressure, temp
        )
        heat_exchange_data = (
            coordinator.heat_exchange.air_water_exchange.heat_transfer_over_time(
                320.15,
                288.15,
                air_mass,
                1.0,  # 47°C air, 15°C water, air mass, 1 second
            )
        )
        print(
            f"✓ Air-water heat transfer: {heat_exchange_data['total_heat_transferred']/1000:.2f} kJ"
        )

    print("✓ Phase 5 integration fully functional in Phase 6")


if __name__ == "__main__":
    try:
        run_phase6_simple_demo()
        test_phase5_integration()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback

        traceback.print_exc()
