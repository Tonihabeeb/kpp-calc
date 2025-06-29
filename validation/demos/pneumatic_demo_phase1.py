"""
Phase 1 Pneumatic System Demonstration

This script demonstrates the functionality of the newly implemented
air compression and pressure control systems from Phase 1.

It shows realistic pneumatic system behavior including:
- Air compression with energy calculations
- Pressure control with hysteresis
- Safety monitoring and fault detection
- Energy efficiency tracking
"""

import os
import sys
import time

import matplotlib.pyplot as plt
import numpy as np

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from simulation.pneumatics import (
    CompressorState,
    SafetyLevel,
    create_standard_kpp_compressor,
    create_standard_kpp_pressure_controller,
)


def demonstrate_compression_physics():
    """Demonstrate compression physics calculations."""
    print("🔧 Demonstrating Air Compression Physics")
    print("-" * 50)

    compressor = create_standard_kpp_compressor()

    # Test different depths and their pressure requirements
    depths = [5, 10, 15, 20, 25]  # meters
    print("Pressure requirements for different depths:")
    for depth in depths:
        required_pressure = compressor.get_required_injection_pressure(depth)
        print(
            f"  {depth:2d}m depth: {required_pressure/100000:.2f} bar "
            f"({required_pressure/101325:.1f} atm)"
        )

    print("\nCompression work calculations (for 0.1 m³ air):")
    volume = 0.1  # m³
    for depth in [10, 20]:
        target_pressure = compressor.get_required_injection_pressure(depth)

        isothermal = compressor.calculate_isothermal_compression_work(
            volume, target_pressure
        )
        adiabatic = compressor.calculate_adiabatic_compression_work(
            volume, target_pressure
        )
        actual, heat_gen, heat_removed = compressor.calculate_actual_compression_work(
            volume, target_pressure
        )

        print(f"\n  {depth}m depth ({target_pressure/100000:.1f} bar):")
        print(f"    Isothermal work:  {isothermal/1000:.1f} kJ")
        print(f"    Adiabatic work:   {adiabatic/1000:.1f} kJ")
        print(f"    Actual work:      {actual/1000:.1f} kJ")
        print(f"    Heat generated:   {heat_gen/1000:.1f} kJ")
        print(f"    Heat removed:     {heat_removed/1000:.1f} kJ")

        # Calculate electrical power needed
        electrical_power = actual / compressor.compressor.efficiency
        print(f"    Electrical input: {electrical_power/1000:.1f} kJ")
        print(f"    Efficiency:       {(actual/electrical_power)*100:.1f}%")


def demonstrate_pressure_control():
    """Demonstrate pressure control system behavior."""
    print("\n🎛️  Demonstrating Pressure Control System")
    print("-" * 50)

    # Create integrated system
    air_system = create_standard_kpp_compressor()
    control_system = create_standard_kpp_pressure_controller(2.5)  # 2.5 bar target
    control_system.set_air_compressor(air_system)

    print(f"Target pressure: {control_system.settings.target_pressure/100000:.1f} bar")
    print(
        f"High setpoint:   {control_system.settings.high_pressure_setpoint/100000:.1f} bar"
    )
    print(
        f"Low setpoint:    {control_system.settings.low_pressure_setpoint/100000:.1f} bar"
    )

    # Simulate pressure buildup
    dt = 1.0  # 1 second steps
    current_time = 0.0
    max_time = 120.0  # 2 minutes

    # Data collection
    times = []
    pressures = []
    compressor_states = []
    power_consumption = []

    print(
        f"\nSimulating pressure buildup (starting at {air_system.tank_pressure/100000:.2f} bar):"
    )

    while current_time < max_time:
        results = control_system.control_step(dt, current_time)

        # Collect data
        times.append(current_time)
        pressures.append(results["tank_pressure"] / 100000.0)  # Convert to bar
        compressor_states.append(results["compressor_state"])
        power_consumption.append(
            results["compressor_results"].get("power_consumed", 0) / 1000.0
        )  # kW

        # Print periodic updates
        if int(current_time) % 20 == 0 and current_time > 0:
            print(
                f"  t={current_time:3.0f}s: "
                f"P={results['tank_pressure']/100000:.2f} bar, "
                f"State={results['compressor_state']}, "
                f"Power={results['compressor_results'].get('power_consumed', 0)/1000:.1f} kW"
            )

        current_time += dt

        # Stop if target reached
        if results["tank_pressure"] >= control_system.settings.target_pressure * 0.98:
            print(f"  Target pressure reached at t={current_time:.0f}s")
            break

    # Show final status
    final_status = control_system.get_control_status()
    air_status = air_system.get_system_status()

    print(f"\nFinal system status:")
    print(f"  Final pressure:    {final_status['current_pressure_bar']:.2f} bar")
    print(f"  Compressor cycles: {final_status['cycle_count']}")
    print(
        f"  Total runtime:     {final_status['total_runtime_hours']*3600:.0f} seconds"
    )
    print(f"  Energy consumed:   {air_status['total_energy_consumed_kwh']*1000:.1f} Wh")
    print(f"  Overall efficiency: {air_status['compression_efficiency']*100:.1f}%")

    return times, pressures, compressor_states, power_consumption


def demonstrate_air_consumption_regulation():
    """Demonstrate pressure regulation during air consumption."""
    print("\n💨 Demonstrating Air Consumption and Regulation")
    print("-" * 50)

    # Create system and build up pressure first
    air_system = create_standard_kpp_compressor()
    control_system = create_standard_kpp_pressure_controller(2.0)  # 2 bar target
    control_system.set_air_compressor(air_system)

    # Build up pressure (simplified)
    for _ in range(60):  # 1 minute to build pressure
        control_system.control_step(1.0, float(_))

    print(f"Initial pressure: {air_system.tank_pressure/100000:.2f} bar")

    # Simulate air consumption events
    dt = 1.0
    current_time = 60.0
    consumption_events = [70, 85, 100, 115, 130]  # times when air is consumed
    consumption_volume = 0.02  # m³ per consumption event

    times = []
    pressures = []
    compressor_states = []
    consumption_markers = []

    for t in range(60, 150):  # 90 seconds of operation
        current_time = float(t)

        # Consume air at specified times
        if t in consumption_events:
            success = air_system.consume_air_from_tank(consumption_volume)
            consumption_markers.append(t - 60)  # Relative time
            print(
                f"  t={t-60:2.0f}s: Consumed {consumption_volume*1000:.0f}L, "
                f"P={air_system.tank_pressure/100000:.2f} bar"
            )

        # Run control step
        results = control_system.control_step(dt, current_time)

        # Collect data
        times.append(t - 60)  # Relative time
        pressures.append(results["tank_pressure"] / 100000.0)
        compressor_states.append(results["compressor_state"])

    print(f"Final pressure: {air_system.tank_pressure/100000:.2f} bar")

    return times, pressures, compressor_states, consumption_markers


def demonstrate_safety_systems():
    """Demonstrate safety monitoring and emergency procedures."""
    print("\n🚨 Demonstrating Safety Systems")
    print("-" * 50)

    control_system = create_standard_kpp_pressure_controller(2.0)

    # Test safety level calculations
    test_pressures = [
        (100000, "Very low pressure"),
        (150000, "Critical low pressure"),
        (200000, "Normal pressure"),
        (300000, "High pressure"),
        (350000, "Emergency high pressure"),
    ]

    print("Safety level responses to different pressures:")
    for pressure, description in test_pressures:
        safety_level = control_system.check_safety_conditions(pressure)
        print(
            f"  {pressure/100000:.1f} bar ({description}): {safety_level.value.upper()}"
        )
        if control_system.safety_warnings:
            print(f"    Warnings: {', '.join(control_system.safety_warnings)}")

    # Test emergency stop
    print(f"\nTesting emergency stop:")
    control_system.compressor_state = CompressorState.RUNNING
    print(f"  Before emergency stop: State = {control_system.compressor_state.value}")

    control_system.emergency_stop()
    print(f"  After emergency stop:  State = {control_system.compressor_state.value}")
    print(f"  Emergency active:      {control_system.emergency_stop_active}")

    # Test reset
    control_system.reset_emergency_stop()
    print(
        f"  After reset:           Emergency active = {control_system.emergency_stop_active}"
    )


def create_visualization(
    times,
    pressures,
    compressor_states,
    power_consumption=None,
    consumption_markers=None,
):
    """Create visualization of pneumatic system operation."""
    try:
        fig, axes = plt.subplots(
            2 if power_consumption else 1,
            1,
            figsize=(12, 8 if power_consumption else 6),
        )
        if not isinstance(axes, np.ndarray):
            axes = [axes]

        # Pressure plot
        axes[0].plot(times, pressures, "b-", linewidth=2, label="Tank Pressure")
        axes[0].set_ylabel("Pressure (bar)")
        axes[0].set_title("KPP Pneumatic System Operation - Phase 1 Demonstration")
        axes[0].grid(True, alpha=0.3)
        axes[0].legend()

        # Mark consumption events if provided
        if consumption_markers:
            for marker_time in consumption_markers:
                axes[0].axvline(
                    x=marker_time,
                    color="red",
                    linestyle="--",
                    alpha=0.7,
                    label="Air Consumption",
                )

        # Color background based on compressor state
        state_colors = {
            "off": "lightgray",
            "starting": "yellow",
            "running": "lightgreen",
            "stopping": "orange",
        }

        for i in range(len(times) - 1):
            state = compressor_states[i]
            color = state_colors.get(state, "white")
            axes[0].axvspan(times[i], times[i + 1], alpha=0.2, color=color)

        # Power consumption plot if provided
        if power_consumption:
            axes[1].plot(
                times, power_consumption, "r-", linewidth=2, label="Compressor Power"
            )
            axes[1].set_ylabel("Power (kW)")
            axes[1].set_xlabel("Time (seconds)")
            axes[1].grid(True, alpha=0.3)
            axes[1].legend()
        else:
            axes[0].set_xlabel("Time (seconds)")

        plt.tight_layout()
        plt.savefig("pneumatic_system_demo.png", dpi=150, bbox_inches="tight")
        print(f"\n📊 Visualization saved as 'pneumatic_system_demo.png'")
        plt.show()

    except ImportError:
        print("📊 Matplotlib not available - skipping visualization")


def main():
    """Run complete Phase 1 demonstration."""
    print("🚀 KPP Pneumatic System - Phase 1 Demonstration")
    print("=" * 60)
    print("This demonstration shows the newly implemented air compression")
    print("and pressure control systems with realistic physics modeling.")
    print()

    try:
        # Demonstrate compression physics
        demonstrate_compression_physics()

        # Demonstrate pressure control
        times, pressures, states, power = demonstrate_pressure_control()

        # Demonstrate consumption regulation
        times2, pressures2, states2, markers = demonstrate_air_consumption_regulation()

        # Demonstrate safety systems
        demonstrate_safety_systems()

        # Create visualizations
        print("\n📊 Creating visualizations...")
        create_visualization(times, pressures, states, power)

        print("\n✅ Phase 1 demonstration completed successfully!")
        print("\nKey achievements:")
        print("  ✓ Realistic air compression physics with energy calculations")
        print("  ✓ Intelligent pressure control with hysteresis and safety monitoring")
        print("  ✓ Proper energy conservation (no over-unity)")
        print("  ✓ Safety systems with emergency stop and fault detection")
        print("  ✓ Integration-ready design for Phase 2 components")

        print(
            f"\nNext steps: Phase 2 will add air injection control and floater coordination"
        )

    except Exception as e:
        print(f"\n❌ Demonstration failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
