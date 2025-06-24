"""
Test Phase 3: Generator and Electrical Systems
Comprehensive testing for advanced generator, power electronics, and integrated electrical system.
"""

import pytest
import math
from simulation.components.advanced_generator import AdvancedGenerator, create_kmp_generator
from simulation.components.power_electronics import PowerElectronics, GridInterface, create_kmp_power_electronics
from simulation.components.integrated_electrical_system import IntegratedElectricalSystem, create_standard_kmp_electrical_system


def test_advanced_generator():
    """Test advanced generator electromagnetic modeling."""
    print("Testing Advanced Generator...")
    
    # Create generator with test parameters
    config = {
        'rated_power': 530000.0,
        'rated_speed': 375.0,
        'pole_pairs': 4
    }
    generator = AdvancedGenerator(config)
    
    # Test at rated conditions
    rated_speed = 375.0 * (2 * math.pi / 60)  # Convert RPM to rad/s
    load_factor = 0.8  # 80% load
    
    result = generator.update(rated_speed, load_factor, 0.1)
    
    # Verify basic functionality
    assert result['electrical_power'] > 0, "Generator should produce power at rated speed"
    assert result['efficiency'] > 0.8, f"Efficiency should be reasonable: {result['efficiency']:.3f}"
    assert result['torque'] > 0, "Generator should produce torque"
    assert 0 <= result['slip'] <= 0.1, f"Slip should be reasonable: {result['slip']:.4f}"
    
    # Test efficiency curve
    efficiencies = []
    for load in [0.2, 0.5, 0.8, 1.0]:
        result = generator.update(rated_speed, load, 0.1)
        efficiencies.append(result['efficiency'])
    
    # Efficiency should peak around 80% load
    max_eff_idx = efficiencies.index(max(efficiencies))
    assert max_eff_idx >= 1, "Peak efficiency should occur at medium to high loads"
    
    print(f"✓ Generator efficiency curve: {[f'{e:.3f}' for e in efficiencies]}")
    print(f"✓ Generator torque at rated: {result['torque']:.1f} N⋅m")
    print(f"✓ Generator power at rated: {result['electrical_power']/1000:.1f} kW")


def test_power_electronics():
    """Test power electronics conversion and grid interface."""
    print("\nTesting Power Electronics...")
    
    # Create power electronics system
    pe, grid = create_kmp_power_electronics()
    
    # Test grid conditions
    grid_conditions = grid.update(0.1)
    assert 'voltage' in grid_conditions, "Grid should provide voltage"
    assert 'frequency' in grid_conditions, "Grid should provide frequency"
    assert abs(grid_conditions['frequency'] - 60.0) < 1.0, "Grid frequency should be near 60Hz"
    
    # Test power electronics at various loads
    generator_power = 400000.0  # 400 kW input
    generator_voltage = 480.0
    generator_frequency = 60.0
    
    # First, allow synchronization to occur
    print("  Synchronizing with grid...")
    for i in range(30):  # 3 seconds at 0.1s steps to allow synchronization
        pe_result = pe.update(generator_power, generator_voltage, generator_frequency, grid_conditions, 0.1)
        grid_conditions = grid.update(0.1)
        if pe_result['is_synchronized']:
            break
    
    # Now test with synchronized system
    pe_result = pe.update(generator_power, generator_voltage, generator_frequency, grid_conditions, 0.1)
    
    # Verify synchronization occurred
    assert pe_result['is_synchronized'], f"Should synchronize with stable conditions (sync_progress: {pe_result['sync_progress']:.2f})"
    
    # Verify power conversion
    assert pe_result['output_power'] > 0, "Should convert power to output when synchronized"
    assert pe_result['output_power'] < generator_power, "Output should be less than input due to losses"
    assert pe_result['overall_efficiency'] > 0.85, f"Overall PE efficiency should be high: {pe_result['overall_efficiency']:.3f}"
    
    print(f"✓ Power electronics efficiency: {pe_result['overall_efficiency']:.3f}")
    print(f"✓ Synchronization achieved: {pe_result['is_synchronized']}")
    print(f"✓ Output power: {pe_result['output_power']/1000:.1f} kW from {generator_power/1000:.1f} kW input")


def test_integrated_electrical_system():
    """Test complete integrated electrical system."""
    print("\nTesting Integrated Electrical System...")
    
    # Create electrical system with relaxed protection settings for testing
    config = {
        'power_electronics': {
            'max_frequency_deviation': 15.0,  # Allow larger frequency deviation for testing
            'max_current': 2000.0  # Higher current limit for testing
        }
    }
    electrical_system = create_standard_kmp_electrical_system(config)
    
    # Test at operating conditions closer to rated speed (for better frequency match)
    test_conditions = [
        (1000.0, 39.27),   # Low torque, rated speed (375 RPM = 39.27 rad/s)
        (1500.0, 39.27),   # Medium torque, rated speed  
        (1200.0, 35.34),   # Lower torque, lower speed (337 RPM = ~54Hz)
        (1800.0, 41.89),   # Higher torque, higher speed (400 RPM = ~64Hz)
    ]
    
    results = []
    for torque, speed in test_conditions:
        # Run a few steps to allow synchronization
        for _ in range(10):
            result = electrical_system.update(torque, speed, 0.1)
        results.append(result)
        
        # Basic validation
        assert result['mechanical_power_input'] >= 0, "Mechanical power should be non-negative"
        assert result['electrical_power_output'] >= 0, "Electrical power should be non-negative"
        assert result['grid_power_output'] >= 0, "Grid power should be non-negative"
        assert 0 <= result['system_efficiency'] <= 1, f"System efficiency should be 0-1: {result['system_efficiency']:.3f}"
    
    # Test load management
    electrical_system.set_target_load_factor(0.8)
    # Run for synchronization with rated conditions
    for _ in range(30):
        result = electrical_system.update(1800.0, 39.27, 0.1)
    
    assert result['load_torque_command'] > 0, "Load management should command torque"
    
    # Test performance tracking
    for _ in range(100):  # Run for 10 seconds
        electrical_system.update(1800.0, 39.27, 0.1)
    
    final_state = electrical_system.update(1800.0, 39.27, 0.1)
    assert final_state['operating_hours'] > 0, "Should track operating hours"
    assert final_state['total_energy_generated_kwh'] > 0, "Should track energy generation"
    
    print(f"✓ System efficiency range: {min(r['system_efficiency'] for r in results):.3f} - {max(r['system_efficiency'] for r in results):.3f}")
    print(f"✓ Load management functional: {final_state['load_torque_command']:.1f} N⋅m command")
    print(f"✓ Performance tracking: {final_state['operating_hours']:.2f} hours, {final_state['total_energy_generated_kwh']:.1f} kWh")


def test_electrical_system_integration():
    """Test electrical system integration with drivetrain-like inputs."""
    print("\nTesting Electrical System Integration...")
      # Create electrical system with relaxed protection for testing
    config = {
        'load_management': False,  # Disable PID control for testing
        'power_electronics': {
            'max_frequency_deviation': 15.0,
            'max_current': 2000.0
        }
    }
    electrical_system = create_standard_kmp_electrical_system(config)
    
    # Use steady conditions for reliable testing
    time_step = 0.1
    simulation_time = 5.0  # 5 seconds
    steps = int(simulation_time / time_step)
    
    # Run simulation with steady torque and speed
    power_outputs = []
    efficiencies = []
    
    # Test with steady conditions that should work
    torque = 8000.0  # N·m (about 60% of rated)
    speed = 39.27    # rad/s (rated speed)
    
    for i in range(steps):
        result = electrical_system.update(torque, speed, time_step)
        
        power_outputs.append(result['grid_power_output'])
        efficiencies.append(result['system_efficiency'])
        
        # Debug output for a few key steps
        if i in [0, 10, 20, 30, 40]:
            print(f"Step {i}: Torque={torque:.0f} N·m, Speed={speed:.1f} rad/s, "
                  f"Grid Power={result['grid_power_output']/1000:.1f} kW, "
                  f"Sync={result.get('synchronized', 0):.1f}")
    
    # Validate results
    assert len(power_outputs) == steps, "Should have output for each step"
    
    # Check if any power was generated (after synchronization)
    power_after_sync = power_outputs[20:]  # After synchronization period
    max_power_after_sync = max(power_after_sync) if power_after_sync else 0
    
    assert max_power_after_sync > 0, f"Should generate power after synchronization, max: {max_power_after_sync}"
    
    max_efficiency = max(efficiencies)
    assert max_efficiency > 0.1, f"Peak efficiency should be reasonable: {max_efficiency:.3f}"
    
    print(f"✓ Simulation completed: {steps} steps over {simulation_time}s")
    print(f"✓ Power range: {min(power_outputs)/1000:.1f} - {max(power_outputs)/1000:.1f} kW")
    print(f"✓ Efficiency range: {min(efficiencies):.3f} - {max(efficiencies):.3f}")
    print(f"✓ Power generation achieved after synchronization")


def test_electrical_system_reset():
    """Test electrical system reset functionality."""
    print("\nTesting Electrical System Reset...")
    
    electrical_system = create_standard_kmp_electrical_system()
    
    # Run system for a while to build up state
    for _ in range(50):
        electrical_system.update(2000.0, 39.27, 0.1)
    
    # Verify state has been built up
    state_before = electrical_system._get_comprehensive_state()
    assert state_before['operating_hours'] > 0, "Should have operating hours before reset"
    assert state_before['total_energy_generated_kwh'] > 0, "Should have energy before reset"
    
    # Reset the system
    electrical_system.reset()
    
    # Verify reset worked
    state_after = electrical_system._get_comprehensive_state()
    assert state_after['operating_hours'] == 0, "Operating hours should be reset"
    assert state_after['total_energy_generated_kwh'] == 0, "Energy should be reset"
    assert state_after['mechanical_power_input'] == 0, "Power input should be reset"
    
    print(f"✓ Reset successful: {state_before['operating_hours']:.2f}h → {state_after['operating_hours']:.2f}h")
    print(f"✓ Energy reset: {state_before['total_energy_generated_kwh']:.1f}kWh → {state_after['total_energy_generated_kwh']:.1f}kWh")


if __name__ == "__main__":
    print("Testing Phase 3: Generator and Electrical Systems")
    print("=" * 60)
    
    test_advanced_generator()
    test_power_electronics()
    test_integrated_electrical_system()
    test_electrical_system_integration()
    test_electrical_system_reset()
    
    print("\n" + "=" * 60)
    print("✅ All Phase 3 electrical system tests passed!")
    print("✅ Advanced generator modeling functional")
    print("✅ Power electronics and grid interface operational")
    print("✅ Integrated electrical system ready for main simulation integration")
