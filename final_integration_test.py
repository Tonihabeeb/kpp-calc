#!/usr/bin/env python3
"""
Final Integration Test for KPP Simulator Stage 1 & 2 Completion
Tests all backend components and physics integration before Stage 3
"""

import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import queue
from typing import Any, Dict


def test_imports():
    """Test 1: Verify all required imports work"""
    print("=" * 60)
    print("TEST 1: IMPORT VERIFICATION")
    print("=" * 60)

    try:
        from simulation.engine import SimulationEngine

        print("✓ SimulationEngine import successful")

        from config.parameter_schema import (
            PARAM_SCHEMA,
            get_default_parameters,
            validate_parameter,
            validate_parameters,
        )

        print("✓ Parameter schema imports successful")

        from simulation.physics.nanobubble_physics import NanobubblePhysics
        from simulation.physics.pulse_controller import PulseController
        from simulation.physics.thermal_physics import ThermalPhysics

        print("✓ Physics modules import successful")

        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_parameter_validation():
    """Test 2: Parameter schema validation"""
    print("\n" + "=" * 60)
    print("TEST 2: PARAMETER VALIDATION")
    print("=" * 60)

    try:
        from config.parameter_schema import get_default_parameters, validate_parameters

        # Test valid parameters
        valid_params = {
            "time_step": 0.05,
            "num_floaters": 3,
            "nanobubble_frac": 0.1,
            "h1_enabled": True,
            "thermal_efficiency": 0.8,
            "pulse_enabled": True,
        }

        validated = validate_parameters(valid_params)
        print(f"✓ Valid parameters accepted: {len(validated)} params")

        # Test invalid parameters
        try:
            invalid_params = {"time_step": -1, "num_floaters": "invalid"}
            validate_parameters(invalid_params)
            print("✗ Invalid parameters incorrectly accepted")
            return False
        except ValueError:
            print("✓ Invalid parameters correctly rejected")

        # Test defaults
        defaults = get_default_parameters()
        print(f"✓ Default parameters retrieved: {len(defaults)} defaults")

        return True
    except Exception as e:
        print(f"✗ Parameter validation failed: {e}")
        return False


def test_physics_modules():
    """Test 3: Individual physics modules"""
    print("\n" + "=" * 60)
    print("TEST 3: PHYSICS MODULES")
    print("=" * 60)

    try:
        from simulation.physics.nanobubble_physics import NanobubblePhysics
        from simulation.physics.pulse_controller import PulseController
        from simulation.physics.thermal_physics import ThermalPhysics

        # Test H1 Nanobubbles
        h1 = NanobubblePhysics(enabled=True, nanobubble_fraction=0.1)
        h1.update(0.1)
        print(
            f"✓ H1 Nanobubbles: Active={h1.active}, Power={h1.power_consumption:.1f}W"
        )

        # Test H2 Thermal
        h2 = ThermalPhysics(enabled=True, thermal_coefficient=0.05)
        h2.update(0.1, 295.0)  # 22°C
        print(f"✓ H2 Thermal: Active={h2.active}, Boost={h2.buoyancy_multiplier:.3f}")

        # Test H3 Pulse
        h3 = PulseController(enabled=True, pulse_duration=3.0, coast_duration=2.0)
        h3.update(0.1, 0.1)  # current_time=0.1, dt=0.1
        print(f"✓ H3 Pulse: Active={h3.active}, Clutch={h3.clutch_engaged}")

        return True
    except Exception as e:
        print(f"✗ Physics modules failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_engine_integration():
    """Test 4: Full engine integration with physics"""
    print("\n" + "=" * 60)
    print("TEST 4: ENGINE INTEGRATION")
    print("=" * 60)

    try:
        from simulation.engine import SimulationEngine

        # Test parameters with all physics enabled
        test_params = {
            "time_step": 0.1,
            "num_floaters": 3,
            "h1_enabled": True,
            "nanobubble_frac": 0.05,
            "h2_enabled": True,
            "thermal_efficiency": 0.8,
            "thermal_coeff": 0.1,
            "h3_enabled": True,
            "pulse_enabled": True,
            "pulse_duration": 3.0,
            "coast_duration": 2.0,
        }

        # Create engine
        data_queue = queue.Queue()
        engine = SimulationEngine(test_params, data_queue)
        print("✓ Engine created successfully")

        # Check physics activation
        print(f"   - H1 Nanobubbles: {engine.h1_nanobubbles_active}")
        print(f"   - H2 Thermal: {engine.h2_thermal_active}")
        print(f"   - H3 Pulse: {engine.h3_pulse_active}")
        print(f"   - Enhanced Physics: {engine.enhanced_physics_enabled}")

        if not (
            engine.h1_nanobubbles_active
            and engine.h2_thermal_active
            and engine.h3_pulse_active
        ):
            print("✗ Not all physics modules activated")
            return False

        print("✓ All physics modules activated")
        return True
    except Exception as e:
        print(f"✗ Engine integration failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_simulation_execution():
    """Test 5: Simulation execution and output"""
    print("\n" + "=" * 60)
    print("TEST 5: SIMULATION EXECUTION")
    print("=" * 60)

    try:
        from simulation.engine import SimulationEngine

        test_params = {
            "time_step": 0.1,
            "num_floaters": 2,
            "h1_enabled": True,
            "nanobubble_frac": 0.1,
            "h2_enabled": True,
            "thermal_efficiency": 0.75,
            "h3_enabled": True,
            "pulse_enabled": True,
        }

        data_queue = queue.Queue()
        engine = SimulationEngine(test_params, data_queue)

        # Execute multiple steps
        print("Running simulation steps...")
        for i in range(10):
            engine.step(0.1)
            if i % 3 == 0:
                print(f"   Step {i+1}: t={engine.time:.1f}s")

        print("✓ Multiple simulation steps executed")

        # Test output data structure
        output = engine.get_output_data()
        required_keys = [
            "time",
            "torque",
            "power",
            "efficiency",
            "torque_components",
            "floaters",
            "physics_status",
        ]

        missing_keys = [key for key in required_keys if key not in output]
        if missing_keys:
            print(f"✗ Missing output keys: {missing_keys}")
            return False

        print("✓ Output data structure complete")
        print(f"   - Time: {output['time']:.2f}s")
        print(f"   - Power: {output['power']:.1f}W")
        print(f"   - Efficiency: {output['efficiency']:.1f}%")
        print(f"   - Floaters: {len(output['floaters'])}")

        # Verify physics status
        physics_status = output.get("physics_status", {})
        print(f"   - Physics Status: {list(physics_status.keys())}")

        return True
    except Exception as e:
        print(f"✗ Simulation execution failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test 6: Verify API endpoint functions exist"""
    print("\n" + "=" * 60)
    print("TEST 6: API ENDPOINT VERIFICATION")
    print("=" * 60)

    try:
        import app

        # Check if Flask app exists
        if not hasattr(app, "app"):
            print("✗ Flask app not found")
            return False

        # Check for required endpoints
        routes = [rule.rule for rule in app.app.url_map.iter_rules()]
        required_endpoints = ["/set_params", "/stream", "/get_output_schema"]

        missing_endpoints = [ep for ep in required_endpoints if ep not in routes]
        if missing_endpoints:
            print(f"✗ Missing endpoints: {missing_endpoints}")
            return False

        print("✓ All required API endpoints present")
        print(f"   - Available routes: {len(routes)}")
        print(f"   - Required endpoints: {required_endpoints}")

        return True
    except Exception as e:
        print(f"✗ API endpoint verification failed: {e}")
        return False


def run_final_integration_test():
    """Execute all integration tests"""
    print("KPP SIMULATOR - FINAL INTEGRATION TEST")
    print("Stage 1 & 2 Completion Verification")
    print("=" * 60)

    start_time = time.time()

    tests = [
        ("Import Verification", test_imports),
        ("Parameter Validation", test_parameter_validation),
        ("Physics Modules", test_physics_modules),
        ("Engine Integration", test_engine_integration),
        ("Simulation Execution", test_simulation_execution),
        ("API Endpoints", test_api_endpoints),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("FINAL INTEGRATION TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")
    print(f"Elapsed time: {elapsed:.2f} seconds")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Stage 1 (Backend API Foundation) - COMPLETE")
        print("✅ Stage 2 (Enhanced Physics Implementation) - COMPLETE")
        print("🚀 Ready for Stage 3 (Frontend UI Enhancement)")
        return True
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        print("❗ Issues must be resolved before proceeding to Stage 3")
        return False


if __name__ == "__main__":
    success = run_final_integration_test()
    sys.exit(0 if success else 1)
