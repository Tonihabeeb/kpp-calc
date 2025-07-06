#!/usr/bin/env python3
"""
Quick Start Script for Code Quality Improvement - Phase 1
Automates the initial setup and formatting tasks
"""

import subprocess
import sys
import os
from pathlib import Path
import json
from datetime import datetime

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def create_config_files():
    """Create configuration files for code quality tools"""
    print("📝 Creating configuration files...")
    
    # Create pyproject.toml for Black
    pyproject_content = """[tool.black]
line-length = 88
target-version = ['py39']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # directories
  \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | build
  | dist
)/
'''
"""
    
    with open("pyproject.toml", "w") as f:
        f.write(pyproject_content)
    
    # Create .flake8 configuration
    flake8_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    .venv,
    build,
    dist,
    *.egg-info
"""
    
    with open(".flake8", "w") as f:
        f.write(flake8_content)
    
    # Create .isort.cfg
    isort_content = """[settings]
profile = black
line_length = 88
multi_line_output = 3
include_trailing_comma = True
force_grid_wrap = 0
use_parentheses = True
ensure_newline_before_comments = True
"""
    
    with open(".isort.cfg", "w") as f:
        f.write(isort_content)
    
    print("✅ Configuration files created")

def install_tools():
    """Install required code quality tools"""
    tools = [
        ("black", "Code formatter"),
        ("autopep8", "PEP 8 auto-formatter"),
        ("flake8", "Linter"),
        ("isort", "Import sorter"),
        ("autoflake", "Import cleaner")
    ]
    
    for tool, description in tools:
        if not run_command(f"{sys.executable} -m pip install {tool}", f"Installing {description}"):
            return False
    
    return True

def format_code():
    """Run code formatting tools"""
    core_dirs = ["simulation", "config", "utils"]
    core_files = ["app.py", "dash_app.py", "main.py"]
    
    # Run Black formatting
    black_targets = core_dirs + core_files
    if not run_command(f"{sys.executable} -m black {' '.join(black_targets)}", "Running Black formatter"):
        return False
    
    # Run autopep8
    if not run_command(f"{sys.executable} -m autopep8 --in-place --aggressive --aggressive {' '.join(black_targets)}", "Running autopep8"):
        return False
    
    # Run isort
    if not run_command(f"{sys.executable} -m isort {' '.join(black_targets)}", "Running isort"):
        return False
    
    return True

def clean_imports():
    """Clean up unused imports"""
    core_dirs = ["simulation", "config", "utils"]
    
    for directory in core_dirs:
        if Path(directory).exists():
            if not run_command(f"{sys.executable} -m autoflake --in-place --remove-all-unused-imports --recursive {directory}", f"Cleaning imports in {directory}"):
                return False
    
    return True

def run_quality_check():
    """Run a quick quality check to measure improvement"""
    print("📊 Running quality check...")
    
    # Count long lines
    long_lines = 0
    core_files = list(Path("simulation").rglob("*.py")) + \
                list(Path("config").rglob("*.py")) + \
                [Path("app.py"), Path("dash_app.py"), Path("main.py")]
    
    for file_path in core_files:
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        if len(line.rstrip()) > 88:
                            long_lines += 1
            except Exception:
                continue
    
    print(f"📈 Long lines remaining: {long_lines}")
    
    # Run flake8 check
    if run_command(f"{sys.executable} -m flake8 simulation config utils app.py dash_app.py main.py --count", "Running flake8 check"):
        print("✅ Code quality check completed")
        return True
    else:
        print("⚠️  Some quality issues remain")
        return False

def main():
    """Main function to start quality improvement"""
    print("🚀 Starting Code Quality Improvement - Phase 1")
    print("=" * 60)
    
    # Step 1: Install tools
    if not install_tools():
        print("❌ Tool installation failed. Exiting.")
        return False
    
    # Step 2: Create configuration files
    create_config_files()
    
    # Step 3: Format code
    if not format_code():
        print("❌ Code formatting failed. Exiting.")
        return False
    
    # Step 4: Clean imports
    if not clean_imports():
        print("❌ Import cleaning failed. Exiting.")
        return False
    
    # Step 5: Quality check
    if not run_quality_check():
        print("⚠️  Quality check completed with issues")
    else:
        print("✅ Quality check completed successfully")
    
    print("\n" + "=" * 60)
    print("🎉 Phase 1 Quick Start Completed!")
    print("=" * 60)
    print("📋 Next Steps:")
    print("1. Review the formatted code")
    print("2. Test that all functionality still works")
    print("3. Continue with Phase 2 of the roadmap")
    print("4. Check the CODE_QUALITY_IMPROVEMENT_ROADMAP.md for details")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 