#!/usr/bin/env python3
"""
KPP Simulator - Development Environment Setup Script

This script automates the setup of a development environment for the KPP Simulator.
It handles virtual environment creation, dependency installation, and development tool setup.

Usage:
    python setup_dev_env.py [--force] [--advanced]

Options:
    --force     : Force recreation of virtual environment if it exists
    --advanced  : Install advanced/optional dependencies
"""

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def create_virtual_environment(venv_path: Path, force: bool = False) -> None:
    """Create a virtual environment."""
    if venv_path.exists():
        if force:
            print(f"Removing existing virtual environment: {venv_path}")
            import shutil

            shutil.rmtree(venv_path)
        else:
            print(f"Virtual environment already exists: {venv_path}")
            return

    print(f"Creating virtual environment: {venv_path}")
    venv.create(venv_path, with_pip=True)


def get_pip_command(venv_path: Path) -> list[str]:
    """Get the pip command for the virtual environment."""
    if sys.platform == "win32":
        return [str(venv_path / "Scripts" / "pip.exe")]
    else:
        return [str(venv_path / "bin" / "pip")]


def install_dependencies(venv_path: Path, advanced: bool = False) -> None:
    """Install project dependencies."""
    pip_cmd = get_pip_command(venv_path)

    # Upgrade pip
    run_command(pip_cmd + ["install", "--upgrade", "pip"])

    # Install runtime dependencies
    print("Installing runtime dependencies...")
    run_command(pip_cmd + ["install", "-r", "requirements.txt"])

    # Install development dependencies
    print("Installing development dependencies...")
    run_command(pip_cmd + ["install", "-r", "requirements-dev.txt"])

    # Install advanced dependencies if requested
    if advanced:
        print("Installing advanced dependencies...")
        try:
            run_command(pip_cmd + ["install", "-r", "requirements-advanced.txt"])
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to install some advanced dependencies: {e}")

    # Install project in development mode
    print("Installing KPP Simulator in development mode...")
    run_command(pip_cmd + ["install", "-e", "."])


def setup_pre_commit(venv_path: Path) -> None:
    """Set up pre-commit hooks."""
    if sys.platform == "win32":
        pre_commit_cmd = [str(venv_path / "Scripts" / "pre-commit.exe")]
    else:
        pre_commit_cmd = [str(venv_path / "bin" / "pre-commit")]

    print("Installing pre-commit hooks...")
    try:
        run_command(pre_commit_cmd + ["install"])
        print("✅ Pre-commit hooks installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to install pre-commit hooks: {e}")


def create_activation_script() -> None:
    """Create platform-appropriate activation script."""
    if sys.platform == "win32":
        script_content = """@echo off
REM KPP Simulator Development Environment Activation Script
echo Activating KPP Simulator development environment...
call .venv\\Scripts\\activate.bat
echo ✅ KPP Simulator development environment activated!
echo.
echo Available commands:
echo   pytest                 - Run tests
echo   black .                - Format code
echo   pylint simulation/     - Lint code
echo   mypy simulation/       - Type check
echo   python app.py          - Start simulator
echo.
"""
        script_file = "activate_dev.bat"
    else:
        script_content = """#!/bin/bash
# KPP Simulator Development Environment Activation Script
echo "Activating KPP Simulator development environment..."
source .venv/bin/activate
echo "✅ KPP Simulator development environment activated!"
echo ""
echo "Available commands:"
echo "  pytest                 - Run tests"
echo "  black .                - Format code"
echo "  pylint simulation/     - Lint code"
echo "  mypy simulation/       - Type check"
echo "  python app.py          - Start simulator"
echo ""
"""
        script_file = "activate_dev.sh"

    with open(script_file, "w") as f:
        f.write(script_content)

    if not sys.platform == "win32":
        os.chmod(script_file, 0o755)

    print(f"✅ Created activation script: {script_file}")


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(
        description="Set up KPP Simulator development environment"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force recreation of virtual environment"
    )
    parser.add_argument(
        "--advanced", action="store_true", help="Install advanced dependencies"
    )
    args = parser.parse_args()

    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required")
        sys.exit(1)

    print("🚀 Setting up KPP Simulator development environment")
    print(f"Python version: {sys.version}")

    # Set up paths
    project_root = Path.cwd()
    venv_path = project_root / ".venv"

    try:
        # Create virtual environment
        create_virtual_environment(venv_path, args.force)

        # Install dependencies
        install_dependencies(venv_path, args.advanced)

        # Set up pre-commit hooks
        setup_pre_commit(venv_path)

        # Create activation script
        create_activation_script()

        print("\n✅ Development environment setup complete!")
        print("\nNext steps:")
        if sys.platform == "win32":
            print("  1. Run: activate_dev.bat")
        else:
            print("  1. Run: source activate_dev.sh")
        print("  2. Run: pytest tests/ (once tests are created)")
        print("  3. Run: python app.py (to start the simulator)")
        print("\nQuality tools available:")
        print("  - black . (code formatting)")
        print("  - isort . (import sorting)")
        print("  - pylint simulation/ (linting)")
        print("  - mypy simulation/ (type checking)")
        print("  - pytest (testing)")

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
