#!/usr/bin/env python3
"""
Test runner for KPP Simulator Observability System
Runs all unit tests and provides a summary report
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run observability tests and provide summary"""
    print("=" * 60)
    print("🧪 KPP Simulator Observability System - Test Runner")
    print("=" * 60)
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print(f"📁 Working directory: {script_dir}")
    print("🔧 Running observability unit tests...")
    print("=" * 60)
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_observability.py", 
            "-v", 
            "--tb=short"
        ], capture_output=True, text=True, check=False)
        
        # Print test output
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Print summary
        print("=" * 60)
        if result.returncode == 0:
            print("✅ All observability tests PASSED!")
            print("🎉 The observability system is working correctly.")
        else:
            print("❌ Some observability tests FAILED!")
            print("🔧 Check the output above for details.")
        
        print("=" * 60)
        
        # Additional verification
        print("🔍 Additional Verification:")
        
        # Check if observability module exists
        if os.path.exists("observability.py"):
            print("✅ observability.py - Found")
        else:
            print("❌ observability.py - Missing")
        
        # Check if client-side trace script exists
        if os.path.exists("assets/trace.js"):
            print("✅ assets/trace.js - Found")
        else:
            print("❌ assets/trace.js - Missing")
        
        # Check if test file exists
        if os.path.exists("tests/test_observability.py"):
            print("✅ tests/test_observability.py - Found")
        else:
            print("❌ tests/test_observability.py - Missing")
        
        print("=" * 60)
        
        return result.returncode
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 