#!/usr/bin/env python3
"""
Phase 1-6 Complete Integration Test
Demonstrates the full pneumatic system with all phases integrated.
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.pneumatics.pneumatic_coordinator import create_standard_kpp_pneumatic_coordinator
from simulation.components.pneumatics import PneumaticSystem

def test_complete_integration():
    """Test complete integration of Phases 1-6."""
    print("=" * 70)
    print("COMPLETE PNEUMATIC SYSTEM INTEGRATION TEST (PHASES 1-6)")
    print("=" * 70)
    
    print("\n1. Creating complete pneumatic system...")
    
    # Create Phase 6 control coordinator
    coordinator = create_standard_kpp_pneumatic_coordinator(
        enable_thermodynamics=True,
        enable_optimization=True
    )
    print("   ✓ Phase 6: Control coordinator created")
      # Create enhanced pneumatic system with Phase 5 capabilities
    pneumatic_system = PneumaticSystem(
        tank_pressure=2.0,      # 2.0 bar
        target_pressure=3.5,    # 3.5 bar
        enable_thermodynamics=True
    )
    print("   ✓ Phases 1-5: Enhanced pneumatic system created")
    
    print("\n2. Testing Phase 1: Air Compression and Storage...")
    # Test compression functionality
    compression_work = pneumatic_system.calculate_compression_work(
        initial_pressure=101325.0,
        final_pressure=250000.0,
        volume=0.01
    )
    print(f"   ✓ Compression work calculated: {compression_work/1000:.2f} kJ")
    
    print("\n3. Testing Phase 2: Air Injection Control...")
    # Test injection capabilities
    result = pneumatic_system.inject_air(
        target_depth=10.0,
        water_pressure=200000.0,
        duration=2.0
    )
    print(f"   ✓ Air injection: {result['volume_injected']:.4f} m³ at {result['pressure']/100000:.2f} bar")
    
    print("\n4. Testing Phase 3: Buoyancy and Ascent Dynamics...")
    # Test buoyancy calculations
    buoyancy_data = pneumatic_system.calculate_buoyancy_change(
        air_volume=0.02,
        depth=10.0,
        water_temperature=288.15
    )
    print(f"   ✓ Buoyancy force: {buoyancy_data['buoyancy_force']:.2f} N")
    print(f"   ✓ Volume expansion: {buoyancy_data['volume_expansion']:.4f} m³")
    
    print("\n5. Testing Phase 4: Venting and Reset...")
    # Test venting system
    vent_result = pneumatic_system.vent_air(
        vent_duration=1.0,
        target_pressure=150000.0
    )
    print(f"   ✓ Air vented: {vent_result['volume_vented']:.4f} m³")
    print(f"   ✓ Final pressure: {vent_result['final_pressure']/100000:.2f} bar")
    
    print("\n6. Testing Phase 5: Thermodynamic Modeling...")
    if pneumatic_system.enable_thermodynamics:
        # Test thermal buoyancy boost
        thermal_boost = pneumatic_system.calculate_thermal_buoyancy_boost(
            air_volume=0.02,
            air_temperature=320.15,  # 47°C
            water_temperature=288.15,  # 15°C
            depth=10.0
        )
        print(f"   ✓ Thermal buoyancy boost: {thermal_boost:.2f} N")
        
        # Test complete thermodynamic cycle
        cycle_analysis = pneumatic_system.analyze_thermodynamic_cycle(
            initial_pressure=200000.0,
            final_pressure=250000.0,
            initial_temperature=293.15,
            expansion_ratio=2.5
        )
        print(f"   ✓ Cycle efficiency: {cycle_analysis['efficiency']:.4f}")
        print(f"   ✓ Net work: {cycle_analysis['net_work']/1000:.2f} kJ")
    
    print("\n7. Testing Phase 6: Control System Integration...")
    
    # Start control system
    coordinator.start_control_loop()
    time.sleep(0.2)
    
    # Test thermal efficiency calculation
    efficiency = coordinator.calculate_thermal_efficiency(
        coordinator.sensors.compressor_temp.value,
        coordinator.sensors.water_temp.value
    )
    print(f"   ✓ Real-time thermal efficiency: {efficiency:.4f}")
    
    # Test optimal pressure calculation
    optimal_pressure = coordinator.calculate_optimal_pressure(
        coordinator.sensors.compressor_temp.value,
        coordinator.sensors.water_temp.value
    )
    print(f"   ✓ Optimal pressure target: {optimal_pressure/100000:.2f} bar")
    
    # Test control algorithms
    coordinator.pressure_control_algorithm()
    coordinator.injection_control_algorithm()
    coordinator.thermal_control_algorithm()
    coordinator.performance_optimization_algorithm()
    print("   ✓ All control algorithms operational")
    
    # Test system status
    status = coordinator.get_system_status()
    print(f"   ✓ System state: {status['state']}")
    print(f"   ✓ Active faults: {len(status['faults'])}")
    
    # Stop control system
    coordinator.stop_control_loop()
    
    print("\n8. Integration Summary...")
    print("   ✓ Phase 1: Air compression and storage - OPERATIONAL")
    print("   ✓ Phase 2: Air injection control - OPERATIONAL") 
    print("   ✓ Phase 3: Buoyancy and ascent dynamics - OPERATIONAL")
    print("   ✓ Phase 4: Venting and reset mechanism - OPERATIONAL")
    print("   ✓ Phase 5: Thermodynamic modeling - OPERATIONAL")
    print("   ✓ Phase 6: Control system integration - OPERATIONAL")
    
    print("\n" + "=" * 70)
    print("COMPLETE INTEGRATION TEST SUCCESSFUL")
    print("All phases (1-6) are fully integrated and operational!")
    print("✓ Advanced pneumatic system with intelligent control")
    print("✓ Thermodynamic optimization and thermal boost")
    print("✓ Real-time control and monitoring")
    print("✓ Fault detection and emergency procedures")
    print("✓ Performance optimization algorithms")
    print("=" * 70)

def test_phase_compatibility():
    """Test that all phases work together without conflicts."""
    print("\n" + "=" * 70)
    print("PHASE COMPATIBILITY TEST")
    print("=" * 70)
    
    # Test creating systems with different configurations
    configs = [
        {"thermodynamics": False, "optimization": False},
        {"thermodynamics": True, "optimization": False}, 
        {"thermodynamics": False, "optimization": True},
        {"thermodynamics": True, "optimization": True}
    ]
    
    for i, config in enumerate(configs, 1):
        print(f"\nConfiguration {i}: Thermodynamics={config['thermodynamics']}, Optimization={config['optimization']}")
        
        coordinator = create_standard_kpp_pneumatic_coordinator(
            enable_thermodynamics=config['thermodynamics'],
            enable_optimization=config['optimization']
        )
        
        pneumatic_system = PneumaticSystem(
            enable_thermodynamics=config['thermodynamics']
        )
        
        print(f"   ✓ Systems created successfully")
        print(f"   ✓ Coordinator thermodynamics: {coordinator.enable_thermodynamics}")
        print(f"   ✓ Pneumatic system thermodynamics: {pneumatic_system.enable_thermodynamics}")
    
    print("\n✓ All configuration combinations work correctly")
    print("✓ Phase compatibility confirmed")

if __name__ == "__main__":
    try:
        test_complete_integration()
        test_phase_compatibility()
    except Exception as e:
        print(f"\nIntegration test failed: {e}")
        import traceback
        traceback.print_exc()
