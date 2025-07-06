#!/usr/bin/env python3
"""
Comprehensive Code Quality Analysis for KPP Simulator
Analyzes code quality, syntax, imports, and potential issues.
"""

import ast
import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CodeIssue:
    """Represents a code quality issue"""
    file_path: str
    line_number: int
    issue_type: str
    severity: str
    description: str
    suggestion: str = ""

@dataclass
class FileAnalysis:
    """Analysis results for a single file"""
    file_path: str
    lines_of_code: int
    issues: List[CodeIssue]
    has_syntax_errors: bool
    import_issues: List[str]
    complexity_score: float

class CodeQualityAnalyzer:
    """Comprehensive code quality analyzer for KPP Simulator"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.analysis_results = {}
        self.total_issues = 0
        self.critical_issues = 0
        self.files_analyzed = 0
        
        # Define file patterns to analyze
        self.python_patterns = [
            "*.py",
            "simulation/**/*.py",
            "config/**/*.py", 
            "utils/**/*.py",
            "routes/**/*.py"
        ]
        
        # Define patterns to exclude
        self.exclude_patterns = [
            "**/__pycache__/**",
            "**/.venv/**",
            "**/venv/**",
            "**/env/**",
            "**/node_modules/**",
            "**/*.log",
            "**/logs/**",
            "**/tests/**",
            "**/validation/**",
            "**/archive/**",
            "**/backup/**"
        ]
    
    def find_python_files(self) -> List[Path]:
        """Find all Python files to analyze"""
        python_files = []
        
        for pattern in self.python_patterns:
            files = list(self.project_root.glob(pattern))
            python_files.extend(files)
        
        # Remove duplicates and excluded files
        unique_files = list(set(python_files))
        filtered_files = []
        
        for file_path in unique_files:
            # Check if file should be excluded
            should_exclude = False
            for exclude_pattern in self.exclude_patterns:
                if file_path.match(exclude_pattern):
                    should_exclude = True
                    break
            
            if not should_exclude and file_path.is_file():
                filtered_files.append(file_path)
        
        return filtered_files
    
    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a single Python file"""
        issues = []
        import_issues = []
        has_syntax_errors = False
        complexity_score = 0.0
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines_of_code = len(content.splitlines())
            
            # Parse AST
            try:
                tree = ast.parse(content)
                complexity_score = self._calculate_complexity(tree)
                
                # Analyze imports
                import_issues = self._analyze_imports(tree, file_path)
                
                # Analyze code patterns
                issues.extend(self._analyze_code_patterns(tree, file_path))
                
                # Analyze naming conventions
                issues.extend(self._analyze_naming_conventions(tree, file_path))
                
                # Analyze potential bugs
                issues.extend(self._analyze_potential_bugs(tree, file_path))
                
            except SyntaxError as e:
                has_syntax_errors = True
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=e.lineno or 0,
                    issue_type="syntax_error",
                    severity="critical",
                    description=f"Syntax error: {e.msg}",
                    suggestion="Fix the syntax error in the code"
                ))
            
        except Exception as e:
            issues.append(CodeIssue(
                file_path=str(file_path),
                line_number=0,
                issue_type="file_error",
                severity="critical",
                description=f"Error reading file: {e}",
                suggestion="Check file permissions and encoding"
            ))
        
        return FileAnalysis(
            file_path=str(file_path),
            lines_of_code=lines_of_code,
            issues=issues,
            has_syntax_errors=has_syntax_errors,
            import_issues=import_issues,
            complexity_score=complexity_score
        )
    
    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.With):
                complexity += 1
            elif isinstance(node, ast.AsyncWith):
                complexity += 1
        
        return complexity
    
    def _analyze_imports(self, tree: ast.AST, file_path: Path) -> List[str]:
        """Analyze import statements for issues"""
        issues = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        # Check for common import issues
        for imp in imports:
            if imp.startswith('.'):
                issues.append(f"Relative import: {imp}")
            if imp == 'os' and 'path' in imports:
                issues.append("Consider using pathlib instead of os.path")
        
        return issues
    
    def _analyze_code_patterns(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Analyze code patterns for potential issues"""
        issues = []
        
        for node in ast.walk(tree):
            # Check for broad except clauses
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=getattr(node, 'lineno', 0),
                    issue_type="broad_except",
                    severity="warning",
                    description="Bare except clause catches all exceptions",
                    suggestion="Specify exception types to catch"
                ))
            
            # Check for unused variables
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # This is a simplified check - in practice you'd need more context
                        pass
            
            # Check for magic numbers
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if isinstance(node.value, int) and abs(node.value) > 10:
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=getattr(node, 'lineno', 0),
                        issue_type="magic_number",
                        severity="info",
                        description=f"Magic number: {node.value}",
                        suggestion="Define as a named constant"
                    ))
        
        return issues
    
    def _analyze_naming_conventions(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Analyze naming conventions"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_') and node.name.isupper():
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=getattr(node, 'lineno', 0),
                        issue_type="naming_convention",
                        severity="warning",
                        description=f"Function name '{node.name}' should be lowercase",
                        suggestion="Use snake_case for function names"
                    ))
            
            elif isinstance(node, ast.ClassDef):
                if not node.name[0].isupper():
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=getattr(node, 'lineno', 0),
                        issue_type="naming_convention",
                        severity="warning",
                        description=f"Class name '{node.name}' should be PascalCase",
                        suggestion="Use PascalCase for class names"
                    ))
        
        return issues
    
    def _analyze_potential_bugs(self, tree: ast.AST, file_path: Path) -> List[CodeIssue]:
        """Analyze for potential bugs"""
        issues = []
        
        for node in ast.walk(tree):
            # Check for mutable default arguments
            if isinstance(node, ast.FunctionDef):
                for arg in node.args.defaults:
                    if isinstance(arg, (ast.List, ast.Dict, ast.Set)):
                        issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=getattr(node, 'lineno', 0),
                            issue_type="mutable_default",
                            severity="warning",
                            description="Mutable default argument",
                            suggestion="Use None as default and initialize in function body"
                        ))
            
            # Check for potential division by zero
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                if isinstance(node.right, ast.Constant) and node.right.value == 0:
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=getattr(node, 'lineno', 0),
                        issue_type="division_by_zero",
                        severity="critical",
                        description="Potential division by zero",
                        suggestion="Add zero check before division"
                    ))
        
        return issues
    
    def run_analysis(self) -> Dict[str, Any]:
        """Run comprehensive code quality analysis"""
        logger.info("Starting comprehensive code quality analysis...")
        
        start_time = time.time()
        python_files = self.find_python_files()
        
        logger.info(f"Found {len(python_files)} Python files to analyze")
        
        file_analyses = []
        total_lines = 0
        
        for file_path in python_files:
            logger.info(f"Analyzing {file_path}")
            analysis = self.analyze_file(file_path)
            file_analyses.append(analysis)
            
            total_lines += analysis.lines_of_code
            self.files_analyzed += 1
            
            # Count issues
            for issue in analysis.issues:
                self.total_issues += 1
                if issue.severity == "critical":
                    self.critical_issues += 1
        
        analysis_time = time.time() - start_time
        
        # Generate report
        report = {
            "summary": {
                "files_analyzed": self.files_analyzed,
                "total_lines_of_code": total_lines,
                "total_issues": self.total_issues,
                "critical_issues": self.critical_issues,
                "analysis_time": analysis_time,
                "average_issues_per_file": self.total_issues / max(self.files_analyzed, 1)
            },
            "file_analyses": [
                {
                    "file_path": analysis.file_path,
                    "lines_of_code": analysis.lines_of_code,
                    "issues_count": len(analysis.issues),
                    "has_syntax_errors": analysis.has_syntax_errors,
                    "complexity_score": analysis.complexity_score,
                    "import_issues": analysis.import_issues
                }
                for analysis in file_analyses
            ],
            "issues_by_severity": self._categorize_issues_by_severity(file_analyses),
            "issues_by_type": self._categorize_issues_by_type(file_analyses),
            "recommendations": self._generate_recommendations(file_analyses)
        }
        
        return report
    
    def _categorize_issues_by_severity(self, file_analyses: List[FileAnalysis]) -> Dict[str, int]:
        """Categorize issues by severity"""
        severity_counts = {"critical": 0, "warning": 0, "info": 0}
        
        for analysis in file_analyses:
            for issue in analysis.issues:
                severity_counts[issue.severity] += 1
        
        return severity_counts
    
    def _categorize_issues_by_type(self, file_analyses: List[FileAnalysis]) -> Dict[str, int]:
        """Categorize issues by type"""
        type_counts = {}
        
        for analysis in file_analyses:
            for issue in analysis.issues:
                issue_type = issue.issue_type
                type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        
        return type_counts
    
    def _generate_recommendations(self, file_analyses: List[FileAnalysis]) -> List[str]:
        """Generate recommendations based on analysis results"""
        recommendations = []
        
        # Check for high complexity files
        high_complexity_files = [f for f in file_analyses if f.complexity_score > 10]
        if high_complexity_files:
            recommendations.append(f"Consider refactoring {len(high_complexity_files)} files with high complexity (>10)")
        
        # Check for files with many issues
        problematic_files = [f for f in file_analyses if len(f.issues) > 5]
        if problematic_files:
            recommendations.append(f"Focus on {len(problematic_files)} files with many issues (>5)")
        
        # Check for syntax errors
        syntax_error_files = [f for f in file_analyses if f.has_syntax_errors]
        if syntax_error_files:
            recommendations.append(f"Fix syntax errors in {len(syntax_error_files)} files")
        
        # Check for import issues
        import_issue_files = [f for f in file_analyses if f.import_issues]
        if import_issue_files:
            recommendations.append(f"Review import statements in {len(import_issue_files)} files")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], filename: str = "code_quality_report.json"):
        """Save analysis report to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

def main():
    """Main function to run code quality analysis"""
    logger.info("🧪 Starting Comprehensive Code Quality Analysis")
    
    # Initialize analyzer
    analyzer = CodeQualityAnalyzer()
    
    # Run analysis
    report = analyzer.run_analysis()
    
    # Save report
    analyzer.save_report(report)
    
    # Print summary
    summary = report["summary"]
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE CODE QUALITY ANALYSIS REPORT")
    print("="*80)
    print(f"📁 Files Analyzed: {summary['files_analyzed']}")
    print(f"📝 Total Lines of Code: {summary['total_lines_of_code']:,}")
    print(f"⚠️ Total Issues Found: {summary['total_issues']}")
    print(f"🚨 Critical Issues: {summary['critical_issues']}")
    print(f"⏱️ Analysis Time: {summary['analysis_time']:.2f}s")
    print(f"📊 Average Issues per File: {summary['average_issues_per_file']:.1f}")
    
    # Print issues by severity
    severity_counts = report["issues_by_severity"]
    print(f"\n📋 Issues by Severity:")
    print(f"  🚨 Critical: {severity_counts['critical']}")
    print(f"  ⚠️ Warning: {severity_counts['warning']}")
    print(f"  ℹ️ Info: {severity_counts['info']}")
    
    # Print issues by type
    type_counts = report["issues_by_type"]
    print(f"\n🔍 Issues by Type:")
    for issue_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {issue_type}: {count}")
    
    # Print recommendations
    if report["recommendations"]:
        print(f"\n💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")
    
    print("\n" + "="*80)
    
    if summary['critical_issues'] == 0:
        logger.info("🎉 No critical issues found! Code quality is good.")
    else:
        logger.warning(f"⚠️ {summary['critical_issues']} critical issues need attention.")
    
    return report

if __name__ == "__main__":
    main() 