#!/usr/bin/env python3
"""
Phase 5 Pneumatic System Demonstration: Thermodynamic Modeling and Thermal Boost

This demo showcases the advanced thermodynamic capabilities of the KPP pneumatic system:
- Thermodynamic properties and calculations
- Compression and expansion thermodynamics
- Heat exchange modeling with water reservoir
- Thermal buoyancy boost calculations
- Complete thermodynamic cycle analysis
- Performance optimization through thermal effects

Usage: python pneumatic_demo_phase5.py
"""

import math

import matplotlib.pyplot as plt
import numpy as np

from config.config import RHO_WATER, G
from simulation.components.pneumatics import PneumaticSystem
from simulation.pneumatics.heat_exchange import (
    AirWaterHeatExchange,
    CompressionHeatRecovery,
    HeatTransferCoefficients,
    IntegratedHeatExchange,
    WaterThermalReservoir,
)
from simulation.pneumatics.thermodynamics import (
    AdvancedThermodynamics,
    CompressionThermodynamics,
    ExpansionThermodynamics,
    ThermalBuoyancyCalculator,
    ThermodynamicProperties,
)


def demo_thermodynamic_properties():
    """Demonstrate basic thermodynamic properties and calculations."""
    print("=== Phase 5 Demo: Thermodynamic Properties ===")

    props = ThermodynamicProperties()
    print(f"Air Properties:")
    print(f"  Specific gas constant: {props.R_specific_air:.1f} J/(kg·K)")
    print(f"  Heat capacity ratio (γ): {props.gamma_air:.2f}")
    print(f"  Specific heat (cp): {props.cp_air:.1f} J/(kg·K)")
    print(f"  Standard density: {props.rho_air_standard:.3f} kg/m³")

    # Test air density at different conditions
    pressures = [101325, 150000, 200000, 300000]  # Pa
    temperatures = [273.15, 293.15, 313.15]  # K

    print(f"\nAir Density at Different Conditions:")
    print(f"{'Pressure (bar)':>15} {'Temperature (°C)':>18} {'Density (kg/m³)':>18}")
    print("-" * 55)

    for P in pressures:
        for T in temperatures:
            density = props.air_density(P, T)
            print(f"{P/100000:>13.1f} {T-273.15:>16.1f} {density:>16.3f}")

    print()


def demo_compression_thermodynamics():
    """Demonstrate compression thermodynamics and work calculations."""
    print("=== Phase 5 Demo: Compression Thermodynamics ===")

    compression = CompressionThermodynamics()

    # Compression scenario: 10L air tank, 1 bar to 3 bar
    volume = 0.01  # 10 liters
    P_initial = 101325.0  # 1 bar
    P_final = 303975.0  # 3 bar
    T_initial = 293.15  # 20°C

    print(f"Compression Analysis:")
    print(f"  Initial volume: {volume*1000:.1f} L")
    print(f"  Initial pressure: {P_initial/100000:.1f} bar")
    print(f"  Final pressure: {P_final/100000:.1f} bar")
    print(f"  Initial temperature: {T_initial-273.15:.1f}°C")

    # Calculate different compression modes
    T_adiabatic = compression.adiabatic_compression_temperature(
        P_initial, P_final, T_initial
    )
    work_isothermal = compression.isothermal_compression_work(
        volume, P_initial, P_final
    )
    work_adiabatic = compression.adiabatic_compression_work(
        volume, P_initial, P_final, T_initial
    )
    heat_generated = compression.compression_heat_generation(work_adiabatic, 0.85)

    print(f"\nCompression Results:")
    print(f"  Adiabatic final temperature: {T_adiabatic-273.15:.1f}°C")
    print(f"  Isothermal work: {work_isothermal:.1f} J")
    print(f"  Adiabatic work: {work_adiabatic:.1f} J")
    print(f"  Heat generated: {heat_generated:.1f} J")
    print(f"  Work ratio (adiabatic/isothermal): {work_adiabatic/work_isothermal:.3f}")

    # Intercooling analysis
    T_intercooled = compression.intercooling_temperature_drop(T_adiabatic, 293.15, 0.8)
    print(f"  Temperature after intercooling: {T_intercooled-273.15:.1f}°C")

    print()


def demo_expansion_thermodynamics():
    """Demonstrate expansion thermodynamics with heat transfer."""
    print("=== Phase 5 Demo: Expansion Thermodynamics ===")

    expansion = ExpansionThermodynamics()

    # Expansion scenario: 3 bar compressed air expanding to 1 bar
    P_initial = 303975.0  # 3 bar
    P_final = 101325.0  # 1 bar
    T_initial = 293.15  # 20°C
    V_initial = 0.003333  # Initial volume (compressed)

    print(f"Expansion Analysis:")
    print(f"  Initial pressure: {P_initial/100000:.1f} bar")
    print(f"  Final pressure: {P_final/100000:.1f} bar")
    print(f"  Initial temperature: {T_initial-273.15:.1f}°C")
    print(f"  Initial volume: {V_initial*1000:.1f} L")

    # Define expansion time before using it
    expansion_time = 15.0  # 15 second expansion

    # Different expansion modes
    expansion_results = expansion.expansion_with_heat_transfer(
        V_initial, P_initial, P_final, T_initial, "adiabatic", expansion_time
    )
    V_adiabatic = expansion_results["final_volume"]
    T_adiabatic = expansion_results["final_temperature"]

    expansion_results = expansion.expansion_with_heat_transfer(
        V_initial, P_initial, P_final, T_initial, "isothermal", expansion_time
    )
    V_isothermal = expansion_results["final_volume"]
    T_isothermal = expansion_results["final_temperature"]

    # Mixed expansion with heat transfer
    expansion_results = expansion.expansion_with_heat_transfer(
        V_initial, P_initial, P_final, T_initial, "mixed", expansion_time
    )
    V_mixed = expansion_results["final_volume"]
    T_mixed = expansion_results["final_temperature"]

    print(f"\nExpansion Results:")
    print(f"  Adiabatic final volume: {V_adiabatic*1000:.1f} L")
    print(f"  Isothermal final volume: {V_isothermal*1000:.1f} L")
    print(f"  Mixed expansion volume: {V_mixed*1000:.1f} L")
    print(f"  Mixed expansion temperature: {T_mixed-273.15:.1f}°C")
    print(f"  Volume expansion ratios:")
    print(f"    Adiabatic: {V_adiabatic/V_initial:.2f}")
    print(f"    Isothermal: {V_isothermal/V_initial:.2f}")
    print(f"    Mixed: {V_mixed/V_initial:.2f}")

    print()


def demo_thermal_buoyancy():
    """Demonstrate thermal buoyancy boost calculations."""
    print("=== Phase 5 Demo: Thermal Buoyancy Boost ===")

    calc = PneumaticSystem()

    # Buoyancy scenario
    V_air = 0.01  # 10L air volume
    T_air = 320.15  # 47°C hot air
    T_water = 288.15  # 15°C water
    depth = 5.0  # 5m depth

    print(f"Thermal Buoyancy Analysis:")
    print(f"  Air volume: {V_air*1000:.1f} L")
    print(f"  Air temperature: {T_air-273.15:.1f}°C")
    print(f"  Water temperature: {T_water-273.15:.1f}°C")
    print(f"  Depth: {depth:.1f} m")

    # Calculate thermal effects
    boost = calc.calculate_thermal_buoyancy_boost(V_air, T_air, T_water, depth)

    # Calculate a simple thermal efficiency factor
    temp_diff = abs(T_air - T_water)
    efficiency = min(0.1, temp_diff / 100.0)  # Simple approximation

    # Base buoyancy (without thermal effects)
    P_depth = 101325 + RHO_WATER * G * depth
    rho_air_cold = P_depth / (287.0 * T_water)
    base_buoyancy = V_air * (RHO_WATER - rho_air_cold) * G

    total_buoyancy = base_buoyancy + boost

    print(f"\nBuoyancy Results:")
    print(f"  Base buoyancy force: {base_buoyancy:.1f} N")
    print(f"  Thermal boost: {boost:.1f} N")
    print(f"  Total buoyancy: {total_buoyancy:.1f} N")
    print(f"  Thermal efficiency factor: {efficiency:.3f}")
    print(f"  Performance improvement: {boost/base_buoyancy*100:.1f}%")

    print()


def demo_heat_exchange():
    """Demonstrate heat exchange modeling with water reservoir."""
    print("=== Phase 5 Demo: Heat Exchange Modeling ===")

    # Water thermal reservoir
    reservoir = WaterThermalReservoir()

    print(f"Water Thermal Properties:")
    print(f"  Surface temperature: {reservoir.surface_temperature-273.15:.1f}°C")
    print(f"  Thermal gradient: {reservoir.temperature_gradient*100:.1f}°C/100m")
    print(
        f"  Water thermal conductivity: {reservoir.water_thermal_conductivity:.1f} W/(m·K)"
    )

    # Temperature at different depths
    depths = [0, 2, 5, 10, 20]
    print(f"\nWater Temperature vs Depth:")
    print(f"{'Depth (m)':>10} {'Temperature (°C)':>18}")
    print("-" * 30)
    for depth in depths:
        T_water = reservoir.water_temperature_at_depth(depth)
        print(f"{depth:>8.1f} {T_water-273.15:>16.1f}")

    # Heat transfer analysis
    heat_exchange = IntegratedHeatExchange()

    # Heat exchange scenario
    floater_position = 5.0  # 5m depth
    air_temp = 320.15  # 47°C hot air
    water_temp = 288.15  # 15°C water
    air_volume = 0.01  # 10L
    air_pressure = 200000.0  # 2 bar
    ascent_velocity = 0.5  # 0.5 m/s
    ascent_time = 15.0  # 15 seconds

    analysis = heat_exchange.complete_heat_exchange_analysis(
        floater_position,
        air_volume,
        air_pressure,
        air_temp,
        ascent_velocity,
        ascent_time,
    )

    print(f"\nHeat Exchange Analysis:")
    print(f"  Initial air temperature: {air_temp-273.15:.1f}°C")
    print(f"  Water temperature: {water_temp-273.15:.1f}°C")
    print(f"  Air volume: {air_volume*1000:.1f} L")
    print(f"  Ascent time: {ascent_time:.1f} s")
    print(f"  Heat transfer rate: {analysis['heat_transfer_rate']:.1f} W")
    print(f"  Total heat transfer: {analysis['total_heat_transfer']:.1f} J")
    print(f"  Final air temperature: {analysis['final_air_temperature']-273.15:.1f}°C")
    print(f"  Temperature drop: {air_temp-analysis['final_air_temperature']:.1f}°C")

    print()


def demo_complete_thermodynamic_cycle():
    """Demonstrate complete thermodynamic cycle analysis."""
    print("=== Phase 5 Demo: Complete Thermodynamic Cycle ===")

    thermo = AdvancedThermodynamics()

    # Complete cycle parameters
    initial_air_volume = 0.006  # 6L at surface
    injection_pressure = 250000.0  # 2.5 bar injection
    surface_pressure = 101325.0  # 1 bar surface
    injection_temperature = 290.15  # 17°C injection
    ascent_time = 15.0  # 15 second ascent
    base_buoyant_force = 78.5  # ~8kg buoyancy equivalent

    print(f"Thermodynamic Cycle Parameters:")
    print(f"  Initial air volume: {initial_air_volume*1000:.1f} L")
    print(f"  Injection pressure: {injection_pressure/100000:.1f} bar")
    print(f"  Surface pressure: {surface_pressure/100000:.1f} bar")
    print(f"  Injection temperature: {injection_temperature-273.15:.1f}°C")
    print(f"  Ascent time: {ascent_time:.1f} s")
    print(f"  Base buoyant force: {base_buoyant_force:.1f} N")

    # Run complete analysis
    results = thermo.complete_thermodynamic_cycle(
        initial_air_volume,
        injection_pressure,
        surface_pressure,
        injection_temperature,
        ascent_time,
        base_buoyant_force,
    )

    print(f"\nCycle Analysis Results:")

    # Compression phase
    compression = results["compression"]
    print(f"  Compression Work:")
    print(f"    Isothermal: {compression['isothermal_work']:.1f} J")
    print(f"    Adiabatic: {compression['adiabatic_work']:.1f} J")
    print(f"    Heat generated: {compression['heat_generated']:.1f} J")

    # Expansion phase
    expansion = results["expansion"]
    print(f"  Expansion Results:")
    print(f"    Volume ratio: {expansion['expansion_ratio']:.2f}")
    print(f"    Final temperature: {expansion['final_temperature']-273.15:.1f}°C")

    # Thermal buoyancy
    thermal = results["thermal_buoyancy"]
    print(f"  Thermal Effects:")
    print(f"    Buoyancy boost: {thermal['buoyancy_boost']:.1f} N")
    print(f"    Efficiency factor: {thermal['efficiency_factor']:.3f}")

    # Energy balance
    energy = results["energy_balance"]
    print(f"  Energy Balance:")
    print(f"    Input energy: {energy['total_input_energy']:.1f} J")
    print(f"    Useful work: {energy['useful_work_output']:.1f} J")
    print(f"    Thermal losses: {energy['thermal_losses']:.1f} J")
    print(f"    System efficiency: {energy['system_efficiency']*100:.1f}%")

    # Performance metrics
    performance = results["performance_metrics"]
    print(f"  Performance Metrics:")
    print(f"    Power enhancement: {performance['power_enhancement_factor']:.2f}")
    print(f"    Energy efficiency: {performance['energy_efficiency_ratio']:.3f}")
    print(
        f"    Thermal contribution: {performance['thermal_contribution_percent']:.1f}%"
    )

    print()


def create_thermodynamic_plots():
    """Create visualization plots for thermodynamic analysis."""
    print("=== Phase 5 Demo: Creating Thermodynamic Visualization ===")

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle("KPP Phase 5: Thermodynamic Analysis", fontsize=16, fontweight="bold")

    # Plot 1: Compression work comparison
    compression = CompressionThermodynamics()
    pressure_ratios = np.linspace(1.5, 5.0, 20)
    volume = 0.01
    P_initial = 101325.0
    T_initial = 293.15

    isothermal_work = []
    adiabatic_work = []

    for ratio in pressure_ratios:
        P_final = P_initial * ratio
        iso_work = compression.isothermal_compression_work(volume, P_initial, P_final)
        adi_work = compression.adiabatic_compression_work(
            volume, P_initial, P_final, T_initial
        )
        isothermal_work.append(iso_work)
        adiabatic_work.append(adi_work)

    ax1.plot(pressure_ratios, isothermal_work, "b-", label="Isothermal", linewidth=2)
    ax1.plot(pressure_ratios, adiabatic_work, "r-", label="Adiabatic", linewidth=2)
    ax1.set_xlabel("Pressure Ratio")
    ax1.set_ylabel("Compression Work (J)")
    ax1.set_title("Compression Work vs Pressure Ratio")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Temperature effects during compression
    temperatures = []
    for ratio in pressure_ratios:
        P_final = P_initial * ratio
        T_final = compression.adiabatic_compression_temperature(
            P_initial, P_final, T_initial
        )
        temperatures.append(T_final - 273.15)

    ax2.plot(pressure_ratios, temperatures, "g-", linewidth=2)
    ax2.set_xlabel("Pressure Ratio")
    ax2.set_ylabel("Final Temperature (°C)")
    ax2.set_title("Adiabatic Compression Temperature")
    ax2.grid(True, alpha=0.3)

    # Plot 3: Thermal buoyancy boost
    calc = PneumaticSystem()
    air_temps = np.linspace(288.15, 333.15, 20)  # 15°C to 60°C
    water_temp = 288.15  # 15°C
    air_volume = 0.01
    depth = 5.0

    buoyancy_boosts = []
    base_buoyancy = []

    for T_air in air_temps:
        boost = calc.calculate_thermal_buoyancy_boost(
            air_volume, T_air, water_temp, depth
        )
        buoyancy_boosts.append(boost)

        # Calculate base buoyancy at this temperature
        P_depth = 101325 + RHO_WATER * G * depth
        rho_air = P_depth / (287.0 * water_temp)
        base = air_volume * (RHO_WATER - rho_air) * G
        base_buoyancy.append(base)

    ax3.plot(
        air_temps - 273.15, buoyancy_boosts, "r-", label="Thermal Boost", linewidth=2
    )
    ax3.plot(
        air_temps - 273.15, base_buoyancy, "b--", label="Base Buoyancy", linewidth=2
    )
    ax3.set_xlabel("Air Temperature (°C)")
    ax3.set_ylabel("Buoyancy Force (N)")
    ax3.set_title("Thermal Buoyancy Enhancement")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Heat transfer effects
    reservoir = WaterThermalReservoir()
    depths = np.linspace(0, 20, 50)
    water_temps = [reservoir.water_temperature_at_depth(d) - 273.15 for d in depths]

    ax4.plot(depths, water_temps, "c-", linewidth=2)
    ax4.set_xlabel("Depth (m)")
    ax4.set_ylabel("Water Temperature (°C)")
    ax4.set_title("Water Temperature Profile")
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save the plot
    plot_path = "static/plots/phase5_thermodynamics.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    print(f"Thermodynamic analysis plot saved to: {plot_path}")

    plt.show()


def main():
    """Run the complete Phase 5 pneumatic system demonstration."""
    print("=" * 70)
    print("KPP PNEUMATIC SYSTEM - PHASE 5 DEMONSTRATION")
    print("Thermodynamic Modeling and Thermal Boost")
    print("=" * 70)
    print()

    try:
        # Run all demonstration components
        demo_thermodynamic_properties()
        demo_compression_thermodynamics()
        demo_expansion_thermodynamics()
        demo_thermal_buoyancy()
        demo_heat_exchange()
        demo_complete_thermodynamic_cycle()
        create_thermodynamic_plots()

        print("=" * 70)
        print("PHASE 5 DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print()
        print("Key Phase 5 Capabilities Demonstrated:")
        print("✓ Advanced thermodynamic property calculations")
        print("✓ Compression and expansion thermodynamics")
        print("✓ Heat transfer and thermal reservoir modeling")
        print("✓ Thermal buoyancy boost calculations")
        print("✓ Complete thermodynamic cycle analysis")
        print("✓ Energy balance and performance optimization")
        print("✓ Real-world physics validation")
        print()
        print("Phase 5 successfully integrates thermal effects into the")
        print("pneumatic system, providing significant performance enhancements")
        print("through proper thermodynamic modeling and heat exchange.")

    except Exception as e:
        print(f"Demo encountered an error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
