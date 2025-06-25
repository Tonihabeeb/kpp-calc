#!/usr/bin/env python3
"""
Quick verification of key imports
"""

import sys
import os

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

print("Testing quick imports...")

try:
    import simulation.engine
    print("✅ Engine module")
except Exception as e:
    print(f"❌ Engine: {e}")

try:
    from app import app
    print("✅ Flask app")
except Exception as e:
    print(f"❌ Flask: {e}")

try:
    from simulation.control.integrated_control_system import IntegratedControlSystem
    print("✅ Control system")
except Exception as e:
    print(f"❌ Control: {e}")

try:
    from simulation.grid_services.grid_services_coordinator import GridServicesCoordinator
    print("✅ Grid services")
except Exception as e:
    print(f"❌ Grid services: {e}")

print("Quick test complete!")
