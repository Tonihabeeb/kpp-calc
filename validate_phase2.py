#!/usr/bin/env python3
"""
Phase 2 Validation Script - Static Analysis & Typing Hardening Verification

This script validates the progress of Phase 2 type hint implementation
and measures improvements in static analysis metrics.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def run_command_safe(cmd: List[str]) -> Tuple[bool, str]:
    """Run a command safely and return success status and output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def count_type_hints_in_file(file_path: Path) -> Dict[str, int]:
    """Count type hints in a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Count various type hint patterns
        type_stats = {
            "functions_with_return_types": content.count(" -> "),
            "functions_with_param_types": content.count(": "),
            "typing_imports": 0,
            "total_functions": content.count("def "),
        }

        # Check for typing imports
        typing_patterns = [
            "from typing import",
            "import typing",
            "Dict[",
            "List[",
            "Optional[",
            "Any",
        ]
        type_stats["typing_imports"] = sum(
            1 for pattern in typing_patterns if pattern in content
        )

        return type_stats
    except Exception:
        return {
            "functions_with_return_types": 0,
            "functions_with_param_types": 0,
            "typing_imports": 0,
            "total_functions": 0,
        }


def analyze_typing_progress() -> Dict[str, Any]:
    """Analyze typing progress across key modules."""
    key_modules = [
        "simulation/engine.py",
        "simulation/components/floater.py",
        "simulation/logging/data_logger.py",
        "routes/export_routes.py",
        "app.py",
    ]

    progress = {}
    total_stats = {
        "functions_with_return_types": 0,
        "functions_with_param_types": 0,
        "typing_imports": 0,
        "total_functions": 0,
    }

    for module_path in key_modules:
        path = Path(module_path)
        if path.exists():
            stats = count_type_hints_in_file(path)
            progress[module_path] = stats

            # Add to totals
            for key in total_stats:
                total_stats[key] += stats[key]
        else:
            progress[module_path] = {"error": "File not found"}

    # Calculate percentages
    total_functions = total_stats["total_functions"]
    if total_functions > 0:
        return_type_percentage = (
            total_stats["functions_with_return_types"] / total_functions
        ) * 100
        param_type_percentage = (
            total_stats["functions_with_param_types"] / total_functions
        ) * 100
    else:
        return_type_percentage = param_type_percentage = 0

    return {
        "module_progress": progress,
        "totals": total_stats,
        "return_type_percentage": return_type_percentage,
        "param_type_percentage": param_type_percentage,
    }


def validate_syntax() -> bool:
    """Check that Python files have valid syntax."""
    print("🔍 Syntax Validation:")

    key_files = ["simulation/engine.py", "simulation/components/floater.py", "app.py"]

    all_valid = True
    for file_path in key_files:
        path = Path(file_path)
        if not path.exists():
            print(f"❌ {file_path}: File not found")
            all_valid = False
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            compile(content, file_path, "exec")
            print(f"✅ {file_path}: Valid syntax")
        except SyntaxError as e:
            print(f"❌ {file_path}: Syntax error at line {e.lineno}: {e.msg}")
            all_valid = False
        except Exception as e:
            print(f"❌ {file_path}: Error: {e}")
            all_valid = False

    return all_valid


def check_import_organization() -> bool:
    """Check that imports are properly organized."""
    print("\n📦 Import Organization:")

    # Check key files for typing imports
    files_to_check = [
        ("simulation/engine.py", ["typing"]),
        ("simulation/components/floater.py", ["typing"]),
    ]

    all_good = True
    for file_path, required_imports in files_to_check:
        path = Path(file_path)
        if not path.exists():
            print(f"❌ {file_path}: File not found")
            all_good = False
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            missing_imports = []
            for req_import in required_imports:
                if req_import not in content:
                    missing_imports.append(req_import)

            if missing_imports:
                print(f"❌ {file_path}: Missing imports: {missing_imports}")
                all_good = False
            else:
                print(f"✅ {file_path}: Required imports present")

        except Exception as e:
            print(f"❌ {file_path}: Error checking imports: {e}")
            all_good = False

    return all_good


def main():
    """Run Phase 2 validation."""
    print("🔍 Phase 2 Validation: Static Analysis & Typing Hardening")
    print("=" * 65)

    # 1. Syntax validation
    syntax_valid = validate_syntax()

    # 2. Import organization
    imports_good = check_import_organization()

    # 3. Typing progress analysis
    print("\n📊 Type Hint Progress Analysis:")
    typing_progress = analyze_typing_progress()

    print(
        f"Overall Return Type Coverage: {typing_progress['return_type_percentage']:.1f}%"
    )
    print(
        f"Overall Parameter Type Coverage: {typing_progress['param_type_percentage']:.1f}%"
    )
    print(f"Total Functions Analyzed: {typing_progress['totals']['total_functions']}")

    print("\n📋 Key Module Progress:")
    for module, stats in typing_progress["module_progress"].items():
        if "error" in stats:
            print(f"❌ {module}: {stats['error']}")
        else:
            total_funcs = stats["total_functions"]
            return_types = stats["functions_with_return_types"]
            if total_funcs > 0:
                return_pct = (return_types / total_funcs) * 100
                print(
                    f"📈 {module}: {return_types}/{total_funcs} functions ({return_pct:.1f}%) with return types"
                )
            else:
                print(f"📄 {module}: No functions found")

    # 4. Overall assessment
    print("\n" + "=" * 65)

    checks = [syntax_valid, imports_good]
    passed = sum(checks)
    total = len(checks)

    # Phase 2 targets
    targets_met = []
    target_return_type_coverage = 15.0  # Conservative target for Phase 2

    if typing_progress["return_type_percentage"] >= target_return_type_coverage:
        targets_met.append("Return type coverage target met")
        print(
            f"✅ Return type coverage: {typing_progress['return_type_percentage']:.1f}% (≥{target_return_type_coverage}%)"
        )
    else:
        print(
            f"🔄 Return type coverage: {typing_progress['return_type_percentage']:.1f}% (target: {target_return_type_coverage}%)"
        )

    if syntax_valid and imports_good:
        targets_met.append("Code quality maintained")
        print("✅ Code quality: All syntax and import checks passed")

    if len(targets_met) >= 1:
        print(f"\n🎉 Phase 2 PROGRESS: {len(targets_met)} key targets achieved!")
        print("\n📋 Completed:")
        for target in targets_met:
            print(f"   ✅ {target}")

        print("\n🚀 Next Steps for Phase 2 completion:")
        print("   📝 Add type hints to remaining high-priority functions")
        print("   🔧 Resolve any remaining static analysis issues")
        print("   📈 Reach 30% return type coverage target")
        print("   🧪 Prepare for Phase 3: Unit Testing Implementation")

        return True
    else:
        print(f"❌ Phase 2 IN PROGRESS: {passed}/{total} basic checks passed")
        print("   Continue adding type hints and resolving issues")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
