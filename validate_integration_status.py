#!/usr/bin/env python3
"""
KPP Simulator Integration Status Validation
Checks the current state of integration and identifies remaining issues.
"""

import os
import sys
import logging
import importlib
import inspect
from typing import List, Dict, Any, Tuple
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegrationValidator:
    """Validates the integration status of KPP simulator components."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.validation_results = {}
        self.critical_issues = []
        self.warnings = []
        self.successes = []
        
    def validate_imports(self) -> Dict[str, Any]:
        """Validate that all critical imports work."""
        logger.info("🔍 Validating critical imports...")
        
        import_tests = {
            "simulation.engine": "SimulationEngine",
            "config": "ConfigManager", 
            "simulation.components.floater": "Floater",
            "simulation.components.integrated_drivetrain": "IntegratedDrivetrain",
            "simulation.components.integrated_electrical_system": "IntegratedElectricalSystem",
            "simulation.components.thermal": "ThermalModel",
            "simulation.components.fluid": "Fluid",
            "simulation.components.environment": "Environment",
            "simulation.components.control": "Control",
            "simulation.components.chain": "Chain"
        }
        
        results = {"passed": [], "failed": [], "errors": []}
        
        for module_name, class_name in import_tests.items():
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, class_name):
                    results["passed"].append(f"{module_name}.{class_name}")
                    logger.info(f"✅ {module_name}.{class_name}")
                else:
                    results["failed"].append(f"{module_name}.{class_name} (class not found)")
                    logger.warning(f"⚠️  {module_name}.{class_name} - class not found")
            except ImportError as e:
                results["failed"].append(f"{module_name}.{class_name} (import failed)")
                logger.error(f"❌ {module_name}.{class_name} - import failed: {e}")
            except Exception as e:
                results["errors"].append(f"{module_name}.{class_name} (error: {e})")
                logger.error(f"💥 {module_name}.{class_name} - error: {e}")
        
        return results
    
    def validate_component_methods(self) -> Dict[str, Any]:
        """Validate that components have required methods."""
        logger.info("🔍 Validating component methods...")
        
        required_methods = ["update", "get_state", "reset"]
        component_modules = [
            "simulation.components.thermal",
            "simulation.components.fluid",
            "simulation.components.environment", 
            "simulation.components.control",
            "simulation.components.chain"
        ]
        
        results = {"passed": [], "failed": [], "missing": []}
        
        for module_name in component_modules:
            try:
                module = importlib.import_module(module_name)
                
                # Find the main component class
                component_class = None
                class_mapping = {
                    "simulation.components.thermal": "ThermalModel",
                    "simulation.components.fluid": "FluidSystem", 
                    "simulation.components.environment": "EnvironmentSystem",
                    "simulation.components.control": "Control",
                    "simulation.components.chain": "Chain"
                }
                
                expected_class = class_mapping.get(module_name)
                if expected_class:
                    component_class = getattr(module, expected_class, None)
                else:
                    # Fallback: find any class that's not a data class or config
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and not name.startswith('_') and 
                            not name.endswith('Config') and not name.endswith('State')):
                            component_class = obj
                            break
                
                if component_class:
                    missing_methods = []
                    for method in required_methods:
                        if not hasattr(component_class, method):
                            missing_methods.append(method)
                    
                    if missing_methods:
                        results["missing"].append(f"{module_name}: {missing_methods}")
                        logger.warning(f"⚠️  {module_name} - missing methods: {missing_methods}")
                    else:
                        results["passed"].append(module_name)
                        logger.info(f"✅ {module_name} - all methods present")
                else:
                    results["failed"].append(f"{module_name} - no component class found")
                    logger.error(f"❌ {module_name} - no component class found")
                    
            except ImportError as e:
                results["failed"].append(f"{module_name} - import failed: {e}")
                logger.error(f"❌ {module_name} - import failed: {e}")
            except Exception as e:
                results["failed"].append(f"{module_name} - error: {e}")
                logger.error(f"💥 {module_name} - error: {e}")
        
        return results
    
    def validate_configuration_system(self) -> Dict[str, Any]:
        """Validate configuration system consistency."""
        logger.info("🔍 Validating configuration system...")
        
        results = {"passed": [], "failed": [], "warnings": []}
        
        # Check for dual config usage
        config_patterns = [
            ("FloaterConfig", "simulation/components/floater/core.py"),
            ("LegacyFloaterConfig", "simulation/components/floater/core.py"),
            ("ConfigManager", "simulation/engine.py")
        ]
        
        for pattern, file_path in config_patterns:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                        if pattern in content:
                            results["warnings"].append(f"{file_path} uses {pattern}")
                            logger.warning(f"⚠️  {file_path} uses {pattern}")
                        else:
                            results["passed"].append(f"{file_path} - no {pattern} usage")
                except Exception as e:
                    results["failed"].append(f"{file_path} - read error: {e}")
        
        return results
    
    def validate_engine_functionality(self) -> Dict[str, Any]:
        """Validate simulation engine functionality."""
        logger.info("🔍 Validating simulation engine...")
        
        results = {"passed": [], "failed": [], "warnings": []}
        
        try:
            from simulation.engine import SimulationEngine
            
            # Test engine creation
            engine = SimulationEngine()
            results["passed"].append("Engine creation")
            logger.info("✅ Engine creation successful")
            
            # Test component initialization
            if hasattr(engine, 'grid_services'):
                results["passed"].append("Grid services initialization")
            else:
                results["warnings"].append("Grid services not initialized")
            
            if hasattr(engine, 'floater'):
                results["passed"].append("Floater initialization")
            else:
                results["warnings"].append("Floater not initialized")
            
            if hasattr(engine, 'drivetrain'):
                results["passed"].append("Drivetrain initialization")
            else:
                results["warnings"].append("Drivetrain not initialized")
            
            # Test engine methods
            if hasattr(engine, 'start') and callable(engine.start):
                results["passed"].append("Start method present")
            else:
                results["failed"].append("Start method missing")
            
            if hasattr(engine, 'stop') and callable(engine.stop):
                results["passed"].append("Stop method present")
            else:
                results["failed"].append("Stop method missing")
            
            if hasattr(engine, 'get_state') and callable(engine.get_state):
                results["passed"].append("Get state method present")
            else:
                results["failed"].append("Get state method missing")
                
        except Exception as e:
            results["failed"].append(f"Engine validation failed: {e}")
            logger.error(f"❌ Engine validation failed: {e}")
        
        return results
    
    def validate_test_coverage(self) -> Dict[str, Any]:
        """Validate test coverage."""
        logger.info("🔍 Validating test coverage...")
        
        results = {"passed": [], "failed": [], "missing": []}
        
        test_files = [
            "test_system_integration.py",
            "tests/unit/test_physics_engine.py",
            "tests/integration/test_system_integration.py",
            "tests/performance/test_performance_benchmarks.py"
        ]
        
        for test_file in test_files:
            test_path = self.project_root / test_file
            if test_path.exists():
                results["passed"].append(test_file)
                logger.info(f"✅ {test_file} exists")
            else:
                results["missing"].append(test_file)
                logger.warning(f"⚠️  {test_file} missing")
        
        return results
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation of all aspects."""
        logger.info("🚀 Starting comprehensive integration validation...")
        
        validation_results = {
            "imports": self.validate_imports(),
            "component_methods": self.validate_component_methods(),
            "configuration": self.validate_configuration_system(),
            "engine": self.validate_engine_functionality(),
            "test_coverage": self.validate_test_coverage()
        }
        
        return validation_results
    
    def generate_report(self, results: Dict[str, Any]) -> None:
        """Generate comprehensive validation report."""
        logger.info("\n" + "="*80)
        logger.info("KPP SIMULATOR INTEGRATION STATUS REPORT")
        logger.info("="*80)
        
        total_passed = 0
        total_failed = 0
        total_warnings = 0
        
        for category, category_results in results.items():
            logger.info(f"\n📋 {category.upper()}:")
            logger.info("-" * 40)
            
            passed = len(category_results.get("passed", []))
            failed = len(category_results.get("failed", []))
            warnings = len(category_results.get("warnings", []))
            missing = len(category_results.get("missing", []))
            
            total_passed += passed
            total_failed += failed
            total_warnings += warnings
            
            logger.info(f"✅ Passed: {passed}")
            logger.info(f"❌ Failed: {failed}")
            logger.info(f"⚠️  Warnings: {warnings}")
            if missing > 0:
                logger.info(f"🔍 Missing: {missing}")
            
            # Show details for failures and warnings
            if category_results.get("failed"):
                logger.info("  Failed items:")
                for item in category_results["failed"]:
                    logger.info(f"    - {item}")
            
            if category_results.get("warnings"):
                logger.info("  Warnings:")
                for item in category_results["warnings"]:
                    logger.info(f"    - {item}")
        
        # Overall summary
        logger.info(f"\n{'='*80}")
        logger.info("OVERALL SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"✅ Total Passed: {total_passed}")
        logger.info(f"❌ Total Failed: {total_failed}")
        logger.info(f"⚠️  Total Warnings: {total_warnings}")
        
        success_rate = total_passed / (total_passed + total_failed) * 100 if (total_passed + total_failed) > 0 else 0
        logger.info(f"📊 Success Rate: {success_rate:.1f}%")
        
        if total_failed == 0 and total_warnings == 0:
            logger.info(f"\n🎉 EXCELLENT! All validations passed!")
            logger.info(f"The KPP simulator is fully integrated and ready for use.")
        elif total_failed == 0:
            logger.info(f"\n✅ GOOD! All critical validations passed with some warnings.")
            logger.info(f"The KPP simulator is functional but could be improved.")
        else:
            logger.info(f"\n⚠️  ATTENTION REQUIRED! Some critical validations failed.")
            logger.info(f"Please address the failed items before using the system.")
        
        # Recommendations
        logger.info(f"\n📋 RECOMMENDATIONS:")
        if total_failed > 0:
            logger.info(f"  1. Fix all failed validations first")
        if total_warnings > 0:
            logger.info(f"  2. Address warnings to improve system quality")
        logger.info(f"  3. Run integration tests after fixes")
        logger.info(f"  4. Validate performance meets requirements")

def main():
    """Main validation function."""
    print("🔍 KPP Simulator Integration Status Validation")
    print("=" * 60)
    
    validator = IntegrationValidator()
    
    try:
        results = validator.run_comprehensive_validation()
        validator.generate_report(results)
        
        # Determine exit code based on failures
        total_failed = sum(len(cat.get("failed", [])) for cat in results.values())
        
        if total_failed == 0:
            print("\n✅ Validation completed - system is ready!")
            return 0
        else:
            print(f"\n❌ Validation completed - {total_failed} critical issues found!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error during validation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 