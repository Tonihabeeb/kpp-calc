#!/usr/bin/env python3
"""
Comprehensive Static Analysis for KPP Simulator
Combines multiple tools to provide DeepSource-like analysis
"""

import subprocess
import json
import os
import sys
import logging
from typing import Dict, List, Any, Tuple
from pathlib import Path
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveStaticAnalyzer:
    """Comprehensive static analysis using multiple tools."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.analysis_results = {}
        self.fixes_applied = []
        self.critical_issues = []
        self.quality_score = 0.0
        
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive static analysis using multiple tools."""
        logger.info("Starting comprehensive static analysis...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "tools": {},
            "summary": {},
            "issues": [],
            "recommendations": []
        }
        
        # Run each analysis tool
        tools = [
            ("pylint", self._run_pylint),
            ("flake8", self._run_flake8),
            ("black_check", self._run_black_check),
            ("autopep8_check", self._run_autopep8_check),
            ("complexity_analysis", self._run_complexity_analysis),
            ("import_analysis", self._run_import_analysis)
        ]
        
        for tool_name, tool_func in tools:
            try:
                logger.info(f"Running {tool_name}...")
                tool_results = tool_func()
                results["tools"][tool_name] = tool_results
            except Exception as e:
                logger.error(f"Error running {tool_name}: {e}")
                results["tools"][tool_name] = {"error": str(e)}
        
        # Generate summary
        results["summary"] = self._generate_summary(results["tools"])
        results["issues"] = self._extract_all_issues(results["tools"])
        results["recommendations"] = self._generate_recommendations(results["tools"])
        
        self.analysis_results = results
        return results
    
    def _run_pylint(self) -> Dict[str, Any]:
        """Run pylint analysis."""
        try:
            # Focus on core directories
            core_dirs = ["simulation", "config", "utils", "app.py", "dash_app.py", "main.py"]
            
            result = subprocess.run(
                [sys.executable, "-m", "pylint"] + core_dirs + 
                ["--output-format=json", "--disable=C0114,C0115,C0116"],  # Disable docstring warnings
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                issues = json.loads(result.stdout)
                return {
                    "status": "success",
                    "issues": issues,
                    "total_issues": len(issues),
                    "score": self._calculate_pylint_score(issues)
                }
            else:
                return {
                    "status": "error",
                    "error": result.stderr,
                    "issues": [],
                    "total_issues": 0,
                    "score": 0.0
                }
        except Exception as e:
            return {"status": "error", "error": str(e), "issues": [], "total_issues": 0, "score": 0.0}
    
    def _run_flake8(self) -> Dict[str, Any]:
        """Run flake8 analysis."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "flake8", "simulation", "config", "utils", "app.py", "dash_app.py", "main.py"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            issues = []
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(':')
                        if len(parts) >= 4:
                            issues.append({
                                "file": parts[0],
                                "line": int(parts[1]),
                                "column": int(parts[2]),
                                "code": parts[3].split()[0],
                                "message": ':'.join(parts[3:]).strip()
                            })
            
            return {
                "status": "success",
                "issues": issues,
                "total_issues": len(issues)
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "issues": [], "total_issues": 0}
    
    def _run_black_check(self) -> Dict[str, Any]:
        """Check code formatting with black."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "black", "--check", "--diff", "simulation", "config", "utils", "app.py", "dash_app.py", "main.py"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            return {
                "status": "success",
                "needs_formatting": result.returncode != 0,
                "diff": result.stdout if result.returncode != 0 else "",
                "files_need_formatting": self._count_files_needing_formatting(result.stdout)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _run_autopep8_check(self) -> Dict[str, Any]:
        """Check code formatting with autopep8."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "autopep8", "--diff", "--recursive", "simulation", "config", "utils", "app.py", "dash_app.py", "main.py"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            return {
                "status": "success",
                "needs_formatting": bool(result.stdout.strip()),
                "diff": result.stdout,
                "files_need_formatting": self._count_files_needing_formatting(result.stdout)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _run_complexity_analysis(self) -> Dict[str, Any]:
        """Analyze code complexity."""
        try:
            complex_functions = []
            total_functions = 0
            
            # Analyze core Python files
            core_files = list(Path("simulation").rglob("*.py")) + \
                        list(Path("config").rglob("*.py")) + \
                        [Path("app.py"), Path("dash_app.py"), Path("main.py")]
            
            for file_path in core_files:
                if file_path.exists():
                    complexity_data = self._analyze_file_complexity(file_path)
                    complex_functions.extend(complexity_data["complex_functions"])
                    total_functions += complexity_data["total_functions"]
            
            return {
                "status": "success",
                "complex_functions": complex_functions,
                "total_functions": total_functions,
                "complexity_ratio": len(complex_functions) / max(total_functions, 1)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _run_import_analysis(self) -> Dict[str, Any]:
        """Analyze import statements."""
        try:
            unused_imports = []
            total_imports = 0
            
            # Analyze core Python files
            core_files = list(Path("simulation").rglob("*.py")) + \
                        list(Path("config").rglob("*.py")) + \
                        [Path("app.py"), Path("dash_app.py"), Path("main.py")]
            
            for file_path in core_files:
                if file_path.exists():
                    import_data = self._analyze_file_imports(file_path)
                    unused_imports.extend(import_data["unused_imports"])
                    total_imports += import_data["total_imports"]
            
            return {
                "status": "success",
                "unused_imports": unused_imports,
                "total_imports": total_imports,
                "unused_ratio": len(unused_imports) / max(total_imports, 1)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _calculate_pylint_score(self, issues: List[Dict]) -> float:
        """Calculate pylint score from issues."""
        if not issues:
            return 10.0
        
        # Count issues by severity
        error_count = sum(1 for issue in issues if issue.get("type") == "error")
        warning_count = sum(1 for issue in issues if issue.get("type") == "warning")
        convention_count = sum(1 for issue in issues if issue.get("type") == "convention")
        
        # Calculate score (10.0 is perfect)
        score = 10.0 - (error_count * 0.1) - (warning_count * 0.05) - (convention_count * 0.02)
        return max(0.0, score)
    
    def _count_files_needing_formatting(self, diff_output: str) -> int:
        """Count files that need formatting."""
        if not diff_output:
            return 0
        
        # Count unique files in diff
        files = set()
        for line in diff_output.split('\n'):
            if line.startswith('--- a/') or line.startswith('+++ b/'):
                file_path = line.split(' ', 1)[1]
                files.add(file_path)
        
        return len(files)
    
    def _analyze_file_complexity(self, file_path: Path) -> Dict[str, Any]:
        """Analyze complexity of a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            complex_functions = []
            total_functions = 0
            
            for i, line in enumerate(lines, 1):
                # Count function definitions
                if re.match(r'^\s*def\s+\w+', line):
                    total_functions += 1
                    
                    # Simple complexity estimation (count if/elif/else/for/while/try/except)
                    complexity = 1  # Base complexity
                    for j in range(i, min(i + 50, len(lines))):  # Check next 50 lines
                        next_line = lines[j].strip()
                        if any(keyword in next_line for keyword in ['if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except']):
                            complexity += 1
                        elif re.match(r'^\s*def\s+', next_line):  # Stop at next function
                            break
                    
                    if complexity > 10:  # High complexity threshold
                        complex_functions.append({
                            "file": str(file_path),
                            "line": i,
                            "function": re.search(r'def\s+(\w+)', line).group(1),
                            "complexity": complexity
                        })
            
            return {
                "complex_functions": complex_functions,
                "total_functions": total_functions
            }
        except Exception as e:
            return {"complex_functions": [], "total_functions": 0, "error": str(e)}
    
    def _analyze_file_imports(self, file_path: Path) -> Dict[str, Any]:
        """Analyze imports in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            imports = []
            unused_imports = []
            
            # Extract import statements
            for i, line in enumerate(lines, 1):
                if line.strip().startswith(('import ', 'from ')):
                    import_match = re.match(r'(?:from\s+(\S+)\s+import\s+(\S+)|import\s+(\S+))', line.strip())
                    if import_match:
                        if import_match.group(1):  # from ... import ...
                            module = import_match.group(1)
                            name = import_match.group(2)
                        else:  # import ...
                            module = import_match.group(3)
                            name = module
                        
                        imports.append({
                            "line": i,
                            "module": module,
                            "name": name,
                            "full_import": line.strip()
                        })
            
            # Simple check for unused imports (basic heuristic)
            for imp in imports:
                name_to_check = imp["name"].split('.')[-1]  # Get last part
                if name_to_check not in content[i+1:]:  # Check if used after import
                    unused_imports.append(imp)
            
            return {
                "unused_imports": unused_imports,
                "total_imports": len(imports)
            }
        except Exception as e:
            return {"unused_imports": [], "total_imports": 0, "error": str(e)}
    
    def _generate_summary(self, tools_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary from all tool results."""
        total_issues = 0
        critical_issues = 0
        formatting_issues = 0
        
        # Count issues from each tool
        for tool_name, results in tools_results.items():
            if isinstance(results, dict) and results.get("status") == "success":
                if "total_issues" in results:
                    total_issues += results["total_issues"]
                if "complex_functions" in results:
                    critical_issues += len(results["complex_functions"])
                if "needs_formatting" in results and results["needs_formatting"]:
                    formatting_issues += 1
        
        # Calculate quality score
        quality_score = max(0.0, 100.0 - (total_issues * 2) - (critical_issues * 5) - (formatting_issues * 10))
        
        return {
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "formatting_issues": formatting_issues,
            "quality_score": quality_score,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def _extract_all_issues(self, tools_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all issues from tool results."""
        all_issues = []
        
        for tool_name, results in tools_results.items():
            if isinstance(results, dict) and results.get("status") == "success":
                if "issues" in results:
                    for issue in results["issues"]:
                        issue["tool"] = tool_name
                        all_issues.append(issue)
        
        return all_issues
    
    def _generate_recommendations(self, tools_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        # Check for formatting issues
        if tools_results.get("black_check", {}).get("needs_formatting"):
            recommendations.append("Run 'black' to format code consistently")
        
        if tools_results.get("autopep8_check", {}).get("needs_formatting"):
            recommendations.append("Run 'autopep8' to fix PEP 8 violations")
        
        # Check for complexity issues
        complexity_data = tools_results.get("complexity_analysis", {})
        if complexity_data.get("complex_functions"):
            recommendations.append(f"Refactor {len(complexity_data['complex_functions'])} complex functions")
        
        # Check for import issues
        import_data = tools_results.get("import_analysis", {})
        if import_data.get("unused_imports"):
            recommendations.append(f"Remove {len(import_data['unused_imports'])} unused imports")
        
        # Check for pylint issues
        pylint_data = tools_results.get("pylint", {})
        if pylint_data.get("total_issues", 0) > 0:
            recommendations.append(f"Address {pylint_data['total_issues']} pylint issues")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save analysis report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_static_analysis_report_{timestamp}.json"
        
        filepath = self.project_root / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Report saved to: {filepath}")
        return str(filepath)

def main():
    """Main function to run comprehensive analysis."""
    logger.info("Starting Comprehensive Static Analysis for KPP Simulator")
    
    analyzer = ComprehensiveStaticAnalyzer()
    
    # Run analysis
    results = analyzer.run_comprehensive_analysis()
    
    # Save report
    report_file = analyzer.save_report(results)
    
    # Print summary
    summary = results["summary"]
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE STATIC ANALYSIS SUMMARY")
    print(f"{'='*60}")
    print(f"Quality Score: {summary['quality_score']:.1f}/100")
    print(f"Total Issues: {summary['total_issues']}")
    print(f"Critical Issues: {summary['critical_issues']}")
    print(f"Formatting Issues: {summary['formatting_issues']}")
    print(f"Analysis Time: {summary['analysis_timestamp']}")
    print(f"{'='*60}")
    
    # Print recommendations
    if results["recommendations"]:
        print(f"\nRECOMMENDATIONS:")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"{i}. {rec}")
    
    print(f"\nDetailed report saved to: {report_file}")
    
    return results

if __name__ == "__main__":
    main() 