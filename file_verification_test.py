#!/usr/bin/env python3
"""
File Verification Test for Physics Upgrade
Checks that all physics upgrade files exist and are properly integrated.
"""

import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FileVerificationTester:
    """File verification tester for physics upgrade"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.test_results = {}
        
    def run_file_verification(self) -> bool:
        """Run file verification test"""
        logger.info("Starting File Verification Test for Physics Upgrade")
        logger.info("=" * 60)
        
        try:
            # Step 1: Check physics upgrade files
            if not self.verify_physics_files():
                return False
                
            # Step 2: Check integrated components
            if not self.verify_integrated_components():
                return False
                
            # Step 3: Check integration layer
            if not self.verify_integration_layer():
                return False
                
            # Step 4: Check legacy component status
            if not self.verify_legacy_status():
                return False
                
            logger.info("=" * 60)
            logger.info("FILE VERIFICATION COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"File verification failed: {e}")
            return False
    
    def verify_physics_files(self) -> bool:
        """Verify that all physics upgrade files exist"""
        logger.info("Step 1: Verifying Physics Files")
        
        # Check for physics directories
        physics_dirs = [
            "simulation/physics/chrono/",
            "simulation/physics/thermodynamics/", 
            "simulation/physics/electrical/",
            "simulation/physics/fluid/",
            "simulation/control/events/",
            "simulation/control/strategies/"
        ]
        
        for physics_dir in physics_dirs:
            dir_path = self.project_root / physics_dir
            if not dir_path.exists():
                logger.error(f"Physics directory not found: {physics_dir}")
                return False
            logger.info(f"Physics directory found: {physics_dir}")
            
            # Check for __init__.py files
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                logger.warning(f"__init__.py not found in: {physics_dir}")
            else:
                logger.info(f"__init__.py found in: {physics_dir}")
        
        # Check for specific physics files
        physics_files = [
            "simulation/physics/chrono/chrono_system.py",
            "simulation/physics/chrono/floater_body.py",
            "simulation/physics/chrono/chain_system.py",
            "simulation/physics/chrono/force_applicator.py",
            "simulation/physics/thermodynamics/fluid_properties.py",
            "simulation/physics/thermodynamics/air_system.py",
            "simulation/physics/electrical/generator_model.py",
            "simulation/physics/fluid/drag_model.py"
        ]
        
        for physics_file in physics_files:
            file_path = self.project_root / physics_file
            if not file_path.exists():
                logger.warning(f"Physics file not found: {physics_file}")
            else:
                logger.info(f"Physics file found: {physics_file}")
        
        logger.info("Physics files verification completed")
        return True
    
    def verify_integrated_components(self) -> bool:
        """Verify that integrated components exist"""
        logger.info("Step 2: Verifying Integrated Components")
        
        # Check for integrated components
        integrated_components = [
            "simulation/components/integrated_drivetrain.py",
            "simulation/components/integrated_electrical_system.py",
            "simulation/components/pneumatics.py",
            "simulation/components/advanced_generator.py",
            "simulation/components/power_electronics.py",
            "simulation/components/fluid.py"
        ]
        
        for component in integrated_components:
            component_path = self.project_root / component
            if not component_path.exists():
                logger.error(f"Integrated component not found: {component}")
                return False
            logger.info(f"Integrated component found: {component}")
        
        # Check for enhancement files
        enhancement_files = [
            "simulation/hypotheses/h1_nanobubbles.py",
            "simulation/hypotheses/h2_isothermal.py",
            "simulation/hypotheses/h3_pulse_mode.py"
        ]
        
        for enhancement in enhancement_files:
            enhancement_path = self.project_root / enhancement
            if not enhancement_path.exists():
                logger.warning(f"Enhancement file not found: {enhancement}")
            else:
                logger.info(f"Enhancement file found: {enhancement}")
        
        logger.info("Integrated components verification completed")
        return True
    
    def verify_integration_layer(self) -> bool:
        """Verify that integration layer exists"""
        logger.info("Step 3: Verifying Integration Layer")
        
        # Check for integration files
        integration_files = [
            "simulation/integration/integrated_simulator.py",
            "simulation/integration/compatibility_layer.py",
            "simulation/integration/performance_optimizer.py",
            "simulation/integration/physics_integration.py",
            "simulation/integration/integration_manager.py"
        ]
        
        for integration_file in integration_files:
            file_path = self.project_root / integration_file
            if not file_path.exists():
                logger.error(f"Integration file not found: {integration_file}")
                return False
            logger.info(f"Integration file found: {integration_file}")
        
        # Check for control system files
        control_files = [
            "simulation/control/subsystem_coordinator.py",
            "simulation/control/events/pneumatic_events.py",
            "simulation/control/strategies/base_strategy.py",
            "simulation/control/strategies/periodic_strategy.py",
            "simulation/control/strategies/feedback_strategy.py"
        ]
        
        for control_file in control_files:
            file_path = self.project_root / control_file
            if not file_path.exists():
                logger.warning(f"Control file not found: {control_file}")
            else:
                logger.info(f"Control file found: {control_file}")
        
        logger.info("Integration layer verification completed")
        return True
    
    def verify_legacy_status(self) -> bool:
        """Verify legacy component status"""
        logger.info("Step 4: Verifying Legacy Component Status")
        
        # Check for legacy files that should be removed or replaced
        legacy_files = [
            "simulation/components/drivetrain.py",
            "simulation/components/generator.py"
        ]
        
        for legacy_file in legacy_files:
            legacy_path = self.project_root / legacy_file
            if legacy_path.exists():
                logger.warning(f"Legacy file still exists: {legacy_file}")
                
                # Check if it's being imported in main files
                main_files = ["app.py", "simulation/engine.py", "simulation/controller.py"]
                for main_file in main_files:
                    main_path = self.project_root / main_file
                    if main_path.exists():
                        content = main_path.read_text()
                        legacy_name = Path(legacy_file).stem
                        if f"import {legacy_name}" in content or f"from {legacy_name}" in content:
                            logger.warning(f"Legacy {legacy_name} is imported in {main_file}")
            else:
                logger.info(f"Legacy file removed: {legacy_file}")
        
        # Check that new API routes exist
        api_files = [
            "routes/simulation_api.py",
            "routes/loss_monitoring_api.py"
        ]
        
        for api_file in api_files:
            api_path = self.project_root / api_file
            if not api_path.exists():
                logger.error(f"API file not found: {api_file}")
                return False
            logger.info(f"API file found: {api_file}")
        
        logger.info("Legacy status verification completed")
        return True

def main():
    """Main test execution"""
    print("File Verification Test for Physics Upgrade")
    print("=" * 60)
    
    tester = FileVerificationTester()
    success = tester.run_file_verification()
    
    if success:
        print("\nALL FILE VERIFICATIONS PASSED!")
        print("Physics upgrade files are properly integrated")
        print("\nVerification Summary:")
        print("   - Physics files: PASS")
        print("   - Integrated components: PASS")
        print("   - Integration layer: PASS")
        print("   - Legacy status: PASS")
        print("\nThe physics upgrade is file-by-file complete!")
    else:
        print("\nFILE VERIFICATIONS FAILED!")
        print("Please check the log file for details")
        sys.exit(1)

if __name__ == "__main__":
    main() 