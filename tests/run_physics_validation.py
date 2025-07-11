#!/usr/bin/env python3
"""
Run comprehensive physics validation tests for the KPP simulator.
"""

import os
import sys
import pytest
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'logs/validation_test/physics_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run the physics validation tests"""
    logger.info("Starting physics validation tests...")
    
    # Ensure we're in the project root
    if not os.path.exists('tests/validation/physics_validation.py'):
        logger.error("Please run this script from the project root directory")
        sys.exit(1)
    
    # Run tests with detailed output
    args = [
        'tests/validation/physics_validation.py',
        '-v',  # Verbose output
        '--capture=no',  # Show print statements
        '-s',  # Don't capture stdout
        '--tb=short',  # Shorter traceback format
        '--disable-warnings',  # Disable warning capture
        '-l',  # Show local variables in tracebacks
    ]
    
    logger.info("Running tests with arguments: %s", ' '.join(args))
    
    try:
        exit_code = pytest.main(args)
        
        if exit_code == 0:
            logger.info("All physics validation tests passed successfully!")
        else:
            logger.error("Some tests failed. Please check the output above.")
        
        return exit_code
        
    except Exception as e:
        logger.error("Error running tests: %s", str(e))
        return 1

if __name__ == '__main__':
    sys.exit(main()) 