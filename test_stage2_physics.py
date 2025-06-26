#!/usr/bin/env python3
"""
Stage 2 Enhanced Physics Integration Test
Tests H1, H2, H3 physics modules integration into the KPP simulator.
"""

import sys
import os
import time
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.engine import SimulationEngine
from simulation.physics.nanobubble_physics import NanobubblePhysics
from simulation.physics.thermal_physics import ThermalPhysics
from simulation.physics.pulse_controller import PulseController

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_h1_nanobubble_physics():
    """Test H1 nanobubble physics implementation and effects."""
    logger.info("Testing H1 Nanobubble Physics...")
    
    # Test parameters with H1 enabled
    params = {
        'num_floaters': 4,
        'time_step': 0.1,
        'h1_active': True,
        'h1_bubble_fraction': 0.1,  # 10% nanobubble fraction
        'h1_drag_reduction': 0.2,   # 20% drag reduction
        'h1_density_reduction': 0.05,  # 5% density reduction
        'floater_volume': 0.3,
        'floater_mass_empty': 18.0,
        'water_temperature': 293.15,
        'ambient_temperature': 293.15
    }
    
    # Create simulation engine
    engine = SimulationEngine(params, data_queue=None)
    
    # Verify nanobubble physics module is initialized
    assert hasattr(engine, 'nanobubble_physics'), "Nanobubble physics module not initialized"
    assert engine.nanobubble_physics.h1_enabled == True, "H1 should be enabled"
    
    # Test nanobubble effects on a floater
    floater = engine.floaters[0]
    floater.set_filled(True)  # Make floater buoyant
    floater.velocity = 2.0    # Set upward velocity
    
    # Get baseline forces without nanobubbles
    engine.nanobubble_physics.h1_enabled = False
    baseline_drag = floater.compute_drag_force()
    baseline_buoyancy = floater.compute_buoyant_force()
    
    # Enable nanobubbles and test effects
    engine.nanobubble_physics.h1_enabled = True
    
    # Apply enhanced physics through simulation step
    enhanced_physics = {
        'nanobubble': engine.nanobubble_physics,
        'thermal': engine.thermal_physics,
        'pulse_controller': engine.pulse_controller
    }
    
    # Update floater with enhanced physics
    floater._apply_enhanced_physics(enhanced_physics, 0.1)
    
    # Check effects
    enhanced_drag = floater.compute_drag_force()
    enhanced_buoyancy = floater.compute_buoyant_force()
    
    logger.info(f"H1 Effects - Baseline drag: {baseline_drag:.2f}N, Enhanced: {enhanced_drag:.2f}N")
    logger.info(f"H1 Effects - Baseline buoyancy: {baseline_buoyancy:.2f}N, Enhanced: {enhanced_buoyancy:.2f}N")
    
    # Verify drag reduction
    assert abs(enhanced_drag) < abs(baseline_drag), "H1 should reduce drag force"
    
    logger.info("✅ H1 Nanobubble Physics test passed!")
    return True

def test_h2_thermal_physics():
    """Test H2 thermal physics implementation and effects."""
    logger.info("Testing H2 Thermal Physics...")
    
    # Test parameters with H2 enabled
    params = {
        'num_floaters': 4,
        'time_step': 0.1,
        'h2_active': True,
        'h2_thermal_coefficient': 0.0002,
        'h2_heat_capacity_ratio': 1.4,
        'h2_heat_transfer_coeff': 50.0,
        'water_temperature': 303.15,  # 30°C (warmer water)
        'ambient_temperature': 293.15,  # 20°C
        'floater_volume': 0.3,
        'floater_mass_empty': 18.0
    }
    
    # Create simulation engine
    engine = SimulationEngine(params, data_queue=None)
    
    # Verify thermal physics module is initialized
    assert hasattr(engine, 'thermal_physics'), "Thermal physics module not initialized"
    assert engine.thermal_physics.h2_enabled == True, "H2 should be enabled"
    
    # Test thermal effects on an ascending floater
    floater = engine.floaters[0]
    floater.set_filled(True)    # Make floater buoyant
    floater.velocity = 2.0      # Set upward velocity (ascending)
    floater.position = 5.0      # Mid-tank position
    
    # Get baseline buoyancy without thermal effects
    engine.thermal_physics.h2_enabled = False
    baseline_buoyancy = floater.compute_buoyant_force()
    
    # Enable thermal effects
    engine.thermal_physics.h2_enabled = True
    
    # Apply enhanced physics
    enhanced_physics = {
        'nanobubble': engine.nanobubble_physics,
        'thermal': engine.thermal_physics,
        'pulse_controller': engine.pulse_controller
    }
    
    floater._apply_enhanced_physics(enhanced_physics, 0.1)
    enhanced_buoyancy = floater.compute_buoyant_force()
    
    logger.info(f"H2 Effects - Baseline buoyancy: {baseline_buoyancy:.2f}N, Enhanced: {enhanced_buoyancy:.2f}N")
    
    # Verify thermal boost for ascending floater
    assert enhanced_buoyancy > baseline_buoyancy, "H2 should boost buoyancy for ascending floaters"
    
    logger.info("✅ H2 Thermal Physics test passed!")
    return True

def test_h3_pulse_controller():
    """Test H3 pulse controller implementation and effects."""
    logger.info("Testing H3 Pulse Controller...")
    
    # Test parameters with H3 enabled
    params = {
        'num_floaters': 4,
        'time_step': 0.1,
        'h3_active': True,
        'h3_pulse_duration': 2.0,
        'h3_coast_duration': 3.0,
        'h3_clutch_threshold': 0.1,
        'h3_torque_modulation': 0.8,
        'h3_efficiency_boost': 0.05,
        'floater_volume': 0.3,
        'floater_mass_empty': 18.0,
        'generator_torque': 500.0
    }
    
    # Create simulation engine
    engine = SimulationEngine(params, data_queue=None)
    
    # Verify pulse controller is initialized
    assert hasattr(engine, 'pulse_controller'), "Pulse controller module not initialized"
    assert engine.pulse_controller.state.enabled == True, "H3 should be enabled"
    
    # Test pulse cycle timing
    initial_phase = engine.pulse_controller.get_current_phase()
    logger.info(f"Initial pulse phase: {initial_phase}")
    
    # Simulate multiple time steps to test phase transitions
    total_time = 0.0
    phase_changes = []
    
    for i in range(60):  # 6 seconds of simulation
        current_phase = engine.pulse_controller.get_current_phase()
        if i == 0 or current_phase != phase_changes[-1][1] if phase_changes else True:
            phase_changes.append((total_time, current_phase))
            
        # Step the pulse controller
        engine.pulse_controller.update(total_time, 0.0, 500.0, 0.1)
        total_time += 0.1
    
    logger.info("Pulse phase changes:")
    for time_point, phase in phase_changes:
        logger.info(f"  t={time_point:.1f}s: {phase}")
    
    # Verify we have both pulse and coast phases
    phases = [phase for _, phase in phase_changes]
    assert 'pulse' in phases, "Should have pulse phases"
    assert 'coast' in phases, "Should have coast phases"
    
    logger.info("✅ H3 Pulse Controller test passed!")
    return True

def test_integrated_simulation():
    """Test integrated simulation with all H1, H2, H3 physics enabled."""
    logger.info("Testing Integrated H1+H2+H3 Simulation...")
    
    # Parameters with all enhancements enabled
    params = {
        'num_floaters': 4,
        'time_step': 0.1,
        # H1 Nanobubbles
        'h1_active': True,
        'h1_bubble_fraction': 0.05,
        'h1_drag_reduction': 0.15,
        'h1_density_reduction': 0.03,
        # H2 Thermal
        'h2_active': True,
        'h2_thermal_coefficient': 0.0001,
        'water_temperature': 298.15,  # 25°C
        'ambient_temperature': 293.15,  # 20°C
        # H3 Pulse Controller
        'h3_active': True,
        'h3_pulse_duration': 2.0,
        'h3_coast_duration': 2.0,
        'h3_efficiency_boost': 0.1,
        # Base parameters
        'floater_volume': 0.3,
        'floater_mass_empty': 18.0,
        'generator_torque': 500.0,
        'sprocket_radius': 1.0
    }
    
    # Create simulation engine
    engine = SimulationEngine(params, data_queue=None)
    
    # Verify all modules are enabled
    assert engine.nanobubble_physics.h1_enabled == True, "H1 should be enabled"
    assert engine.thermal_physics.h2_enabled == True, "H2 should be enabled"
    assert engine.pulse_controller.state.enabled == True, "H3 should be enabled"
    
    # Run simulation for several steps
    logger.info("Running integrated simulation with H1+H2+H3...")
    
    start_time = time.time()
    for step in range(50):  # 5 seconds of simulation
        try:
            engine.step(0.1)
            
            if step % 10 == 0:  # Log every second
                logger.info(f"Step {step}: t={engine.time:.1f}s, "
                           f"chain_v={getattr(engine.physics_engine, 'v_chain', 0):.2f}m/s")
                
                # Check floater states
                for i, floater in enumerate(engine.floaters):
                    if hasattr(floater, '_pulse_phase'):
                        phase = floater._pulse_phase
                        logger.info(f"  Floater {i}: pos={floater.position:.2f}m, "
                                   f"vel={floater.velocity:.2f}m/s, phase={phase}")
                                   
        except Exception as e:
            logger.error(f"Simulation step {step} failed: {e}")
            return False
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    logger.info(f"Simulation completed successfully in {elapsed:.2f}s")
    logger.info(f"Final simulation time: {engine.time:.1f}s")
    
    # Basic checks
    assert engine.time > 0, "Simulation should advance in time"
    assert len(engine.floaters) == 4, "Should maintain correct number of floaters"
    
    logger.info("✅ Integrated H1+H2+H3 simulation test passed!")
    return True

def main():
    """Run all Stage 2 physics integration tests."""
    logger.info("="*60)
    logger.info("KPP Simulator Stage 2 Enhanced Physics Integration Test")
    logger.info("="*60)
    
    tests = [
        test_h1_nanobubble_physics,
        test_h2_thermal_physics,
        test_h3_pulse_controller,
        test_integrated_simulation
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_func.__name__} PASSED")
            else:
                failed += 1
                logger.error(f"❌ {test_func.__name__} FAILED")
        except Exception as e:
            failed += 1
            logger.error(f"❌ {test_func.__name__} FAILED with exception: {e}")
        
        logger.info("-" * 40)
    
    logger.info("="*60)
    logger.info(f"Stage 2 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All Stage 2 Enhanced Physics tests PASSED!")
        logger.info("Stage 2 implementation is ready for frontend integration.")
        return True
    else:
        logger.error("❌ Some tests failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
