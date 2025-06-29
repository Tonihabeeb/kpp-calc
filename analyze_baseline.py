#!/usr/bin/env python3
"""
Phase 2 Baseline Analysis - Static Analysis & Typing Assessment

This script analyzes the current codebase to establish baseline measurements
for type hints, import structure, and code complexity before implementing
systematic improvements.
"""

import ast
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set


class CodebaseAnalyzer:
    """Analyzes Python codebase for typing and quality metrics."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.stats = {
            "total_files": 0,
            "total_lines": 0,
            "total_functions": 0,
            "total_classes": 0,
            "typed_functions": 0,
            "typed_methods": 0,
            "complex_functions": 0,
            "import_issues": [],
            "high_priority_functions": [],
        }
        self.modules = {}

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single Python file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            file_stats = {
                "path": str(file_path),
                "lines": len(content.splitlines()),
                "functions": [],
                "classes": [],
                "imports": [],
                "complexity_issues": [],
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = self.analyze_function(node)
                    file_stats["functions"].append(func_info)

                elif isinstance(node, ast.ClassDef):
                    class_info = self.analyze_class(node)
                    file_stats["classes"].append(class_info)

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_info = self.analyze_import(node)
                    file_stats["imports"].append(import_info)

            return file_stats

        except Exception as e:
            return {"path": str(file_path), "error": str(e)}

    def analyze_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze a function for type hints and complexity."""
        has_return_type = node.returns is not None
        has_arg_types = any(arg.annotation is not None for arg in node.args.args)

        # Count lines in function
        if (
            hasattr(node, "lineno")
            and hasattr(node, "end_lineno")
            and node.end_lineno is not None
        ):
            line_count = node.end_lineno - node.lineno + 1
        else:
            line_count = 0

        # Count parameters
        param_count = len(node.args.args)

        # Assess complexity
        complexity_issues = []
        if param_count > 8:
            complexity_issues.append(f"Many parameters: {param_count}")
        if line_count > 50:
            complexity_issues.append(f"Long function: {line_count} lines")

        return {
            "name": node.name,
            "line": node.lineno,
            "has_return_type": has_return_type,
            "has_arg_types": has_arg_types,
            "is_typed": has_return_type and has_arg_types,
            "param_count": param_count,
            "line_count": line_count,
            "complexity_issues": complexity_issues,
        }

    def analyze_class(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Analyze a class for methods and typing."""
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self.analyze_function(item)
                method_info["is_method"] = True
                methods.append(method_info)

        return {
            "name": node.name,
            "line": node.lineno,
            "methods": methods,
            "method_count": len(methods),
        }

    def analyze_import(self, node) -> Dict[str, Any]:
        """Analyze import statements."""
        if isinstance(node, ast.Import):
            return {
                "type": "import",
                "modules": [alias.name for alias in node.names],
                "line": node.lineno,
            }
        elif isinstance(node, ast.ImportFrom):
            return {
                "type": "from_import",
                "module": node.module,
                "names": [alias.name for alias in node.names] if node.names else ["*"],
                "line": node.lineno,
            }
        else:
            return {"type": "unknown", "line": getattr(node, "lineno", 0)}

    def identify_high_priority_functions(self) -> List[Dict[str, Any]]:
        """Identify functions that should be prioritized for type hints."""
        high_priority = []

        priority_patterns = [
            "step",
            "update",
            "calculate",
            "compute",
            "get_",
            "set_",
            "__init__",
        ]

        for module_path, module_data in self.modules.items():
            if "error" in module_data:
                continue

            for func in module_data.get("functions", []):
                # Check if function name matches priority patterns
                is_priority = any(
                    pattern in func["name"].lower() for pattern in priority_patterns
                )

                # Check if it's complex or important
                is_complex = (
                    func["param_count"] > 5
                    or func["line_count"] > 20
                    or func["complexity_issues"]
                )

                # Check if it's in a core module
                is_core_module = any(
                    core in module_path
                    for core in ["engine.py", "floater.py", "data_logger.py"]
                )

                if (is_priority or is_complex or is_core_module) and not func[
                    "is_typed"
                ]:
                    high_priority.append(
                        {
                            "module": module_path,
                            "function": func["name"],
                            "line": func["line"],
                            "reason": self.get_priority_reason(
                                func, is_priority, is_complex, is_core_module
                            ),
                            "param_count": func["param_count"],
                            "line_count": func["line_count"],
                        }
                    )

        # Sort by priority
        high_priority.sort(
            key=lambda x: (
                "engine.py" in x["module"],  # Engine functions first
                "step" in x["function"].lower(),  # Step functions highest
                x["param_count"],  # More parameters = higher priority
                x["line_count"],  # Longer functions = higher priority
            ),
            reverse=True,
        )

        return high_priority[:20]  # Top 20 priorities

    def get_priority_reason(
        self, func: Dict, is_priority: bool, is_complex: bool, is_core: bool
    ) -> str:
        """Get reason why function is high priority."""
        reasons = []
        if "step" in func["name"].lower():
            reasons.append("Core simulation method")
        elif "compute" in func["name"].lower() or "calculate" in func["name"].lower():
            reasons.append("Physics calculation")
        elif func["name"] == "__init__":
            reasons.append("Constructor")
        elif is_priority:
            reasons.append("High-traffic method")

        if is_complex:
            reasons.append("High complexity")
        if is_core:
            reasons.append("Core module")

        return ", ".join(reasons) if reasons else "Important function"

    def analyze_codebase(self) -> None:
        """Analyze the entire codebase."""
        python_files = list(self.root_path.rglob("*.py"))

        # Filter out test files, virtual env, and other non-source files
        source_files = [
            f
            for f in python_files
            if not any(
                exclude in str(f)
                for exclude in [
                    ".venv",
                    "__pycache__",
                    "test_",
                    "_test.py",
                    "logs",
                    "build",
                    "dist",
                ]
            )
        ]

        self.stats["total_files"] = len(source_files)

        for file_path in source_files:
            print(f"Analyzing: {file_path.relative_to(self.root_path)}")
            module_data = self.analyze_file(file_path)
            self.modules[str(file_path.relative_to(self.root_path))] = module_data

            if "error" not in module_data:
                self.stats["total_lines"] += module_data["lines"]
                self.stats["total_functions"] += len(module_data["functions"])
                self.stats["total_classes"] += len(module_data["classes"])

                # Count typed functions
                for func in module_data["functions"]:
                    if func["is_typed"]:
                        self.stats["typed_functions"] += 1
                    if func["complexity_issues"]:
                        self.stats["complex_functions"] += 1

                # Count typed methods
                for cls in module_data["classes"]:
                    for method in cls["methods"]:
                        if method["is_typed"]:
                            self.stats["typed_methods"] += 1

    def generate_report(self) -> str:
        """Generate a comprehensive baseline report."""
        # Get high priority functions
        self.stats["high_priority_functions"] = self.identify_high_priority_functions()

        # Calculate percentages
        total_functions = self.stats["total_functions"]
        typing_percentage = (
            (self.stats["typed_functions"] / total_functions * 100)
            if total_functions > 0
            else 0
        )

        report = f"""# Phase 2 Baseline Report - Static Analysis & Typing Assessment

**Generated:** June 28, 2025  
**Analysis Target:** KPP Simulator Codebase  
**Python Version:** {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}

## Codebase Overview

### 📊 **Basic Metrics**
- **Total Python Files:** {self.stats['total_files']}
- **Total Lines of Code:** {self.stats['total_lines']:,}
- **Total Functions:** {self.stats['total_functions']}
- **Total Classes:** {self.stats['total_classes']}

### 🔍 **Type Annotation Status**
- **Typed Functions:** {self.stats['typed_functions']}/{total_functions} ({typing_percentage:.1f}%)
- **Typed Methods:** {self.stats['typed_methods']}
- **Complex Functions:** {self.stats['complex_functions']} (>8 params or >50 lines)

## High-Priority Functions for Type Hints

The following functions should be prioritized for adding type annotations:

"""

        # Add high priority functions
        for i, func in enumerate(self.stats["high_priority_functions"][:10], 1):
            report += f"{i:2d}. **`{func['function']}`** in `{func['module']}`\n"
            report += f"    - Line {func['line']} | {func['param_count']} params | {func['line_count']} lines\n"
            report += f"    - Priority: {func['reason']}\n\n"

        report += f"""
## Module Analysis

### 📁 **Core Modules Assessment**

"""

        # Analyze core modules
        core_modules = {
            "simulation/engine.py": "Main simulation engine",
            "simulation/components/floater.py": "Floater physics",
            "simulation/logging/data_logger.py": "Stage 5 logging system",
            "routes/export_routes.py": "API endpoints",
            "app.py": "Flask application",
        }

        for module_path, description in core_modules.items():
            if module_path in self.modules:
                module = self.modules[module_path]
                if "error" not in module:
                    func_count = len(module["functions"])
                    typed_count = sum(1 for f in module["functions"] if f["is_typed"])
                    typing_pct = (
                        (typed_count / func_count * 100) if func_count > 0 else 0
                    )

                    report += f"**{module_path}** - {description}\n"
                    report += f"  - Functions: {func_count} ({typed_count} typed, {typing_pct:.1f}%)\n"
                    report += f"  - Lines: {module['lines']}\n\n"

        report += f"""
## Static Analysis Baseline

### 🎯 **Phase 2 Goals**
1. **Add type hints to top 10 high-priority functions**
2. **Resolve import organization issues**  
3. **Address complexity warnings in core modules**
4. **Achieve 30% type annotation coverage**

### 🔧 **Recommended Implementation Order**

#### Week 1: Core Engine Types
- `SimulationEngine.step()` - Main simulation loop
- `SimulationEngine.__init__()` - Engine initialization  
- `Floater.compute_buoyant_force()` - Physics calculation

#### Week 2: Data & Logging
- `DataLogger.__init__()` - Stage 5 logging system
- `DataLogger.log_data()` - Data recording methods
- Export route functions - API endpoints

#### Week 3: Physics & Components  
- Enhanced physics module methods (H1, H2, H3)
- Component update methods
- Control system functions

## Quality Improvement Strategy

### 📈 **Gradual Typing Approach**
1. Start with function signatures (parameters and return types)
2. Add basic type hints for common types (int, float, str, bool)
3. Use `Any` for complex types initially
4. Gradually refine to specific types (List[float], Dict[str, Any])

### 🛠️ **Tools Integration**
- Use MyPy for type checking with current lenient configuration
- PyLint for code quality (focusing on errors only initially)
- Automated formatting with Black and isort

### 📊 **Success Metrics**
- Type annotation coverage: {typing_percentage:.1f}% → 30% (Phase 2 target)
- MyPy error count: Baseline TBD → <50 errors
- PyLint error count: Baseline TBD → 0 errors
- Complex function count: {self.stats['complex_functions']} → Maintain or reduce

---

**Next Steps:** 
1. Implement type hints for top 10 priority functions
2. Run MyPy/PyLint to establish error baseline  
3. Create typing guidelines for team
4. Set up automated type checking in CI

"""
        return report


def main():
    """Run baseline analysis."""
    print("🔍 Phase 2 Baseline Analysis: Static Analysis & Typing Assessment")
    print("=" * 70)

    analyzer = CodebaseAnalyzer(".")
    analyzer.analyze_codebase()

    # Generate and save report
    report = analyzer.generate_report()

    with open("docs/phase2_baseline.md", "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ Analysis complete!")
    print(f"📊 Files analyzed: {analyzer.stats['total_files']}")
    print(f"🔍 Functions found: {analyzer.stats['total_functions']}")
    print(
        f"📝 Type coverage: {analyzer.stats['typed_functions']}/{analyzer.stats['total_functions']} functions"
    )
    print(f"📋 Report saved: docs/phase2_baseline.md")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
