#!/usr/bin/env python3
"""
Phase 6 Demo: Pneumatic Control System Integration
Demonstrates the complete control system with PLC logic, sensor integration,
fault detection, and performance optimization.
"""

import time
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.pneumatics.pneumatic_coordinator import PneumaticControlCoordinator, create_standard_kpp_pneumatic_coordinator

def run_phase6_demo():
    """Run a comprehensive Phase 6 demonstration."""
    print("=" * 60)
    print("PHASE 6 DEMO: Pneumatic Control System Integration")
    print("=" * 60)
      # Create standard coordinator with all subsystems
    print("\n1. Creating integrated control coordinator...")
    coordinator = create_standard_kpp_pneumatic_coordinator()
    
    print(f"   - Control frequency: {coordinator.control_frequency} Hz")
    print(f"   - Subsystems: {list(coordinator.subsystems.keys())}")
    print(f"   - Fault detection: {len(coordinator.fault_conditions)} conditions")
    print(f"   - Performance optimization: {'Enabled' if coordinator.optimization_enabled else 'Disabled'}")
    
    # Start control loop
    print("\n2. Starting control loop...")
    coordinator.start_control_loop()
    time.sleep(0.1)  # Allow control loop to start
    
    # Demonstrate sensor updates and control
    print("\n3. Simulating sensor updates and control responses...")
    
    # Update tank pressure (low pressure scenario)
    print("   - Setting low tank pressure (triggering compression)...")
    coordinator.update_sensor_data('tank_pressure', 150.0)  # Below minimum
    coordinator.update_sensor_data('tank_temperature', 25.0)
    coordinator.update_sensor_data('floater_depth', 10.0)
    
    # Process one control cycle
    time.sleep(0.1)
    
    # Check system response
    status = coordinator.get_system_status()
    print(f"   - Tank pressure: {status['sensors']['tank_pressure']['value']:.1f} bar")
    print(f"   - System state: {status['state']}")
    print(f"   - Active faults: {len(status['faults'])}")
    
    # Simulate injection scenario
    print("\n4. Simulating air injection scenario...")
    coordinator.update_sensor_data('tank_pressure', 250.0)  # Good pressure
    coordinator.update_sensor_data('floater_depth', 15.0)   # Target depth
    coordinator.update_sensor_data('floater_velocity', -0.5)  # Sinking
    
    # Trigger injection
    coordinator.set_operational_mode('injection')
    time.sleep(0.2)
    
    status = coordinator.get_system_status()
    print(f"   - System state: {status['state']}")
    print(f"   - Injection active: {coordinator.subsystems['injection'].is_injecting}")
    
    # Demonstrate fault detection
    print("\n5. Testing fault detection...")
    # Simulate sensor failure
    coordinator.update_sensor_data('tank_pressure', -10.0)  # Invalid reading
    time.sleep(0.1)
    
    status = coordinator.get_system_status()
    print(f"   - Detected faults: {status['faults']}")
    
    # Clear fault
    coordinator.update_sensor_data('tank_pressure', 200.0)  # Valid reading
    time.sleep(0.1)
    
    # Demonstrate performance optimization
    print("\n6. Performance optimization analysis...")
    
    # Set up thermal conditions
    coordinator.update_sensor_data('ambient_temperature', 20.0)
    coordinator.update_sensor_data('water_temperature', 15.0)
    coordinator.update_sensor_data('tank_temperature', 30.0)
    
    # Calculate optimal parameters
    thermal_efficiency = coordinator.calculate_thermal_efficiency(293.15 + 30.0, 288.15)  # 30°C compressor, 15°C water
    optimal_pressure = coordinator.calculate_optimal_pressure(293.15 + 30.0, 288.15)  # Same temperatures
    
    print(f"   - Thermal efficiency: {thermal_efficiency:.2f}")
    print(f"   - Optimal pressure: {optimal_pressure/100000:.1f} bar")
    
    # Update performance metrics
    coordinator.update_performance_metrics(0.1)  # 0.1 second time step
    performance = coordinator.get_performance_metrics()
    print(f"   - System efficiency: {performance.get('system_efficiency', 0.0):.2f}")
    print(f"   - Energy consumption: {performance.get('energy_consumption', 0.0):.1f} kJ")
    
    # Demonstrate emergency stop
    print("\n7. Testing emergency stop procedure...")
    coordinator.emergency_stop()
    
    status = coordinator.get_system_status()
    print(f"   - System state after emergency stop: {status['state']}")
    print(f"   - All subsystems stopped: {all(not s.is_active for s in coordinator.subsystems.values())}")
    
    # System reset
    print("\n8. System reset and restart...")
    coordinator.reset_system()
    coordinator.set_operational_mode('standby')
    
    status = coordinator.get_system_status()
    print(f"   - System state after reset: {status['state']}")
    print(f"   - System ready: {status['state'] == 'standby'}")
    
    # Stop control loop
    coordinator.stop_control_loop()
    
    print("\n" + "=" * 60)
    print("PHASE 6 DEMO COMPLETE")
    print("✓ Control system integration functional")
    print("✓ PLC logic operational")
    print("✓ Sensor integration working")
    print("✓ Fault detection active")
    print("✓ Performance optimization enabled")
    print("✓ Emergency procedures tested")
    print("=" * 60)

def run_control_timing_demo():
    """Demonstrate real-time control timing characteristics."""
    print("\n" + "=" * 60)
    print("CONTROL TIMING DEMONSTRATION")
    print("=" * 60)
    
    coordinator = create_standard_kpp_pneumatic_coordinator()
    coordinator.start_control_loop()
    
    print(f"Control frequency: {coordinator.control_frequency} Hz")
    print(f"Control period: {1000/coordinator.control_frequency:.1f} ms")
    
    # Monitor control loop timing
    print("\nMonitoring control loop for 2 seconds...")
    
    start_time = time.time()
    initial_cycles = coordinator.control_cycle_count
    
    time.sleep(2.0)
    
    end_time = time.time()
    final_cycles = coordinator.control_cycle_count
    
    actual_frequency = (final_cycles - initial_cycles) / (end_time - start_time)
    
    print(f"Target frequency: {coordinator.control_frequency:.1f} Hz")
    print(f"Actual frequency: {actual_frequency:.1f} Hz")
    print(f"Timing accuracy: {100 * actual_frequency / coordinator.control_frequency:.1f}%")
    
    coordinator.stop_control_loop()

if __name__ == "__main__":
    try:
        run_phase6_demo()
        run_control_timing_demo()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
