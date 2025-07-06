#!/usr/bin/env python3
"""
Code Quality Check Script for KPP Simulator
Run this script to check code quality before commits
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  PASS: {description}")
            return True
        else:
            print(f"  FAIL: {description}")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"  ERROR: {description} - {e}")
        return False

def main():
    print("Running Code Quality Checks...")
    
    # Check if tools are installed
    tools = ['black', 'flake8', 'mypy', 'isort']
    missing_tools = []
    
    for tool in tools:
        try:
            subprocess.run([tool, '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"Missing tools: {', '.join(missing_tools)}")
        print("Run: python setup_quality_tools.py")
        sys.exit(1)
    
    # Run checks
    checks = [
        ("black --check simulation/ config/ utils/ app.py dash_app.py main.py", "Code formatting"),
        ("flake8 simulation/ config/ utils/ app.py dash_app.py main.py", "Code linting"),
        ("isort --check-only simulation/ config/ utils/ app.py dash_app.py main.py", "Import sorting"),
        ("mypy simulation/ config/ utils/ app.py dash_app.py main.py", "Type checking")
    ]
    
    all_passed = True
    for cmd, desc in checks:
        if not run_command(cmd, desc):
            all_passed = False
    
    if all_passed:
        print("\nAll quality checks passed!")
        sys.exit(0)
    else:
        print("\nSome quality checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
