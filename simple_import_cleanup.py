#!/usr/bin/env python3
"""
Simple Import Cleanup Tool for KPP Simulator
Provides a list of unused imports for manual cleanup
"""

import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime

class SimpleImportCleaner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.core_files = set()
        
        # Define core application paths
        self.core_paths = [
            'app.py', 'dash_app.py', 'main.py', 'start_server.py', 'start_synchronized_system.py',
            'simulation/engine.py', 'simulation/controller.py', 'simulation/components/',
            'simulation/physics/', 'simulation/control/', 'simulation/managers/',
            'simulation/grid_services/', 'simulation/pneumatics/', 'simulation/monitoring/',
            'simulation/optimization/', 'simulation/logging/', 'simulation/integration/',
            'simulation/future/', 'config/parameter_schema.py', 'config/config.py',
            'config/components/', 'config/core/', 'utils/'
        ]
        
        self.exclude_patterns = [
            '__pycache__', '.pyc', '.pyo', 'test_', '_test.py', 'demo_', 
            'backup_', '_backup', '_old', 'archive', 'docs', 'browser_logs', 
            'logs', 'assets', 'static', 'templates'
        ]
        
    def identify_core_files(self):
        """Identify all core application files"""
        print("Identifying core application files...")
        
        for path_spec in self.core_paths:
            full_path = self.project_root / path_spec
            
            if full_path.is_file():
                if self._should_include_file(full_path):
                    self.core_files.add(full_path)
            elif full_path.is_dir():
                for file_path in full_path.rglob("*.py"):
                    if self._should_include_file(file_path):
                        self.core_files.add(file_path)
        
        print(f"Found {len(self.core_files)} core application files")
        
    def _should_include_file(self, file_path: Path) -> bool:
        """Check if a file should be included in analysis"""
        file_name = file_path.name
        file_str = str(file_path)
        
        for pattern in self.exclude_patterns:
            if pattern in file_name or pattern in file_str:
                return False
        
        return True
    
    def analyze_file_imports(self, file_path: Path) -> Tuple[List[str], Set[str]]:
        """Analyze imports and used names in a file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
            
            # Collect all imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        if alias.name == '*':
                            imports.append(f"{module}.*")
                        else:
                            imports.append(f"{module}.{alias.name}")
            
            # Collect all used names
            used_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    # Handle attribute access (e.g., module.function)
                    parts = []
                    current = node
                    while isinstance(current, ast.Attribute):
                        parts.insert(0, current.attr)
                        current = current.value
                    if isinstance(current, ast.Name):
                        parts.insert(0, current.id)
                        used_names.add('.'.join(parts))
            
            return imports, used_names
            
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
            return [], set()
    
    def find_unused_imports(self):
        """Find unused imports in all core files"""
        print("Analyzing imports for unused references...")
        
        for file_path in sorted(self.core_files):
            imports, used_names = self.analyze_file_imports(file_path)
            
            unused_imports = []
            for imp in imports:
                # Check if import is actually used
                if not self._is_import_used(imp, used_names):
                    unused_imports.append(imp)
            
            if unused_imports:
                self.issues.append({
                    'file': str(file_path),
                    'unused_imports': unused_imports,
                    'total_imports': len(imports),
                    'unused_count': len(unused_imports)
                })
    
    def _is_import_used(self, import_name: str, used_names: Set[str]) -> bool:
        """Check if an import is actually used"""
        # Handle different import patterns
        if import_name in used_names:
            return True
        
        # Handle module imports (e.g., 'numpy' -> 'numpy.array')
        base_name = import_name.split('.')[0]
        for used_name in used_names:
            if used_name.startswith(base_name + '.'):
                return True
        
        # Handle wildcard imports
        if import_name.endswith('.*'):
            base_name = import_name[:-2]
            for used_name in used_names:
                if used_name.startswith(base_name + '.'):
                    return True
        
        return False
    
    def generate_cleanup_report(self):
        """Generate a detailed cleanup report"""
        print("Generating cleanup report...")
        
        report_content = """# Unused Imports Cleanup Report
Generated: {timestamp}

## Summary
- Files with unused imports: {total_files}
- Total unused imports: {total_imports}

## Manual Cleanup Instructions

For each file below, manually remove the listed unused imports.

"""
        
        # Sort issues by unused count (descending)
        sorted_issues = sorted(self.issues, key=lambda x: x['unused_count'], reverse=True)
        
        for i, issue in enumerate(sorted_issues, 1):
            file_path = issue['file']
            unused_imports = issue['unused_imports']
            
            report_content += f"""
## {i}. {file_path}
**Unused imports: {len(unused_imports)}**

Remove these imports:
```
"""
            for imp in unused_imports:
                report_content += f"# {imp}\n"
            
            report_content += "```\n"
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"unused_imports_cleanup_report_{timestamp}.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content.format(
                timestamp=datetime.now().isoformat(),
                total_files=len(self.issues),
                total_imports=sum(issue['unused_count'] for issue in self.issues)
            ))
        
        print(f"Cleanup report saved to: {report_path}")
        return report_path
    
    def run_analysis(self):
        """Run the complete unused imports analysis"""
        print("Starting unused imports analysis...")
        
        self.identify_core_files()
        self.find_unused_imports()
        
        # Generate summary
        total_files_with_issues = len(self.issues)
        total_unused_imports = sum(issue['unused_count'] for issue in self.issues)
        
        print(f"\nUNUSED IMPORTS ANALYSIS SUMMARY")
        print(f"=" * 50)
        print(f"Files with unused imports: {total_files_with_issues}")
        print(f"Total unused imports: {total_unused_imports}")
        
        if self.issues:
            print(f"\nTOP FILES WITH UNUSED IMPORTS:")
            sorted_issues = sorted(self.issues, key=lambda x: x['unused_count'], reverse=True)
            for i, issue in enumerate(sorted_issues[:10], 1):
                print(f"  {i}. {issue['file']}: {issue['unused_count']} unused imports")
        
        # Generate cleanup report
        if self.issues:
            report_path = self.generate_cleanup_report()
            print(f"\nTo clean up unused imports:")
            print(f"  1. Review the report: {report_path}")
            print(f"  2. Manually remove unused imports from each file")
            print(f"  3. Test the application after each file cleanup")
        
        return {
            'total_files_analyzed': len(self.core_files),
            'files_with_issues': total_files_with_issues,
            'total_unused_imports': total_unused_imports,
            'issues': self.issues
        }

def main():
    """Main function"""
    project_root = os.getcwd()
    
    cleaner = SimpleImportCleaner(project_root)
    results = cleaner.run_analysis()
    
    # Save detailed report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"unused_imports_analysis_{timestamp}.json"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_path}")

if __name__ == "__main__":
    main() 