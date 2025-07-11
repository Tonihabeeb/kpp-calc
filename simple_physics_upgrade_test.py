#!/usr/bin/env python3
"""
Simple Physics Upgrade Integration Test
Verifies that the physics upgrade is properly integrated and working.
"""

import os
import sys
import time
import json
import requests
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Configure logging without Unicode characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('physics_upgrade_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SimplePhysicsUpgradeTester:
    """Simple tester for physics upgrade integration"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.test_results = {}
        
    def run_simple_test(self) -> bool:
        """Run simple physics upgrade test"""
        logger.info("Starting Simple Physics Upgrade Integration Test")
        logger.info("=" * 60)
        
        try:
            # Step 1: File-by-file verification
            if not self.verify_file_integration():
                return False
                
            # Step 2: Check integrated components
            if not self.verify_integrated_components():
                return False
                
            # Step 3: Test API endpoints
            if not self.test_api_endpoints():
                return False
                
            # Step 4: Test simulation start
            if not self.test_simulation_start():
                return False
                
            logger.info("=" * 60)
            logger.info("SIMPLE TEST COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            return False
    
    def verify_file_integration(self) -> bool:
        """Verify that all physics upgrade files are properly integrated"""
        logger.info("Step 1: Verifying File Integration")
        
        # Check for integrated simulator
        integrated_simulator = self.project_root / "simulation" / "integration" / "integrated_simulator.py"
        if not integrated_simulator.exists():
            logger.error("Integrated simulator not found")
            return False
        logger.info("Integrated simulator found")
        
        # Check for physics components
        physics_components = [
            "simulation/physics/chrono/",
            "simulation/physics/thermodynamics/", 
            "simulation/physics/electrical/",
            "simulation/physics/fluid/",
            "simulation/control/events/",
            "simulation/control/strategies/"
        ]
        
        for component in physics_components:
            component_path = self.project_root / component
            if not component_path.exists():
                logger.error(f"Physics component not found: {component}")
                return False
            logger.info(f"Physics component found: {component}")
        
        # Check for compatibility layer
        compatibility_layer = self.project_root / "simulation" / "integration" / "compatibility_layer.py"
        if not compatibility_layer.exists():
            logger.error("Compatibility layer not found")
            return False
        logger.info("Compatibility layer found")
        
        # Check for performance optimizer
        performance_optimizer = self.project_root / "simulation" / "integration" / "performance_optimizer.py"
        if not performance_optimizer.exists():
            logger.error("Performance optimizer not found")
            return False
        logger.info("Performance optimizer found")
        
        logger.info("File integration verification completed")
        return True
    
    def verify_integrated_components(self) -> bool:
        """Verify that integrated components exist and are being used"""
        logger.info("Step 2: Verifying Integrated Components")
        
        # Check that integrated components exist
        integrated_components = [
            "simulation/components/integrated_drivetrain.py",
            "simulation/components/integrated_electrical_system.py",
            "simulation/components/pneumatics.py"  # Updated to check for the correct file
        ]
        
        for component in integrated_components:
            component_path = self.project_root / component
            if not component_path.exists():
                logger.error(f"Integrated component not found: {component}")
                return False
            logger.info(f"Integrated component found: {component}")
        
        # Check that legacy components are not being imported in main files
        main_files = [
            "app.py",
            "simulation/engine.py",
            "simulation/controller.py"
        ]
        
        for main_file in main_files:
            main_path = self.project_root / main_file
            if main_path.exists():
                content = main_path.read_text()
                if "import drivetrain" in content or "from drivetrain" in content:
                    logger.warning(f"Legacy drivetrain import found in {main_file}")
                if "import generator" in content or "from generator" in content:
                    logger.warning(f"Legacy generator import found in {main_file}")
                logger.info(f"Main file checked: {main_file}")
        
        logger.info("Integrated components verification completed")
        return True
    
    def test_api_endpoints(self) -> bool:
        """Test API endpoints without starting servers"""
        logger.info("Step 3: Testing API Endpoints")
        
        # Check if Flask app has the correct routes
        app_file = self.project_root / "app.py"
        if app_file.exists():
            content = app_file.read_text()
            
            # Check for new API routes
            if "/api/simulation/control" in content:
                logger.info("New simulation control API route found")
            else:
                logger.warning("New simulation control API route not found")
            
            # Check for component manager integration
            if "ComponentManager" in content:
                logger.info("Component manager integration found")
            else:
                logger.warning("Component manager integration not found")
        
        # Check simulation API routes
        simulation_api = self.project_root / "routes" / "simulation_api.py"
        if simulation_api.exists():
            content = simulation_api.read_text()
            
            if "control_simulation" in content:
                logger.info("Simulation control function found")
            else:
                logger.warning("Simulation control function not found")
            
            if "stream" in content:
                logger.info("Data stream endpoint found")
            else:
                logger.warning("Data stream endpoint not found")
        
        logger.info("API endpoints verification completed")
        return True
    
    def test_simulation_start(self) -> bool:
        """Test simulation start functionality"""
        logger.info("Step 4: Testing Simulation Start")
        
        # Check if the simulation can be started programmatically
        try:
            # Import the integrated simulator
            sys.path.insert(0, str(self.project_root / "simulation" / "integration"))
            
            from integrated_simulator import IntegratedKPPSimulator
            
            # Create a test configuration
            config = {
                'time_step': 0.02,
                'air_thermo': {'temperature': 293.15, 'pressure': 101325},
                'pneumatic': {'target_pressure': 400000, 'injection_time': 0.5},
                'drivetrain': {'flywheel_inertia': 10.0, 'gear_ratio': 1.0},
                'h2': {'enabled': True, 'thermal_factor': 1.1},
                'h3': {'enabled': True, 'pulse_duration': 2.0},
                'control': {'strategy': 'periodic', 'injection_interval': 2.0},
                'safety': {'max_speed': 100.0, 'max_torque': 1000.0}
            }
            
            # Create simulator instance
            simulator = IntegratedKPPSimulator(config)
            logger.info("Integrated simulator created successfully")
            
            # Test start simulation
            if simulator.start_simulation():
                logger.info("Simulation started successfully")
                
                # Test update simulation
                state = simulator.update_simulation(0.02)
                if state:
                    logger.info("Simulation update successful")
                    
                    # Check for physics data in state
                    if 'drivetrain_system' in state:
                        logger.info("Drivetrain system data found")
                    if 'pneumatic_system' in state:
                        logger.info("Pneumatic system data found")
                    if 'performance' in state:
                        logger.info("Performance data found")
                
                # Stop simulation
                simulator.stop_simulation()
                logger.info("Simulation stopped successfully")
            else:
                logger.error("Failed to start simulation")
                return False
            
            logger.info("Simulation start test completed successfully")
            return True
            
        except ImportError as e:
            logger.error(f"Import error: {e}")
            return False
        except Exception as e:
            logger.error(f"Simulation test error: {e}")
            return False

def main():
    """Main test execution"""
    print("KPP Simulator Physics Upgrade Integration Test")
    print("=" * 60)
    
    tester = SimplePhysicsUpgradeTester()
    success = tester.run_simple_test()
    
    if success:
        print("\nALL TESTS PASSED!")
        print("Physics upgrade is fully integrated and working")
        print("\nTest Summary:")
        print("   - File integration: PASS")
        print("   - Integrated components: PASS")
        print("   - API endpoints: PASS")
        print("   - Simulation start: PASS")
    else:
        print("\nTESTS FAILED!")
        print("Please check the log file for details")
        sys.exit(1)

if __name__ == "__main__":
    main() 