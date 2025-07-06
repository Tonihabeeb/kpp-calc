#!/usr/bin/env python3
"""
Quick Static Analysis for KPP Simulator
Fast analysis focusing on critical files and immediate issues
"""

import subprocess
import json
import os
import sys
import logging
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickStaticAnalyzer:
    """Quick static analysis focusing on critical issues."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.critical_files = [
            "app.py",
            "dash_app.py", 
            "main.py",
            "simulation/engine.py",
            "simulation/controller.py"
        ]
        
    def run_quick_analysis(self) -> Dict[str, Any]:
        """Run quick analysis on critical files."""
        logger.info("Starting quick static analysis...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "issues": [],
            "recommendations": []
        }
        
        # Run focused analysis
        analysis_tools = [
            ("formatting_check", self._check_formatting),
            ("line_length_check", self._check_line_length),
            ("complexity_check", self._check_complexity),
            ("import_check", self._check_imports)
        ]
        
        all_issues = []
        for tool_name, tool_func in analysis_tools:
            try:
                logger.info(f"Running {tool_name}...")
                tool_issues = tool_func()
                all_issues.extend(tool_issues)
            except Exception as e:
                logger.error(f"Error in {tool_name}: {e}")
        
        results["issues"] = all_issues
        results["summary"] = self._generate_summary(all_issues)
        results["recommendations"] = self._generate_recommendations(all_issues)
        
        return results
    
    def _check_formatting(self) -> List[Dict[str, Any]]:
        """Check code formatting issues."""
        issues = []
        
        for file_path in self.critical_files:
            if Path(file_path).exists():
                try:
                    # Check with black
                    result = subprocess.run(
                        [sys.executable, "-m", "black", "--check", "--quiet", file_path],
                        capture_output=True,
                        text=True,
                        cwd=self.project_root
                    )
                    
                    if result.returncode != 0:
                        issues.append({
                            "type": "formatting",
                            "file": file_path,
                            "severity": "medium",
                            "message": "Code needs formatting with black",
                            "tool": "black"
                        })
                except Exception as e:
                    logger.warning(f"Could not check formatting for {file_path}: {e}")
        
        return issues
    
    def _check_line_length(self) -> List[Dict[str, Any]]:
        """Check for long lines."""
        issues = []
        max_line_length = 120
        
        for file_path in self.critical_files:
            if Path(file_path).exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines, 1):
                        if len(line.rstrip()) > max_line_length:
                            issues.append({
                                "type": "line_length",
                                "file": file_path,
                                "line": i,
                                "severity": "low",
                                "message": f"Line {i} exceeds {max_line_length} characters ({len(line.rstrip())} chars)",
                                "tool": "manual"
                            })
                except Exception as e:
                    logger.warning(f"Could not check line length for {file_path}: {e}")
        
        return issues
    
    def _check_complexity(self) -> List[Dict[str, Any]]:
        """Check for complex functions."""
        issues = []
        
        for file_path in self.critical_files:
            if Path(file_path).exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if line.strip().startswith('def '):
                            # Simple complexity estimation
                            complexity = 1
                            for j in range(i, min(i + 30, len(lines))):
                                next_line = lines[j].strip()
                                if any(keyword in next_line for keyword in ['if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except']):
                                    complexity += 1
                                elif next_line.startswith('def '):
                                    break
                            
                            if complexity > 10:
                                func_name = line.strip().split('def ')[1].split('(')[0]
                                issues.append({
                                    "type": "complexity",
                                    "file": file_path,
                                    "line": i,
                                    "severity": "medium",
                                    "message": f"Function '{func_name}' has high complexity ({complexity})",
                                    "tool": "manual"
                                })
                except Exception as e:
                    logger.warning(f"Could not check complexity for {file_path}: {e}")
        
        return issues
    
    def _check_imports(self) -> List[Dict[str, Any]]:
        """Check for obvious import issues."""
        issues = []
        
        for file_path in self.critical_files:
            if Path(file_path).exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    lines = content.split('\n')
                    imports = []
                    
                    # Find import statements
                    for i, line in enumerate(lines, 1):
                        if line.strip().startswith(('import ', 'from ')):
                            imports.append((i, line.strip()))
                    
                    # Check for obvious unused imports (very basic check)
                    for line_num, import_line in imports:
                        if 'import ' in import_line:
                            import_name = import_line.split('import ')[1].split()[0]
                            if import_name not in content[content.find(import_line) + len(import_line):]:
                                issues.append({
                                    "type": "unused_import",
                                    "file": file_path,
                                    "line": line_num,
                                    "severity": "low",
                                    "message": f"Potentially unused import: {import_name}",
                                    "tool": "manual"
                                })
                except Exception as e:
                    logger.warning(f"Could not check imports for {file_path}: {e}")
        
        return issues
    
    def _generate_summary(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary from issues."""
        total_issues = len(issues)
        formatting_issues = len([i for i in issues if i["type"] == "formatting"])
        line_length_issues = len([i for i in issues if i["type"] == "line_length"])
        complexity_issues = len([i for i in issues if i["type"] == "complexity"])
        import_issues = len([i for i in issues if i["type"] == "unused_import"])
        
        # Calculate quality score
        quality_score = max(0.0, 100.0 - (total_issues * 2) - (complexity_issues * 5))
        
        return {
            "total_issues": total_issues,
            "formatting_issues": formatting_issues,
            "line_length_issues": line_length_issues,
            "complexity_issues": complexity_issues,
            "import_issues": import_issues,
            "quality_score": quality_score
        }
    
    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on issues."""
        recommendations = []
        
        formatting_count = len([i for i in issues if i["type"] == "formatting"])
        if formatting_count > 0:
            recommendations.append(f"Run 'black' to format {formatting_count} files")
        
        line_length_count = len([i for i in issues if i["type"] == "line_length"])
        if line_length_count > 0:
            recommendations.append(f"Fix {line_length_count} long lines (max 120 chars)")
        
        complexity_count = len([i for i in issues if i["type"] == "complexity"])
        if complexity_count > 0:
            recommendations.append(f"Refactor {complexity_count} complex functions")
        
        import_count = len([i for i in issues if i["type"] == "unused_import"])
        if import_count > 0:
            recommendations.append(f"Review {import_count} potentially unused imports")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save analysis report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"quick_static_analysis_report_{timestamp}.json"
        
        filepath = self.project_root / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Report saved to: {filepath}")
        return str(filepath)

def main():
    """Main function to run quick analysis."""
    logger.info("Starting Quick Static Analysis for KPP Simulator")
    
    analyzer = QuickStaticAnalyzer()
    
    # Run analysis
    results = analyzer.run_quick_analysis()
    
    # Save report
    report_file = analyzer.save_report(results)
    
    # Print summary
    summary = results["summary"]
    print(f"\n{'='*60}")
    print(f"QUICK STATIC ANALYSIS SUMMARY")
    print(f"{'='*60}")
    print(f"Quality Score: {summary['quality_score']:.1f}/100")
    print(f"Total Issues: {summary['total_issues']}")
    print(f"Formatting Issues: {summary['formatting_issues']}")
    print(f"Line Length Issues: {summary['line_length_issues']}")
    print(f"Complexity Issues: {summary['complexity_issues']}")
    print(f"Import Issues: {summary['import_issues']}")
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