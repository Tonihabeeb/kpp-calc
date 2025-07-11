"""
Test runner for Phase 4 integration tests
Executes all test suites for Phase 4 components
"""

import unittest
import sys
import logging
from datetime import datetime

# Import test suites
from test_phase4_battery_storage import TestBatteryStorageSystem
from test_phase4_grid_services import TestGridServicesCoordinator
from test_phase4_economic import TestEconomicOptimization
from test_phase4_demand_response import TestDemandResponse

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'phase4_test_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )

def run_test_suite():
    """Run all Phase 4 test suites"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestBatteryStorageSystem))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestGridServicesCoordinator))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEconomicOptimization))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDemandResponse))
    
    # Create test runner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run tests
    result = runner.run(suite)
    
    return result

def main():
    """Main entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Phase 4 integration tests")
    
    try:
        # Run tests
        result = run_test_suite()
        
        # Log results
        logger.info("Test execution completed")
        logger.info(f"Tests run: {result.testsRun}")
        logger.info(f"Tests passed: {result.testsRun - len(result.failures) - len(result.errors)}")
        logger.info(f"Tests failed: {len(result.failures)}")
        logger.info(f"Tests errored: {len(result.errors)}")
        
        # Log failures and errors
        if result.failures:
            logger.error("Test failures:")
            for failure in result.failures:
                logger.error(f"{failure[0]}: {failure[1]}")
        
        if result.errors:
            logger.error("Test errors:")
            for error in result.errors:
                logger.error(f"{error[0]}: {error[1]}")
        
        # Set exit code
        if result.wasSuccessful():
            logger.info("All tests passed successfully")
            sys.exit(0)
        else:
            logger.error("Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}", exc_info=True)
        sys.exit(2)

if __name__ == '__main__':
    main() 