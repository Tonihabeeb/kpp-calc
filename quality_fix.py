#!/usr/bin/env python3
"""
Code Quality Fix Script for KPP Simulator
Run this script to automatically fix code quality issues
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  COMPLETED: {description}")
            return True
        else:
            print(f"  FAILED: {description}")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"  ERROR: {description} - {e}")
        return False

def main():
    print("Running Code Quality Fixes...")
    
    # Run fixes
    fixes = [
        ("black simulation/ config/ utils/ app.py dash_app.py main.py", "Code formatting"),
        ("isort simulation/ config/ utils/ app.py dash_app.py main.py", "Import sorting"),
        ("autoflake --in-place --remove-all-unused-imports --remove-unused-variables --recursive simulation/ config/ utils/ app.py dash_app.py main.py", "Remove unused imports")
    ]
    
    all_successful = True
    for cmd, desc in fixes:
        if not run_command(cmd, desc):
            all_successful = False
    
    if all_successful:
        print("\nAll quality fixes completed!")
        print("\nRun quality_check.py to verify the fixes.")
    else:
        print("\nSome quality fixes failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
