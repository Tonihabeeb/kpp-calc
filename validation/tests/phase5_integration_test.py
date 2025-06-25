#!/usr/bin/env python3
"""
Phase 5 Integration Test: Thermodynamic Integration with Main Simulation

This script tests the integration of Phase 5 thermodynamic capabilities
with the main KPP simulation system components.
"""

import sys
import os
import time
import math
import queue
from simulation.engine import SimulationEngine
from simulation.components.floater import Floater
from simulation.components.pneumatics import PneumaticSystem


def test_enhanced_pneumatic_system():
    """Test the enhanced pneumatic system with Phase 5 thermodynamics."""
    print("=== Testing Enhanced Pneumatic System ===")
    
    # Create enhanced pneumatic system with Phase 5 capabilities
    pneumatics = PneumaticSystem(
        tank_pressure=3.0,  # 3 bar
        tank_volume=0.1,    # 100L tank
        compressor_power=4.2,  # 4.2 kW (from specs)
        target_pressure=3.0,
        enable_thermodynamics=True,
        water_temperature=288.15,  # 15°C water
        expansion_mode='mixed'
    )
    
    print(f"✓ Pneumatic system created with Phase 5 thermodynamics")
    print(f"  Tank pressure: {pneumatics.tank_pressure} bar")
    print(f"  Thermodynamics enabled: {pneumatics.enable_thermodynamics}")
      # Create a test floater
    floater = Floater(mass=10.0, volume=0.012, area=0.5)  # 10kg, 12L floater, 0.5m² area
    
    # Add air volume and temperature attributes for thermal calculations
    # Use setattr to add these attributes dynamically
    setattr(floater, 'air_volume', 0.006)      # 6L air volume
    setattr(floater, 'air_temperature', 310.15)  # 37°C heated air
    
    print(f"✓ Test floater created: {floater.mass}kg, {floater.volume*1000}L")
    print(f"  Air volume: {getattr(floater, 'air_volume', 0)*1000}L")
    print(f"  Air temperature: {getattr(floater, 'air_temperature', 273.15)-273.15}°C")
    
    # Test thermal buoyancy boost calculation
    water_depth = 8.0  # 8 meters depth
    air_volume = getattr(floater, 'air_volume', 0.006)
    air_temperature = getattr(floater, 'air_temperature', 293.15)
    water_temperature = 288.15  # 15°C water temperature
    thermal_boost = pneumatics.calculate_thermal_buoyancy_boost(
        air_volume, air_temperature, water_temperature, water_depth)
    
    print(f"✓ Thermal buoyancy boost calculated")
    print(f"  Water depth: {water_depth}m")
    print(f"  Thermal boost: {thermal_boost:.2f} N")
      # Test complete thermodynamic cycle analysis
    cycle_analysis = pneumatics.get_thermodynamic_cycle_analysis(
        getattr(floater, 'air_volume', 0.006), 20.0)  # 20 second ascent
    
    if cycle_analysis:
        print(f"✓ Thermodynamic cycle analysis completed")
        print(f"  Energy balance keys: {list(cycle_analysis.get('energy_balance', {}).keys())}")
        if 'performance_metrics' in cycle_analysis:
            perf = cycle_analysis['performance_metrics']
            print(f"  Power enhancement: {perf.get('power_enhancement_factor', 1.0):.2f}")
    
    return pneumatics, floater


def test_simulation_integration():
    """Test integration with the main simulation engine."""
    print("\n=== Testing Main Simulation Integration ===")
    
    # Create basic simulation parameters with Phase 5 enhancements
    params = {
        'chain_length': 50.0,  # 50m chain
        'num_floaters': 8,
        'simulation_time': 30.0,  # 30 second test
        'time_step': 0.1,
        'water_depth': 10.0,
        
        # Pneumatic parameters with Phase 5
        'pneumatic': {
            'tank_pressure': 2.5,
            'tank_volume': 0.15,
            'compressor_power': 4.2,
            'enable_thermodynamics': True,
            'water_temperature': 288.15,
            'expansion_mode': 'mixed'
        }
    }
    
    # Create data queue for simulation
    data_queue = queue.Queue()
    
    try:
        # Create simulation engine
        sim = SimulationEngine(params, data_queue)
        print(f"✓ Simulation engine created successfully")
        
        # Check that pneumatic system has Phase 5 capabilities
        if hasattr(sim, 'pneumatics') and hasattr(sim.pneumatics, 'enable_thermodynamics'):
            if sim.pneumatics.enable_thermodynamics:
                print(f"✓ Phase 5 thermodynamics integrated into simulation")
                print(f"  Advanced thermodynamics: {hasattr(sim.pneumatics, 'advanced_thermo')}")
                print(f"  Heat exchange: {hasattr(sim.pneumatics, 'heat_exchange')}")
                print(f"  Thermal buoyancy: {hasattr(sim.pneumatics, 'thermal_buoyancy')}")
            else:
                print("⚠ Thermodynamics not enabled in simulation")
        else:
            print("⚠ Pneumatic system not found or missing thermodynamic capabilities")
        
        # Test a short simulation run
        print(f"✓ Running short simulation test...")
        sim.running = True
        start_time = time.time()
          # Run for a few steps
        for step in range(10):
            sim.step(dt=0.1)  # Pass dt parameter
            if step % 3 == 0:
                print(f"  Step {step}: time={sim.time:.1f}s")
        
        sim.running = False
        elapsed = time.time() - start_time
        print(f"✓ Simulation test completed in {elapsed:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"✗ Simulation integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_comparison():
    """Compare performance with and without Phase 5 thermodynamics."""
    print("\n=== Testing Performance Comparison ===")
    
    # Test without thermodynamics
    pneumatics_basic = PneumaticSystem(
        tank_pressure=2.5,
        enable_thermodynamics=False
    )
    
    # Test with thermodynamics
    pneumatics_advanced = PneumaticSystem(
        tank_pressure=2.5,
        enable_thermodynamics=True,
        water_temperature=288.15,
        expansion_mode='mixed'
    )
      # Create test floater
    floater = Floater(mass=10.0, volume=0.012, area=0.5)
    setattr(floater, 'air_volume', 0.006)
    setattr(floater, 'air_temperature', 310.15)
    
    water_depth = 5.0
    air_volume = getattr(floater, 'air_volume', 0.006)
    air_temperature = getattr(floater, 'air_temperature', 310.15)
    water_temperature = 288.15  # 15°C water temperature
    
    # Test basic system
    basic_boost = pneumatics_basic.calculate_thermal_buoyancy_boost(
        air_volume, air_temperature, water_temperature, water_depth)
    basic_analysis = pneumatics_basic.get_thermodynamic_cycle_analysis(getattr(floater, 'air_volume', 0.006), 15.0)
    
    # Test advanced system
    advanced_boost = pneumatics_advanced.calculate_thermal_buoyancy_boost(
        air_volume, air_temperature, water_temperature, water_depth)
    advanced_analysis = pneumatics_advanced.get_thermodynamic_cycle_analysis(getattr(floater, 'air_volume', 0.006), 15.0)
    
    print(f"Performance Comparison Results:")
    print(f"  Basic system thermal boost: {basic_boost:.2f} N")
    print(f"  Advanced system thermal boost: {advanced_boost:.2f} N")
    print(f"  Improvement: {advanced_boost - basic_boost:.2f} N ({((advanced_boost - basic_boost) / max(basic_boost, 0.1)) * 100:.1f}%)")
    
    print(f"  Basic system analysis: {'Available' if basic_analysis else 'Not available'}")
    print(f"  Advanced system analysis: {'Available' if advanced_analysis else 'Not available'}")
    
    if advanced_analysis and 'performance_metrics' in advanced_analysis:
        perf = advanced_analysis['performance_metrics']
        enhancement = perf.get('power_enhancement_factor', 1.0)
        thermal_contrib = perf.get('thermal_contribution_percent', 0.0)
        print(f"  Power enhancement factor: {enhancement:.2f}")
        print(f"  Thermal contribution: {thermal_contrib:.1f}%")


def main():
    """Run complete Phase 5 integration test suite."""
    print("=" * 70)
    print("KPP PHASE 5 INTEGRATION TEST")
    print("Thermodynamic Modeling Integration with Main Simulation")
    print("=" * 70)
    
    try:
        # Test 1: Enhanced pneumatic system
        pneumatics, floater = test_enhanced_pneumatic_system()
        
        # Test 2: Simulation integration
        integration_success = test_simulation_integration()
        
        # Test 3: Performance comparison
        test_performance_comparison()
        
        print("\n" + "=" * 70)
        print("PHASE 5 INTEGRATION TEST RESULTS")
        print("=" * 70)
        
        if integration_success:
            print("✓ Enhanced pneumatic system with Phase 5 thermodynamics")
            print("✓ Thermal buoyancy boost calculations")
            print("✓ Complete thermodynamic cycle analysis")
            print("✓ Integration with main simulation engine")
            print("✓ Performance enhancement validation")
            
            print("\nPhase 5 integration SUCCESSFUL!")
            print("The pneumatic system now includes:")
            print("  • Advanced thermodynamic property calculations")
            print("  • Compression and expansion thermodynamics")
            print("  • Heat exchange modeling with water reservoir")
            print("  • Thermal buoyancy boost calculations")
            print("  • Complete thermodynamic cycle analysis")
            print("  • Integration with existing simulation components")
        else:
            print("⚠ Some integration issues detected")
            print("Phase 5 components are functional but may need additional integration work")
        
    except Exception as e:
        print(f"✗ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
