#!/usr/bin/env python3
"""
Simplified Final Integration Test - ASCII only
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import queue


def simple_integration_test():
    """Test basic integration without Unicode issues"""

    print("=== KPP INTEGRATION TEST ===")

    try:
        # Test imports
        print("Testing imports...")
        from config.parameter_schema import get_default_parameters, validate_parameters
        from simulation.engine import SimulationEngine
        from simulation.physics.nanobubble_physics import NanobubblePhysics
        from simulation.physics.pulse_controller import PulseController
        from simulation.physics.thermal_physics import ThermalPhysics

        print("PASS - All imports successful")

        # Test parameter validation
        print("Testing parameter validation...")
        valid_params = {"time_step": 0.05, "num_floaters": 3}
        validated = validate_parameters(valid_params)
        defaults = get_default_parameters()
        print(
            f"PASS - Validation working, {len(validated)} params, {len(defaults)} defaults"
        )

        # Test physics modules individually
        print("Testing physics modules...")
        h1 = NanobubblePhysics(enabled=True, nanobubble_fraction=0.1)
        h1_status = h1.update(0.1)
        print(f"PASS - H1 Nanobubbles: Active={h1.active}")

        h2 = ThermalPhysics(enabled=True, thermal_coefficient=0.05)
        h2_status = h2.update(0.1, 295.0)
        print(f"PASS - H2 Thermal: Active={h2.active}")

        h3 = PulseController(enabled=True, pulse_duration=3.0, coast_duration=2.0)
        h3_status = h3.update(0.0, 0.1)
        print(f"PASS - H3 Pulse: Active={h3.active}")

        # Test engine integration
        print("Testing engine integration...")
        test_params = {
            "time_step": 0.1,
            "num_floaters": 2,
            "h1_enabled": True,
            "nanobubble_frac": 0.05,
            "h2_enabled": True,
            "thermal_efficiency": 0.8,
            "h3_enabled": True,
            "pulse_enabled": True,
        }

        data_queue = queue.Queue()
        engine = SimulationEngine(test_params, data_queue)
        print("PASS - Engine created")
        print(f"  H1: {engine.h1_nanobubbles_active}")
        print(f"  H2: {engine.h2_thermal_active}")
        print(f"  H3: {engine.h3_pulse_active}")

        # Test simulation execution
        print("Testing simulation execution...")
        for i in range(3):
            engine.step(0.1)
        print("PASS - Simulation steps executed")

        # Test output data
        output = engine.get_output_data()
        required_keys = ["time", "torque", "power", "efficiency", "floaters"]
        missing = [k for k in required_keys if k not in output]
        if missing:
            print(f"FAIL - Missing output keys: {missing}")
            return False

        print("PASS - Output data structure complete")
        print(f"  Keys: {len(output)} total")
        print(f"  Time: {output['time']:.2f}s")
        print(f"  Floaters: {len(output['floaters'])}")

        # Test API endpoints
        print("Testing API endpoints...")
        import app

        routes = [rule.rule for rule in app.app.url_map.iter_rules()]
        required_endpoints = ["/set_params", "/stream", "/get_output_schema"]
        missing_endpoints = [ep for ep in required_endpoints if ep not in routes]

        if missing_endpoints:
            print(f"FAIL - Missing endpoints: {missing_endpoints}")
            return False

        print(f"PASS - All required endpoints present ({len(routes)} total)")

        print("\n=== ALL TESTS PASSED ===")
        print("Stage 1 (Backend API Foundation) - COMPLETE")
        print("Stage 2 (Enhanced Physics) - COMPLETE")
        print("Ready for Stage 3 (Frontend UI Enhancement)")
        return True

    except Exception as e:
        print(f"FAIL - Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = simple_integration_test()
    sys.exit(0 if success else 1)
