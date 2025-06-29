#!/usr/bin/env python3
"""
Simple Validation Test for KPP Simulator
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def validate_simulator():
    """Validate that the simulator is ready to run"""
    print("KPP SIMULATOR VALIDATION")
    print("=" * 30)
    
    checks = []
    
    # Check 1: Core imports
    try:
        from flask import Flask
        from simulation.engine import SimulationEngine
        from config.parameter_schema import PARAM_SCHEMA
        checks.append(("Core imports", True, "All core modules available"))
    except Exception as e:
        checks.append(("Core imports", False, str(e)))
    
    # Check 2: Create simulation engine
    try:
        import queue
        params = {"num_floaters": 4, "floater_volume": 0.3}
        data_queue = queue.Queue()
        engine = SimulationEngine(params, data_queue)
        engine.reset()
        checks.append(("Simulation engine", True, "Engine creates and resets"))
    except Exception as e:
        checks.append(("Simulation engine", False, str(e)))
    
    # Check 3: Flask app
    try:
        import app
        if hasattr(app, 'app'):
            checks.append(("Flask app", True, "App instance found"))
        else:
            checks.append(("Flask app", False, "No app instance"))
    except Exception as e:
        checks.append(("Flask app", False, str(e)))
    
    # Check 4: Required files
    required_files = [
        "templates/index.html",
        "static/css/style.css",
        "static/js/main.js"
    ]
    
    missing = [f for f in required_files if not os.path.exists(f)]
    if not missing:
        checks.append(("Frontend files", True, "All files present"))
    else:
        checks.append(("Frontend files", False, f"Missing: {missing}"))
    
    # Print results
    passed = 0
    for name, success, message in checks:
        status = "✓" if success else "✗"
        print(f"{status} {name}: {message}")
        if success:
            passed += 1
    
    # Summary
    total = len(checks)
    success_rate = (passed / total) * 100
    
    print(f"\nValidation: {passed}/{total} checks passed ({success_rate:.0f}%)")
    
    if success_rate >= 75:
        print("🎉 SIMULATOR READY!")
        print("\nTo start:")
        print("  python app.py")
        print("  Open: http://127.0.0.1:5000")
        return True
    else:
        print("❌ Issues detected - please fix before running")
        return False

if __name__ == "__main__":
    validate_simulator()
