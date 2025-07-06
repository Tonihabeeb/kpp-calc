#!/usr/bin/env python3
"""
Core Application Static Analysis Tool for KPP Simulator
Comprehensive analysis focused on essential application files only
"""

import os
import ast
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Set
import logging

class CoreApplicationAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.metrics = {}
        self.core_files = set()
        self.analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'project': str(self.project_root),
            'summary': {},
            'core_files_analyzed': [],
            'issues': [],
            'metrics': {},
            'architecture_analysis': {},
            'recommendations': [],
            'code_quality_score': 0.0
        }
        
        # Define core application files and directories
        self.core_paths = [
            'app.py',
            'dash_app.py', 
            'main.py',
            'start_server.py',
            'start_synchronized_system.py',
            'simulation/engine.py',
            'simulation/controller.py',
            'simulation/components/',
            'simulation/physics/',
            'simulation/control/',
            'simulation/managers/',
            'simulation/grid_services/',
            'simulation/pneumatics/',
            'simulation/monitoring/',
            'simulation/optimization/',
            'simulation/logging/',
            'simulation/integration/',
            'simulation/future/',
            'config/parameter_schema.py',
            'config/config.py',
            'config/components/',
            'config/core/',
            'utils/'
        ]
        
        # Files to exclude (even if in core directories)
        self.exclude_patterns = [
            '__pycache__',
            '.pyc',
            '.pyo',
            'test_',
            '_test.py',
            'demo_',
            'backup_',
            '_backup',
            '_old',
            'archive',
            'docs',
            'browser_logs',
            'logs',
            'assets',
            'static',
            'templates'
        ]
        
    def identify_core_files(self):
        """Identify all core application files"""
        print("🔍 Identifying core application files...")
        
        for path_spec in self.core_paths:
            full_path = self.project_root / path_spec
            
            if full_path.is_file():
                if self._should_include_file(full_path):
                    self.core_files.add(full_path)
            elif full_path.is_dir():
                for file_path in full_path.rglob("*.py"):
                    if self._should_include_file(file_path):
                        self.core_files.add(file_path)
        
        self.metrics['core_files_count'] = len(self.core_files)
        print(f"✅ Found {len(self.core_files)} core application files")
        
    def _should_include_file(self, file_path: Path) -> bool:
        """Check if a file should be included in analysis"""
        file_name = file_path.name
        file_str = str(file_path)
        
        # Check exclusion patterns
        for pattern in self.exclude_patterns:
            if pattern in file_name or pattern in file_str:
                return False
        
        return True
    
    def analyze_core_files(self):
        """Analyze all identified core files"""
        print("📊 Analyzing core application files...")
        
        self.metrics['total_lines'] = 0
        self.metrics['total_functions'] = 0
        self.metrics['total_classes'] = 0
        self.metrics['total_imports'] = 0
        self.metrics['complexity_scores'] = []
        
        file_analysis = []
        
        for file_path in sorted(self.core_files):
            try:
                file_result = self._analyze_single_core_file(file_path)
                file_analysis.append(file_result)
                self.metrics['total_lines'] += file_result['lines_of_code']
                self.metrics['total_functions'] += file_result['function_count']
                self.metrics['total_classes'] += file_result['class_count']
                self.metrics['total_imports'] += file_result['import_count']
                if file_result['complexity_score'] > 0:
                    self.metrics['complexity_scores'].append(file_result['complexity_score'])
                
            except Exception as e:
                self.issues.append({
                    'file': str(file_path),
                    'type': 'analysis_error',
                    'severity': 'error',
                    'message': f'Failed to analyze: {str(e)}',
                    'line': 0
                })
        
        self.analysis_results['core_files_analyzed'] = file_analysis
        
    def _analyze_single_core_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single core file in detail"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        try:
            tree = ast.parse(content)
            
            # Basic metrics
            function_count = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
            class_count = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
            import_count = len([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))])
            
            # Complexity analysis
            complexity_score = self._calculate_complexity(tree)
            
            # Detailed analysis
            self._analyze_ast_detailed(file_path, tree, lines)
            
            return {
                'file_path': str(file_path.relative_to(self.project_root)),
                'lines_of_code': len(lines),
                'function_count': function_count,
                'class_count': class_count,
                'import_count': import_count,
                'complexity_score': complexity_score,
                'has_syntax_errors': False,
                'issues_count': len([i for i in self.issues if i['file'] == str(file_path)])
            }
            
        except SyntaxError as e:
            self.issues.append({
                'file': str(file_path),
                'type': 'syntax_error',
                'severity': 'error',
                'message': f'Syntax error: {str(e)}',
                'line': e.lineno or 0
            })
            
            return {
                'file_path': str(file_path.relative_to(self.project_root)),
                'lines_of_code': len(lines),
                'function_count': 0,
                'class_count': 0,
                'import_count': 0,
                'complexity_score': 0,
                'has_syntax_errors': True,
                'issues_count': 1
            }
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _analyze_ast_detailed(self, file_path: Path, tree: ast.AST, lines: List[str]):
        """Detailed AST analysis for core files"""
        for node in ast.walk(tree):
            # Check for long functions
            if isinstance(node, ast.FunctionDef):
                if len(node.body) > 50:
                    self.issues.append({
                        'file': str(file_path),
                        'type': 'long_function',
                        'severity': 'warning',
                        'message': f'Function {node.name} is long ({len(node.body)} lines)',
                        'line': node.lineno
                    })
                
                # Check for complex functions
                func_complexity = self._calculate_complexity(node)
                if func_complexity > 10:
                    self.issues.append({
                        'file': str(file_path),
                        'type': 'complex_function',
                        'severity': 'warning',
                        'message': f'Function {node.name} is complex (complexity: {func_complexity})',
                        'line': node.lineno
                    })
            
            # Check for long lines
            if hasattr(node, 'lineno') and node.lineno <= len(lines):
                line_content = lines[node.lineno - 1]
                if len(line_content) > 120:
                    self.issues.append({
                        'file': str(file_path),
                        'type': 'long_line',
                        'severity': 'warning',
                        'message': f'Line too long ({len(line_content)} chars)',
                        'line': node.lineno
                    })
            
            # Check for unused imports (basic check)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not self._is_import_used(alias.name, tree):
                        self.issues.append({
                            'file': str(file_path),
                            'type': 'unused_import',
                            'severity': 'warning',
                            'message': f'Unused import: {alias.name}',
                            'line': node.lineno
                        })
    
    def _is_import_used(self, import_name: str, tree: ast.AST) -> bool:
        """Check if an import is actually used"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == import_name:
                return True
        return False
    
    def analyze_architecture(self):
        """Analyze the overall architecture and dependencies"""
        print("🏗️  Analyzing application architecture...")
        
        architecture = {
            'modules': {},
            'dependencies': {},
            'entry_points': [],
            'core_components': []
        }
        
        # Identify entry points
        entry_files = ['app.py', 'dash_app.py', 'main.py', 'start_server.py']
        for file_name in entry_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                architecture['entry_points'].append(file_name)
        
        # Analyze module structure
        for file_path in self.core_files:
            rel_path = file_path.relative_to(self.project_root)
            module_name = str(rel_path).replace('\\', '/').replace('.py', '')
            
            if 'simulation' in module_name:
                architecture['core_components'].append(module_name)
            
            architecture['modules'][module_name] = {
                'path': str(rel_path),
                'size': file_path.stat().st_size,
                'type': self._classify_module(module_name)
            }
        
        self.analysis_results['architecture_analysis'] = architecture
    
    def _classify_module(self, module_name: str) -> str:
        """Classify module type"""
        if 'simulation/engine' in module_name:
            return 'core_engine'
        elif 'simulation/components' in module_name:
            return 'physics_component'
        elif 'simulation/physics' in module_name:
            return 'physics_engine'
        elif 'simulation/control' in module_name:
            return 'integrated_control_system'
        elif 'simulation/managers' in module_name:
            return 'system_manager'
        elif 'config' in module_name:
            return 'configuration'
        elif 'utils' in module_name:
            return 'utility'
        elif module_name in ['app.py', 'dash_app.py']:
            return 'entry_point'
        else:
            return 'other'
    
    def calculate_quality_score(self):
        """Calculate overall code quality score"""
        print("📈 Calculating code quality score...")
        
        total_issues = len(self.issues)
        error_count = sum(1 for i in self.issues if i['severity'] == 'error')
        warning_count = sum(1 for i in self.issues if i['severity'] == 'warning')
        
        # Base score starts at 100
        score = 100.0
        
        # Deduct points for errors (more severe)
        score -= error_count * 10
        
        # Deduct points for warnings (less severe)
        score -= warning_count * 2
        
        # Bonus for good practices
        if self.metrics.get('total_files_count', 0) > 0:
            avg_complexity = sum(self.metrics.get('complexity_scores', [])) / len(self.metrics.get('complexity_scores', [1]))
            if avg_complexity < 5:
                score += 10  # Bonus for low complexity
            elif avg_complexity > 15:
                score -= 10  # Penalty for high complexity
        
        # Ensure score is between 0 and 100
        score = max(0.0, min(100.0, score))
        
        self.analysis_results['code_quality_score'] = score
    
    def generate_recommendations(self):
        """Generate specific recommendations based on analysis"""
        print("💡 Generating recommendations...")
        
        recommendations = []
        
        # Count issues by type
        issue_types = {}
        severity_counts = {'error': 0, 'warning': 0, 'info': 0}
        
        for issue in self.issues:
            issue_types[issue['type']] = issue_types.get(issue['type'], 0) + 1
            severity_counts[issue['severity']] += 1
        
        # Generate specific recommendations
        if severity_counts['error'] > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'critical',
                'message': f"Fix {severity_counts['error']} syntax/analysis errors first",
                'action': 'Review and fix all error-level issues before deployment'
            })
        
        if issue_types.get('long_function', 0) > 5:
            recommendations.append({
                'priority': 'medium',
                'category': 'maintainability',
                'message': f"Break down {issue_types['long_function']} long functions",
                'action': 'Refactor functions longer than 50 lines into smaller, focused functions'
            })
        
        if issue_types.get('complex_function', 0) > 3:
            recommendations.append({
                'priority': 'medium',
                'category': 'complexity',
                'message': f"Simplify {issue_types['complex_function']} complex functions",
                'action': 'Reduce cyclomatic complexity in functions with complexity > 10'
            })
        
        if issue_types.get('long_line', 0) > 20:
            recommendations.append({
                'priority': 'low',
                'category': 'style',
                'message': f"Break {issue_types['long_line']} long lines for readability",
                'action': 'Keep lines under 120 characters for better readability'
            })
        
        if issue_types.get('unused_import', 0) > 5:
            recommendations.append({
                'priority': 'low',
                'category': 'cleanup',
                'message': f"Remove {issue_types['unused_import']} unused imports",
                'action': 'Clean up unused imports to improve code clarity'
            })
        
        # Architecture recommendations
        if self.metrics.get('total_files_count', 0) > 50:
            recommendations.append({
                'priority': 'medium',
                'category': 'architecture',
                'message': 'Large codebase detected - consider modularization',
                'action': 'Review module boundaries and consider breaking large modules'
            })
        
        if not recommendations:
            recommendations.append({
                'priority': 'low',
                'category': 'maintenance',
                'message': 'Code quality is good!',
                'action': 'Continue with current development practices'
            })
        
        self.analysis_results['recommendations'] = recommendations
    
    def run_comprehensive_analysis(self):
        """Run the complete core application analysis"""
        print("🚀 Starting comprehensive core application analysis...")
        start_time = time.time()
        
        # Step 1: Identify core files
        self.identify_core_files()
        
        # Step 2: Analyze core files
        self.analyze_core_files()
        
        # Step 3: Analyze architecture
        self.analyze_architecture()
        
        # Step 4: Calculate quality score
        self.calculate_quality_score()
        
        # Step 5: Generate recommendations
        self.generate_recommendations()
        
        # Compile final results
        self.analysis_results['issues'] = self.issues
        self.analysis_results['metrics'] = self.metrics
        
        # Generate summary
        self.analysis_results['summary'] = {
            'core_files_analyzed': self.metrics.get('core_files_count', 0),
            'total_lines_of_code': self.metrics.get('total_lines', 0),
            'total_issues': len(self.issues),
            'error_count': sum(1 for i in self.issues if i['severity'] == 'error'),
            'warning_count': sum(1 for i in self.issues if i['severity'] == 'warning'),
            'info_count': sum(1 for i in self.issues if i['severity'] == 'info'),
            'code_quality_score': self.analysis_results['code_quality_score'],
            'analysis_time_seconds': time.time() - start_time
        }
        
        return self.analysis_results
    
    def save_report(self, filename: str = None):
        """Save analysis report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"core_application_analysis_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)
        
        print(f"📄 Analysis report saved to: {filename}")
        return filename

def main():
    """Main function to run core application analysis"""
    project_root = os.getcwd()
    
    analyzer = CoreApplicationAnalyzer(project_root)
    report = analyzer.run_comprehensive_analysis()
    
    # Print comprehensive summary
    print("\n" + "="*80)
    print("🎯 CORE APPLICATION ANALYSIS SUMMARY")
    print("="*80)
    print(f"Project: {report['project']}")
    print(f"Analysis Time: {report['timestamp']}")
    print(f"Core Files Analyzed: {report['summary']['core_files_analyzed']}")
    print(f"Total Lines of Code: {report['summary']['total_lines_of_code']:,}")
    print(f"Code Quality Score: {report['summary']['code_quality_score']:.1f}/100")
    print(f"Analysis Duration: {report['summary']['analysis_time_seconds']:.2f} seconds")
    
    print(f"\n📊 ISSUES SUMMARY:")
    print(f"  Total Issues: {report['summary']['total_issues']}")
    print(f"  Errors: {report['summary']['error_count']}")
    print(f"  Warnings: {report['summary']['warning_count']}")
    print(f"  Info: {report['summary']['info_count']}")
    
    print(f"\n🏗️  ARCHITECTURE SUMMARY:")
    arch = report['architecture_analysis']
    print(f"  Entry Points: {len(arch['entry_points'])}")
    print(f"  Core Components: {len(arch['core_components'])}")
    print(f"  Total Modules: {len(arch['modules'])}")
    
    if report['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. [{rec['priority'].upper()}] {rec['message']}")
            print(f"     Action: {rec['action']}")
    
    # Save detailed report
    filename = analyzer.save_report()
    
    print(f"\n📄 Detailed report saved to: {filename}")
    print("✅ Core application analysis complete!")

if __name__ == "__main__":
    main() 