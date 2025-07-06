#!/usr/bin/env python3
"""
Unused Imports Cleanup Tool for KPP Simulator
Automatically detects and removes unused imports from core application files
"""

import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging

class UnusedImportsCleaner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.fixes_applied = []
        self.core_files = set()
        
        # Define core application paths (same as analyzer)
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
        
        print(f"✅ Found {len(self.core_files)} core application files")
        
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
            print(f"⚠️  Syntax error in {file_path}: {e}")
            return [], set()
    
    def find_unused_imports(self):
        """Find unused imports in all core files"""
        print("🔍 Analyzing imports for unused references...")
        
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
    
    def generate_cleanup_script(self):
        """Generate a script to clean up unused imports"""
        print("📝 Generating cleanup script...")
        
        script_content = """#!/usr/bin/env python3
\"\"\"
Auto-generated cleanup script for unused imports
Generated by UnusedImportsCleaner
\"\"\"

import ast
import re
from pathlib import Path

def remove_unused_imports(file_path: str, unused_imports: list):
    \"\"\"Remove unused imports from a file\"\"\"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\\n')
    
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this is an import line
        if line.startswith('import ') or line.startswith('from '):
            # Check if this import should be removed
            should_remove = False
            for unused in unused_imports:
                if unused in line:
                    should_remove = True
                    break
            
            if should_remove:
                # Skip this line
                i += 1
                continue
        
        new_lines.append(lines[i])
        i += 1
    
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\\n'.join(new_lines))

# Cleanup operations
"""
        
        for issue in self.issues:
            file_path = issue['file']
            unused_imports = issue['unused_imports']
            
            safe_name = file_path.replace('/', '_').replace('\\', '_').replace('.py', '')
        script_content += f"""
# Cleanup {file_path}
unused_imports_{safe_name} = {unused_imports}
remove_unused_imports(r'{file_path}', unused_imports_{safe_name})
print(f"Cleaned up {{len(unused_imports_{safe_name})}} unused imports in {file_path}")
"""
        
        script_content += """
print("\\n✅ Unused imports cleanup completed!")
"""
        
        # Save the script
        script_path = self.project_root / "cleanup_unused_imports_auto.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        print(f"📄 Cleanup script saved to: {script_path}")
        return script_path
    
    def run_analysis(self):
        """Run the complete unused imports analysis"""
        print("🚀 Starting unused imports analysis...")
        
        self.identify_core_files()
        self.find_unused_imports()
        
        # Generate summary
        total_files_with_issues = len(self.issues)
        total_unused_imports = sum(issue['unused_count'] for issue in self.issues)
        
        print(f"\n📊 UNUSED IMPORTS ANALYSIS SUMMARY")
        print(f"=" * 50)
        print(f"Files with unused imports: {total_files_with_issues}")
        print(f"Total unused imports: {total_unused_imports}")
        
        if self.issues:
            print(f"\n📋 TOP FILES WITH UNUSED IMPORTS:")
            sorted_issues = sorted(self.issues, key=lambda x: x['unused_count'], reverse=True)
            for i, issue in enumerate(sorted_issues[:10], 1):
                print(f"  {i}. {issue['file']}: {issue['unused_count']} unused imports")
        
        # Generate cleanup script
        if self.issues:
            script_path = self.generate_cleanup_script()
            print(f"\n💡 To clean up unused imports, run:")
            print(f"   python {script_path}")
        
        return {
            'total_files_analyzed': len(self.core_files),
            'files_with_issues': total_files_with_issues,
            'total_unused_imports': total_unused_imports,
            'issues': self.issues
        }

def main():
    """Main function"""
    project_root = os.getcwd()
    
    cleaner = UnusedImportsCleaner(project_root)
    results = cleaner.run_analysis()
    
    # Save detailed report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"unused_imports_analysis_{timestamp}.json"
    
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_path}")

if __name__ == "__main__":
    from datetime import datetime
    main() 