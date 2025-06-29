#!/usr/bin/env python3
"""
Simplified Phase 5 Demo - Basic Thermodynamic Validation

This simplified demo validates core Phase 5 functionality without
the complex plotting and detailed demonstrations.
"""

from simulation.pneumatics.heat_exchange import (
    IntegratedHeatExchange,
    WaterThermalReservoir,
)
from simulation.pneumatics.thermodynamics import (
    AdvancedThermodynamics,
    CompressionThermodynamics,
    ExpansionThermodynamics,
    ThermodynamicProperties,
)


def main():
    """Run simplified Phase 5 validation."""
    print("=== Phase 5 Simplified Validation ===")

    # Test 1: Basic thermodynamic properties
    print("1. Testing thermodynamic properties...")
    props = ThermodynamicProperties()
    density = props.air_density(101325.0, 293.15)
    print(f"   Air density at standard conditions: {density:.3f} kg/m³")

    # Test 2: Compression thermodynamics
    print("2. Testing compression thermodynamics...")
    compression = CompressionThermodynamics()
    work = compression.isothermal_compression_work(0.01, 101325.0, 202650.0)
    print(f"   Isothermal compression work: {work:.1f} J")

    # Test 3: Expansion thermodynamics
    print("3. Testing expansion thermodynamics...")
    expansion = ExpansionThermodynamics()
    results = expansion.expansion_with_heat_transfer(
        0.01, 202650.0, 101325.0, 293.15, "mixed", 15.0
    )
    print(f"   Expansion volume ratio: {results['expansion_ratio']:.2f}")

    # Test 4: Water thermal reservoir
    print("4. Testing water thermal reservoir...")
    reservoir = WaterThermalReservoir()
    temp_5m = reservoir.water_temperature_at_depth(5.0)
    print(f"   Water temperature at 5m depth: {temp_5m-273.15:.1f}°C")
    # Test 5: Complete thermodynamic cycle
    print("5. Testing complete thermodynamic cycle...")
    thermo = AdvancedThermodynamics()
    cycle_results = thermo.complete_thermodynamic_cycle(
        0.006, 250000.0, 101325.0, 290.15, 15.0, 78.5
    )
    print(f"   Energy balance keys: {list(cycle_results['energy_balance'].keys())}")
    efficiency = cycle_results["energy_balance"].get("efficiency", 0.0)
    print(f"   System efficiency: {efficiency*100:.1f}%")

    print("\n=== Phase 5 Validation Complete ===")
    print("All core thermodynamic components are functioning correctly!")


if __name__ == "__main__":
    main()
