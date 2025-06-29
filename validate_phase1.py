#!/usr/bin/env python3
"""
Phase 1 Validation Script - Tool Integration & Baseline Configs Verification

This script validates that all Phase 1 configuration files have been properly created
and contain the expected content for professional development workflows.
"""

import sys
from pathlib import Path
from typing import List, Tuple


def check_file_exists_and_validate(
    file_path: str, description: str, required_content: List[str] = None
) -> bool:
    """Check if a file exists and optionally validate content."""
    path = Path(file_path)
    if not path.exists():
        print(f"❌ {description}: {file_path} (MISSING)")
        return False

    # Check content if specified
    if required_content:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            missing_content = []
            for required in required_content:
                if required not in content:
                    missing_content.append(required)

            if missing_content:
                print(f"❌ {description}: {file_path} (Missing: {missing_content})")
                return False
        except Exception as e:
            print(f"❌ {description}: {file_path} (Read error: {e})")
            return False

    print(f"✅ {description}: {file_path}")
    return True


def validate_pylint_config() -> bool:
    """Validate PyLint configuration."""
    required_sections = [
        "[MASTER]",
        "[MESSAGES CONTROL]",
        "[FORMAT]",
        "disable=",
        "extension-pkg-whitelist=numpy",
    ]
    return check_file_exists_and_validate(
        ".pylintrc", "PyLint configuration", required_sections
    )


def validate_mypy_config() -> bool:
    """Validate MyPy configuration."""
    required_content = [
        "[mypy]",
        "python_version = 3.10",
        "ignore_missing_imports = True",
        "[mypy-numpy.*]",
    ]
    return check_file_exists_and_validate(
        "mypy.ini", "MyPy configuration", required_content
    )


def validate_pytest_config() -> bool:
    """Validate pytest configuration."""
    required_content = [
        "[tool:pytest]",
        "testpaths = tests",
        "--cov=simulation",
        "markers =",
    ]
    return check_file_exists_and_validate(
        "pytest.ini", "Pytest configuration", required_content
    )


def validate_precommit_config() -> bool:
    """Validate pre-commit configuration."""
    required_content = [
        "repos:",
        "- repo: https://github.com/psf/black",
        "- repo: https://github.com/pycqa/isort",
        "- repo: https://github.com/pycqa/pylint",
        "- repo: https://github.com/pre-commit/mirrors-mypy",
    ]
    return check_file_exists_and_validate(
        ".pre-commit-config.yaml", "Pre-commit configuration", required_content
    )


def validate_quality_documentation() -> bool:
    """Validate quality baseline documentation."""
    return check_file_exists_and_validate(
        "docs/quality_baseline.md",
        "Quality baseline documentation",
        ["Quality Baseline Report", "Tool Configurations", "Baseline Measurements"],
    )


def check_directory_structure() -> bool:
    """Check that required directories exist."""
    required_dirs = [
        ("docs", "Documentation directory"),
    ]

    all_exist = True
    for dir_path, description in required_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print(f"✅ {description}: {dir_path}/")
        else:
            print(f"❌ {description}: {dir_path}/ (MISSING)")
            all_exist = False

    return all_exist


def validate_tool_configurations() -> List[bool]:
    """Validate all tool configuration files."""
    return [
        validate_pylint_config(),
        validate_mypy_config(),
        validate_pytest_config(),
        validate_precommit_config(),
        validate_quality_documentation(),
        check_directory_structure(),
    ]


def check_configuration_quality() -> bool:
    """Check quality of configurations."""
    print("\n🔍 Configuration Quality Checks:")

    # Check for balanced PyLint settings
    try:
        with open(".pylintrc", "r") as f:
            pylint_content = f.read()

        # Should disable noisy rules for scientific code
        noisy_rules_disabled = all(
            rule in pylint_content
            for rule in ["too-many-arguments", "too-many-locals", "invalid-name"]
        )

        if noisy_rules_disabled:
            print("✅ PyLint: Scientific computing rules properly configured")
        else:
            print("❌ PyLint: Missing scientific computing rule adjustments")
            return False

    except Exception as e:
        print(f"❌ PyLint quality check failed: {e}")
        return False

    # Check MyPy gradual typing approach
    try:
        with open("mypy.ini", "r") as f:
            mypy_content = f.read()

        gradual_settings = [
            "disallow_untyped_defs = False",  # Start lenient
            "ignore_missing_imports = True",  # For C extensions
        ]

        if all(setting in mypy_content for setting in gradual_settings):
            print("✅ MyPy: Gradual typing approach configured")
        else:
            print("❌ MyPy: Missing gradual typing configuration")
            return False

    except Exception as e:
        print(f"❌ MyPy quality check failed: {e}")
        return False

    return True


def main():
    """Run Phase 1 validation."""
    print("🔧 Phase 1 Validation: Tool Integration & Baseline Configs")
    print("=" * 60)

    # Basic file existence checks
    basic_checks = validate_tool_configurations()

    # Configuration quality checks
    quality_check = check_configuration_quality()

    # Summary
    all_checks = basic_checks + [quality_check]
    passed = sum(all_checks)
    total = len(all_checks)

    print("\n" + "=" * 60)

    if passed == total:
        print(f"🎉 Phase 1 COMPLETE: All {total} checks passed!")
        print("\n📋 Phase 1 Deliverables:")
        print("   ✅ PyLint configuration (.pylintrc)")
        print("   ✅ MyPy configuration (mypy.ini)")
        print("   ✅ Pytest configuration (pytest.ini)")
        print("   ✅ Pre-commit hooks (.pre-commit-config.yaml)")
        print("   ✅ Quality baseline documentation")
        print("   ✅ Balanced configurations for scientific Python")
        print("\n🚀 Ready for Phase 2: Static Analysis & Typing Hardening")
        return True
    else:
        print(f"❌ Phase 1 INCOMPLETE: {passed}/{total} checks passed")
        print("   Fix the failing checks before proceeding to Phase 2")

        # Provide guidance for common issues
        print("\n💡 Common fixes:")
        print("   - Ensure all config files are created with proper content")
        print("   - Check that docs/ directory exists")
        print("   - Verify configurations contain required sections")

        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
