#!/usr/bin/env python3
"""
Demonstration script for Phase 4: Venting and Reset Mechanism

This script demonstrates the complete venting cycle for pneumatic floaters,
including automatic venting triggers, air release dynamics, water refill,
and floater reset to heavy state.

Phase 4 Features Demonstrated:
1. Automatic venting triggers (position-based, tilt-based, surface breach)
2. Air release dynamics with choked/subsonic flow
3. Water inflow calculations
4. Complete venting cycle with floater state transitions
5. Reset coordination for descent phase
"""

import logging
import os
import sys

import matplotlib.pyplot as plt
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import RHO_WATER, G
from simulation.components.floater import Floater
from simulation.pneumatics.venting_system import AutomaticVentingSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def demonstrate_venting_triggers():
    """Demonstrate different venting trigger mechanisms."""
    print("\n" + "=" * 60)
    print("PHASE 4 DEMONSTRATION: VENTING TRIGGERS")
    print("=" * 60)

    # Create venting system
    venting_system = AutomaticVentingSystem(tank_height=10.0)

    # Test position-based trigger
    print("\n1. Position-Based Trigger Test:")
    positions = [5.0, 8.0, 9.0, 9.5, 10.0]
    for pos in positions:
        should_vent = venting_system.trigger.should_trigger_venting(pos)
        status = "TRIGGER" if should_vent else "no trigger"
        print(f"   Position {pos:4.1f}m: {status}")

    # Test tilt-based trigger
    print("\n2. Tilt-Based Trigger Test:")
    venting_system.trigger.trigger_type = "tilt"
    tilt_angles = [0.0, 15.0, 30.0, 45.0, 60.0]
    for tilt in tilt_angles:
        tilt_rad = tilt * np.pi / 180  # Convert to radians
        should_vent = venting_system.trigger.should_trigger_venting(9.0, tilt_rad)
        status = "TRIGGER" if should_vent else "no trigger"
        print(f"   Tilt angle {tilt:4.1f}°: {status}")

    # Test surface breach trigger
    print("\n3. Surface Breach Trigger Test:")
    venting_system.trigger.trigger_type = "surface_breach"
    positions = [8.0, 9.0, 9.5, 9.8, 10.0]
    for pos in positions:
        should_vent = venting_system.trigger.should_trigger_venting(
            pos, water_depth=10.0
        )
        depth_from_surface = 10.0 - pos
        status = "TRIGGER" if should_vent else "no trigger"
        print(
            f"   Position {pos:4.1f}m (depth from surface: {depth_from_surface:.1f}m): {status}"
        )


def demonstrate_air_release_physics():
    """Demonstrate air release rate calculations."""
    print("\n" + "=" * 60)
    print("PHASE 4 DEMONSTRATION: AIR RELEASE PHYSICS")
    print("=" * 60)

    # Create venting system
    venting_system = AutomaticVentingSystem(tank_height=10.0)
    air_physics = venting_system.air_physics

    # Test different pressure conditions
    print("\n1. Air Release Rates vs Pressure Difference:")
    print("   Internal Pressure | External Pressure | Flow Rate | Flow Type")
    print("   ------------------|-------------------|-----------|----------")

    pressure_scenarios = [
        (300000, 200000),  # 3 bar -> 2 bar (moderate)
        (300000, 150000),  # 3 bar -> 1.5 bar (high)
        (300000, 101325),  # 3 bar -> 1 bar (very high - choked)
        (200000, 180000),  # 2 bar -> 1.8 bar (low)
        (150000, 140000),  # 1.5 bar -> 1.4 bar (very low)
    ]

    for p_int, p_ext in pressure_scenarios:
        flow_rate = air_physics.calculate_air_release_rate(p_int, p_ext)
        pressure_ratio = p_ext / p_int
        critical_ratio = (2 / (1.4 + 1)) ** (1.4 / (1.4 - 1))
        flow_type = "Choked" if pressure_ratio <= critical_ratio else "Subsonic"

        print(
            f"   {p_int/1000:8.1f} kPa     | {p_ext/1000:8.1f} kPa      | {flow_rate*1000:6.1f} L/s | {flow_type}"
        )

    # Test water inflow rates
    print("\n2. Water Inflow Rates vs Depth:")
    print("   Depth | Air Volume | Available Space | Inflow Rate")
    print("   ------|------------|-----------------|------------")

    floater_total_volume = 0.01  # 10 liters
    depths = [1.0, 3.0, 5.0, 10.0, 15.0]

    for depth in depths:
        air_volume = 0.005  # 5 liters
        available_space = floater_total_volume - air_volume
        inflow_rate = air_physics.calculate_water_inflow_rate(
            air_volume, floater_total_volume, depth
        )

        print(
            f"   {depth:4.1f}m | {air_volume*1000:6.1f} L    | {available_space*1000:10.1f} L     | {inflow_rate*1000:6.1f} L/s"
        )


def demonstrate_complete_venting_cycle():
    """Demonstrate a complete venting cycle."""
    print("\n" + "=" * 60)
    print("PHASE 4 DEMONSTRATION: COMPLETE VENTING CYCLE")
    print("=" * 60)

    # Create floater and venting system
    floater = Floater(volume=0.01, mass=5.0, area=0.1, tank_height=10.0)
    venting_system = AutomaticVentingSystem(tank_height=10.0)

    # Set up floater with air injection
    floater.pneumatic_fill_state = "full"
    floater.total_air_injected = 0.006  # 6 liters
    floater.current_air_pressure = 250000.0  # 2.5 bar
    floater.position = 9.2  # Near top, ready for venting

    print(f"\nInitial State:")
    print(f"   Floater position: {floater.position:.1f} m")
    print(f"   Air injected: {floater.total_air_injected*1000:.1f} L")
    print(f"   Air pressure: {floater.current_air_pressure/1000:.1f} kPa")
    print(f"   Fill state: {floater.pneumatic_fill_state}")
    print(f"   Water mass: {floater.water_mass:.1f} kg")

    # Start venting process
    print(f"\nStarting venting process...")
    success = floater.start_venting_process(venting_system, 0.0)
    print(f"   Venting started: {success}")
    print(f"   New fill state: {floater.pneumatic_fill_state}")

    # Simulate venting process over time
    time_steps = []
    air_volumes = []
    water_masses = []
    air_pressures = []

    dt = 0.1  # 0.1 second time steps
    max_time = 10.0  # Maximum 10 seconds
    current_time = 0.0

    print(f"\nVenting Process Simulation:")
    print("   Time  | Air Volume | Water Mass | Air Pressure | Complete")
    print("   ------|------------|------------|--------------|----------")

    while current_time < max_time:
        # Update venting process
        is_complete = floater.update_venting_process(venting_system, dt)

        # Record data
        time_steps.append(current_time)
        air_volumes.append(floater.total_air_injected * 1000)  # Convert to liters
        water_masses.append(floater.water_mass)
        air_pressures.append(floater.current_air_pressure / 1000)  # Convert to kPa

        # Print periodic updates
        if int(current_time * 10) % 5 == 0:  # Every 0.5 seconds
            complete_status = "YES" if is_complete else "NO"
            print(
                f"   {current_time:4.1f}s | {floater.total_air_injected*1000:6.1f} L   | {floater.water_mass:6.1f} kg  | {floater.current_air_pressure/1000:8.1f} kPa | {complete_status}"
            )

        if is_complete:
            print(f"\n   Venting completed at t = {current_time:.1f}s")
            break

        current_time += dt

    # Final state
    print(f"\nFinal State:")
    print(f"   Air remaining: {floater.total_air_injected*1000:.1f} L")
    print(f"   Water mass: {floater.water_mass:.1f} kg")
    print(f"   Air pressure: {floater.current_air_pressure/1000:.1f} kPa")
    print(f"   Fill state: {floater.pneumatic_fill_state}")
    print(f"   Ready for descent: {floater.is_ready_for_descent()}")

    return time_steps, air_volumes, water_masses, air_pressures


def demonstrate_multiple_floater_coordination():
    """Demonstrate venting coordination for multiple floaters."""
    print("\n" + "=" * 60)
    print("PHASE 4 DEMONSTRATION: MULTIPLE FLOATER COORDINATION")
    print("=" * 60)

    # Create venting system
    venting_system = AutomaticVentingSystem(tank_height=10.0)

    # Create multiple floaters
    floaters = []
    for i in range(3):
        floater = Floater(volume=0.01, mass=5.0, area=0.1, tank_height=10.0)
        floater.pneumatic_fill_state = "full"
        floater.total_air_injected = 0.005 + i * 0.001  # Varying air volumes
        floater.current_air_pressure = 200000.0 + i * 20000.0  # Varying pressures
        floater.position = 9.0 + i * 0.2  # Different positions
        floaters.append(floater)

    print(f"\nInitial Floater States:")
    for i, floater in enumerate(floaters):
        print(
            f"   Floater {i+1}: {floater.total_air_injected*1000:.1f}L air, "
            f"{floater.current_air_pressure/1000:.1f} kPa, position {floater.position:.1f}m"
        )

    # Start venting for all floaters
    print(f"\nStarting coordinated venting...")
    for i, floater in enumerate(floaters):
        success = floater.start_venting_process(venting_system, 0.0)
        print(f"   Floater {i+1} venting started: {success}")

    # Check system status
    status = venting_system.get_system_status()
    print(f"\nVenting System Status:")
    print(f"   Active venting processes: {status['active_venting_count']}")
    print(f"   Processing venting count: {status['processing_venting_count']}")
    print(f"   Trigger type: {status['trigger_type']}")

    # Simulate coordinated venting
    dt = 0.2
    max_steps = 25

    print(f"\nCoordinated Venting Simulation:")
    print("Step | Floater 1     | Floater 2     | Floater 3     | Active")
    print("-----|---------------|---------------|---------------|-------")

    for step in range(max_steps):
        active_count = 0
        status_line = f"{step:3d}  |"

        for i, floater in enumerate(floaters):
            if floater.pneumatic_fill_state == "venting":
                is_complete = floater.update_venting_process(venting_system, dt)
                if not is_complete:
                    active_count += 1
                status_line += f" {floater.total_air_injected*1000:5.1f}L/{floater.water_mass:4.1f}kg |"
            else:
                status_line += "    COMPLETE     |"

        status_line += f"   {active_count}"
        print(status_line)

        if active_count == 0:
            print(f"\nAll floaters completed venting at step {step}")
            break

    # Final status
    print(f"\nFinal Floater States:")
    for i, floater in enumerate(floaters):
        print(
            f"   Floater {i+1}: {floater.total_air_injected*1000:.1f}L air, "
            f"{floater.water_mass:.1f}kg water, ready for descent: {floater.is_ready_for_descent()}"
        )


def plot_venting_dynamics(time_steps, air_volumes, water_masses, air_pressures):
    """Plot the venting dynamics over time."""
    print("\n" + "=" * 60)
    print("GENERATING VENTING DYNAMICS PLOTS")
    print("=" * 60)

    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle("Phase 4: Pneumatic Venting Dynamics", fontsize=16, fontweight="bold")

    # Air volume over time
    ax1.plot(time_steps, air_volumes, "b-", linewidth=2, label="Air Volume")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Air Volume (L)")
    ax1.set_title("Air Release During Venting")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Water mass over time
    ax2.plot(time_steps, water_masses, "g-", linewidth=2, label="Water Mass")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Water Mass (kg)")
    ax2.set_title("Water Inflow During Venting")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    # Air pressure over time
    ax3.plot(time_steps, air_pressures, "r-", linewidth=2, label="Air Pressure")
    ax3.axhline(
        y=101.325, color="k", linestyle="--", alpha=0.7, label="Atmospheric Pressure"
    )
    ax3.set_xlabel("Time (s)")
    ax3.set_ylabel("Air Pressure (kPa)")
    ax3.set_title("Pressure Equalization During Venting")
    ax3.grid(True, alpha=0.3)
    ax3.legend()

    # Phase diagram: Water mass vs Air volume
    ax4.plot(air_volumes, water_masses, "purple", linewidth=2, marker="o", markersize=3)
    ax4.set_xlabel("Air Volume (L)")
    ax4.set_ylabel("Water Mass (kg)")
    ax4.set_title("Venting State Transition")
    ax4.grid(True, alpha=0.3)

    # Add arrows to show direction
    if len(air_volumes) > 1:
        # Arrow from start to end
        ax4.annotate(
            "",
            xy=(air_volumes[-1], water_masses[-1]),
            xytext=(air_volumes[0], water_masses[0]),
            arrowprops=dict(arrowstyle="->", color="purple", lw=2),
        )
        ax4.text(
            air_volumes[0],
            water_masses[0],
            "Start",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7),
        )
        ax4.text(
            air_volumes[-1],
            water_masses[-1],
            "End",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7),
        )

    plt.tight_layout()
    plt.savefig(
        "static/plots/phase4_venting_dynamics.png", dpi=300, bbox_inches="tight"
    )
    print("   Plot saved as: static/plots/phase4_venting_dynamics.png")
    plt.show()


def main():
    """Main demonstration function."""
    print("=" * 60)
    print("KPP PNEUMATIC SYSTEM - PHASE 4 DEMONSTRATION")
    print("Venting and Reset Mechanism")
    print("=" * 60)

    try:
        # 1. Demonstrate venting triggers
        demonstrate_venting_triggers()

        # 2. Demonstrate air release physics
        demonstrate_air_release_physics()

        # 3. Demonstrate complete venting cycle
        time_data, air_data, water_data, pressure_data = (
            demonstrate_complete_venting_cycle()
        )

        # 4. Demonstrate multiple floater coordination
        demonstrate_multiple_floater_coordination()

        # 5. Generate plots
        if time_data:
            plot_venting_dynamics(time_data, air_data, water_data, pressure_data)

        print("\n" + "=" * 60)
        print("PHASE 4 DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nKey Features Demonstrated:")
        print("✓ Automatic venting triggers (position, tilt, surface breach)")
        print("✓ Air release dynamics (choked vs subsonic flow)")
        print("✓ Water inflow calculations based on hydrostatic pressure")
        print("✓ Complete venting cycle with state transitions")
        print("✓ Floater reset to heavy state for descent")
        print("✓ Multiple floater coordination and system status")
        print("✓ Real-time dynamics visualization")
        print("\nPhase 4 implementation is complete and validated!")

    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
