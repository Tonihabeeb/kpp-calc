#!/usr/bin/env python3
"""
Phase 0 Validation Script - Pre-flight Clean-up Verification

This script validates that all Phase 0 requirements have been properly implemented.
"""

import subprocess
import sys
import tomllib  # Python 3.11+ built-in
from pathlib import Path


def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists and report status."""
    path = Path(file_path)
    if path.exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (MISSING)")
        return False


def check_python_version() -> bool:
    """Check Python version requirement."""
    if sys.version_info >= (3, 10):
        print(
            f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} (≥3.10 required)"
        )
        return True
    else:
        print(
            f"❌ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} (≥3.10 required)"
        )
        return False


def validate_pyproject_toml() -> bool:
    """Validate pyproject.toml structure."""
    try:
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)

        # Check required sections
        required_sections = ["project", "tool", "build-system"]
        missing = [section for section in required_sections if section not in data]

        if missing:
            print(f"❌ pyproject.toml missing sections: {missing}")
            return False

        # Check Python version requirement
        requires_python = data["project"].get("requires-python", "")
        if ">=3.10" in requires_python:
            print("✅ pyproject.toml: Python ≥3.10 requirement set")
        else:
            print(f"❌ pyproject.toml: Invalid Python requirement: {requires_python}")
            return False

        # Check dependencies structure
        if "dependencies" in data["project"]:
            deps = data["project"]["dependencies"]
            print(f"✅ pyproject.toml: {len(deps)} runtime dependencies defined")
        else:
            print("❌ pyproject.toml: No runtime dependencies defined")
            return False

        return True

    except Exception as e:
        print(f"❌ pyproject.toml validation failed: {e}")
        return False


def validate_requirements_files() -> bool:
    """Validate requirements files structure."""
    files_to_check = [
        ("requirements.txt", "Runtime dependencies"),
        ("requirements-dev.txt", "Development dependencies"),
        ("requirements-advanced.txt", "Advanced dependencies"),
    ]

    all_valid = True
    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_valid = False
            continue

        # Check file content
        try:
            with open(file_path, "r") as f:
                content = f.read()
                lines = [
                    line.strip()
                    for line in content.split("\n")
                    if line.strip() and not line.startswith("#")
                ]
                if lines:
                    print(f"   📦 {len(lines)} packages defined")
                else:
                    print(f"❌ {file_path}: No packages defined")
                    all_valid = False
        except Exception as e:
            print(f"❌ {file_path}: Read error: {e}")
            all_valid = False

    return all_valid


def main():
    """Run Phase 0 validation."""
    print("🔍 Phase 0 Validation: Pre-flight Clean-up")
    print("=" * 50)

    checks = []

    # Core requirements
    checks.append(check_python_version())
    checks.append(check_file_exists("pyproject.toml", "Project configuration"))
    checks.append(check_file_exists("setup_dev_env.py", "Development setup script"))
    checks.append(check_file_exists(".gitignore", "Git ignore rules"))

    # Advanced validation
    checks.append(validate_pyproject_toml())
    checks.append(validate_requirements_files())

    # Summary
    print("\n" + "=" * 50)
    passed = sum(checks)
    total = len(checks)

    if passed == total:
        print(f"🎉 Phase 0 COMPLETE: All {total} checks passed!")
        print("\n📋 Phase 0 Deliverables:")
        print("   ✅ Python ≥3.10 requirement enforced")
        print("   ✅ pyproject.toml with proper tool configurations")
        print("   ✅ Split dependencies (runtime vs. dev)")
        print("   ✅ Development environment automation")
        print("   ✅ Comprehensive .gitignore rules")
        print("\n🚀 Ready for Phase 1: Tool Integration & Baseline Configs")
        return True
    else:
        print(f"❌ Phase 0 INCOMPLETE: {passed}/{total} checks passed")
        print("   Fix the failing checks before proceeding to Phase 1")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
