#!/usr/bin/env python3
"""
Code Quality Fixer for KPP Simulator
Applies black formatting and isort import organization to all Python files.
"""
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n🔄 {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if result.returncode == 0:
            print(f"✅ {description}: SUCCESS")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"⚠️  {description}: FAILED")
            if result.stderr.strip():
                print(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description}: EXCEPTION - {e}")
        return False


def fix_formatting():
    """Apply black formatting to core files."""
    core_files = [
        "app.py",
        "simulation/components/floater.py",
        "simulation/components/clutch.py",
        "simulation/components/drivetrain.py",
        "simulation/components/generator.py",
        "simulation/controller.py",
    ]

    success_count = 0
    for file_path in core_files:
        if os.path.exists(file_path):
            if run_command(
                [sys.executable, "-m", "black", file_path], f"Format {file_path}"
            ):
                success_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")

    return success_count


def fix_imports():
    """Apply isort import organization to core files."""
    core_files = [
        "app.py",
        "simulation/components/floater.py",
        "simulation/components/clutch.py",
        "simulation/components/drivetrain.py",
        "simulation/components/generator.py",
        "simulation/controller.py",
    ]

    success_count = 0
    for file_path in core_files:
        if os.path.exists(file_path):
            if run_command(
                [sys.executable, "-m", "isort", file_path],
                f"Fix imports in {file_path}",
            ):
                success_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")

    return success_count


def main():
    """Main execution function."""
    print("🚀 STARTING CODE QUALITY FIXES")
    print("=" * 50)

    # Step 1: Fix formatting
    print("\n📝 STEP 1: APPLYING BLACK FORMATTING")
    format_fixes = fix_formatting()

    # Step 2: Fix imports
    print("\n📋 STEP 2: ORGANIZING IMPORTS WITH ISORT")
    import_fixes = fix_imports()

    # Summary
    print("\n" + "=" * 50)
    print("📊 CODE QUALITY FIXES SUMMARY")
    print("=" * 50)
    print(f"✅ Files formatted with black: {format_fixes}")
    print(f"✅ Files organized with isort: {import_fixes}")

    if format_fixes > 0 or import_fixes > 0:
        print("\n🎉 Code quality improvements applied successfully!")
        print("💡 Run the CI pipeline again to see improved results.")
    else:
        print("\n⚠️  No fixes applied. Check file paths and tool availability.")


if __name__ == "__main__":
    main()
