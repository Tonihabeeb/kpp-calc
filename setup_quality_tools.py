#!/usr/bin/env python3
"""
Automated Quality Tools Setup for KPP Simulator
Sets up DeepSource, linting, and formatting tools for ongoing code quality
"""

import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

class QualityToolsSetup:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.setup_results = {
            'timestamp': datetime.now().isoformat(),
            'tools_installed': [],
            'configs_created': [],
            'errors': [],
            'recommendations': []
        }
    
    def install_python_tools(self):
        """Install Python code quality tools"""
        print("Installing Python code quality tools...")
        
        tools = [
            'black',           # Code formatter
            'flake8',          # Linter
            'autopep8',        # Auto-formatter
            'mypy',           # Type checker
            'pylint',         # Advanced linter
            'isort',          # Import sorter
            'autoflake',      # Remove unused imports
        ]
        
        for tool in tools:
            try:
                print(f"Installing {tool}...")
                result = subprocess.run(
                    ['pip', 'install', tool],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    self.setup_results['tools_installed'].append(tool)
                    print(f"  ✅ {tool} installed successfully")
                else:
                    self.setup_results['errors'].append(f"Failed to install {tool}: {result.stderr}")
                    print(f"  ❌ {tool} installation failed")
                    
            except Exception as e:
                self.setup_results['errors'].append(f"Error installing {tool}: {str(e)}")
                print(f"  ❌ {tool} installation error: {e}")
    
    def create_pyproject_toml(self):
        """Create pyproject.toml with tool configurations"""
        print("Creating pyproject.toml configuration...")
        
        config = """[tool.black]
line-length = 120
target-version = ['py39']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # directories
  \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 120
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.pylint.messages_control]
disable = [
    "C0114",  # missing-module-docstring
    "C0115",  # missing-class-docstring
    "C0116",  # missing-function-docstring
    "R0903",  # too-few-public-methods
    "R0913",  # too-many-arguments
    "R0914",  # too-many-locals
    "R0915",  # too-many-statements
    "W0621",  # redefined-outer-name
    "W0703",  # broad-except
]

[tool.pylint.format]
max-line-length = 120

[tool.pylint.design]
max-args = 10
max-locals = 20
max-returns = 10
max-statements = 50
"""
        
        config_path = self.project_root / "pyproject.toml"
        try:
            with open(config_path, 'w') as f:
                f.write(config)
            
            self.setup_results['configs_created'].append('pyproject.toml')
            print("  ✅ pyproject.toml created successfully")
            
        except Exception as e:
            self.setup_results['errors'].append(f"Failed to create pyproject.toml: {str(e)}")
            print(f"  ❌ Failed to create pyproject.toml: {e}")
    
    def create_flake8_config(self):
        """Create .flake8 configuration"""
        print("Creating .flake8 configuration...")
        
        config = """[flake8]
max-line-length = 120
exclude = 
    .git,
    __pycache__,
    .venv,
    build,
    dist,
    *.egg-info,
    tests,
    validation,
    archive,
    backup,
    docs,
    browser_logs,
    logs,
    assets,
    static,
    templates
ignore = 
    E203,  # whitespace before ':'
    E501,  # line too long (handled by black)
    W503,  # line break before binary operator
    F401,  # imported but unused (handled by autoflake)
    F403,  # wildcard import
    F405,  # name may be undefined, or defined from star imports
"""
        
        config_path = self.project_root / ".flake8"
        try:
            with open(config_path, 'w') as f:
                f.write(config)
            
            self.setup_results['configs_created'].append('.flake8')
            print("  ✅ .flake8 created successfully")
            
        except Exception as e:
            self.setup_results['errors'].append(f"Failed to create .flake8: {str(e)}")
            print(f"  ❌ Failed to create .flake8: {e}")
    
    def create_deepsource_config(self):
        """Create .deepsource.toml configuration for DeepSource"""
        print("Creating DeepSource configuration...")
        
        config = """version = 1

[[analyzers]]
name = "python"
enabled = true

[[analyzers]]
name = "test-coverage"
enabled = true

[[analyzers]]
name = "secrets"
enabled = true

[[analyzers]]
name = "dependency"
enabled = true

[python]
python_version = ["3.9"]

[python.test_patterns]
  - "tests/**/*.py"
  - "test_*.py"
  - "*_test.py"

[python.coverage]
  - "simulation/**/*.py"
  - "config/**/*.py"
  - "utils/**/*.py"
  - "app.py"
  - "dash_app.py"
  - "main.py"

[python.ignore_patterns]
  - "tests/**/*"
  - "validation/**/*"
  - "archive/**/*"
  - "backup/**/*"
  - "docs/**/*"
  - "browser_logs/**/*"
  - "logs/**/*"
  - "assets/**/*"
  - "static/**/*"
  - "templates/**/*"
  - "**/__pycache__/**"
  - "**/*.pyc"
  - "**/*.pyo"
"""
        
        config_path = self.project_root / ".deepsource.toml"
        try:
            with open(config_path, 'w') as f:
                f.write(config)
            
            self.setup_results['configs_created'].append('.deepsource.toml')
            print("  ✅ .deepsource.toml created successfully")
            
        except Exception as e:
            self.setup_results['errors'].append(f"Failed to create .deepsource.toml: {str(e)}")
            print(f"  ❌ Failed to create .deepsource.toml: {e}")
    
    def create_pre_commit_config(self):
        """Create pre-commit configuration"""
        print("Creating pre-commit configuration...")
        
        config = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
"""
        
        config_path = self.project_root / ".pre-commit-config.yaml"
        try:
            with open(config_path, 'w') as f:
                f.write(config)
            
            self.setup_results['configs_created'].append('.pre-commit-config.yaml')
            print("  ✅ .pre-commit-config.yaml created successfully")
            
        except Exception as e:
            self.setup_results['errors'].append(f"Failed to create .pre-commit-config.yaml: {str(e)}")
            print(f"  ❌ Failed to create .pre-commit-config.yaml: {e}")
    
    def create_quality_scripts(self):
        """Create quality check and fix scripts"""
        print("Creating quality check scripts...")
        
        # Quality check script
        check_script = """#!/usr/bin/env python3
\"\"\"
Code Quality Check Script for KPP Simulator
Run this script to check code quality before commits
\"\"\"

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    print(f"\\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ {description} passed")
            return True
        else:
            print(f"  ❌ {description} failed:")
            print(result.stdout)
            print(result.stderr)
            return False
        except Exception as e:
            print(f"  ❌ {description} error: {e}")
            return False

def main():
    print("🔍 Running Code Quality Checks...")
    
    # Check if tools are installed
    tools = ['black', 'flake8', 'mypy', 'isort']
    missing_tools = []
    
    for tool in tools:
        try:
            subprocess.run([tool, '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"❌ Missing tools: {', '.join(missing_tools)}")
        print("Run: python setup_quality_tools.py")
        sys.exit(1)
    
    # Run checks
    checks = [
        ("black --check simulation/ config/ utils/ app.py dash_app.py main.py", "Code formatting"),
        ("flake8 simulation/ config/ utils/ app.py dash_app.py main.py", "Code linting"),
        ("isort --check-only simulation/ config/ utils/ app.py dash_app.py main.py", "Import sorting"),
        ("mypy simulation/ config/ utils/ app.py dash_app.py main.py", "Type checking")
    ]
    
    all_passed = True
    for cmd, desc in checks:
        if not run_command(cmd, desc):
            all_passed = False
    
    if all_passed:
        print("\\n🎉 All quality checks passed!")
        sys.exit(0)
    else:
        print("\\n❌ Some quality checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
        
        # Quality fix script
        fix_script = """#!/usr/bin/env python3
\"\"\"
Code Quality Fix Script for KPP Simulator
Run this script to automatically fix code quality issues
\"\"\"

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    print(f"\\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ {description} completed")
            return True
        else:
            print(f"  ❌ {description} failed:")
            print(result.stdout)
            print(result.stderr)
            return False
        except Exception as e:
            print(f"  ❌ {description} error: {e}")
            return False

def main():
    print("🔧 Running Code Quality Fixes...")
    
    # Run fixes
    fixes = [
        ("black simulation/ config/ utils/ app.py dash_app.py main.py", "Code formatting"),
        ("isort simulation/ config/ utils/ app.py dash_app.py main.py", "Import sorting"),
        ("autoflake --in-place --remove-all-unused-imports --remove-unused-variables --recursive simulation/ config/ utils/ app.py dash_app.py main.py", "Remove unused imports")
    ]
    
    all_successful = True
    for cmd, desc in fixes:
        if not run_command(cmd, desc):
            all_successful = False
    
    if all_successful:
        print("\\n🎉 All quality fixes completed!")
        print("\\n💡 Run quality_check.py to verify the fixes.")
    else:
        print("\\n❌ Some quality fixes failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
        
        scripts = [
            ("quality_check.py", check_script),
            ("quality_fix.py", fix_script)
        ]
        
        for filename, content in scripts:
            script_path = self.project_root / filename
            try:
                with open(script_path, 'w') as f:
                    f.write(content)
                
                # Make executable on Unix systems
                script_path.chmod(0o755)
                
                self.setup_results['configs_created'].append(filename)
                print(f"  ✅ {filename} created successfully")
                
            except Exception as e:
                self.setup_results['errors'].append(f"Failed to create {filename}: {str(e)}")
                print(f"  ❌ Failed to create {filename}: {e}")
    
    def setup_deepsource_instructions(self):
        """Provide DeepSource setup instructions"""
        instructions = """
## DeepSource Setup Instructions

### 1. Install DeepSource CLI
```bash
# For Windows (using pip)
pip install deepsource-cli

# Or download from https://deepsource.io/cli/
```

### 2. Initialize DeepSource
```bash
# Initialize DeepSource in your repository
deepsource init

# This will create a .deepsource.toml file (already created above)
```

### 3. Run DeepSource Analysis
```bash
# Run analysis locally
deepsource analyze

# Or run specific analyzers
deepsource analyze --analyzer python
deepsource analyze --analyzer test-coverage
```

### 4. Set Up DeepSource Dashboard
1. Go to https://deepsource.io/
2. Sign up and connect your repository
3. DeepSource will automatically analyze your code
4. View issues and suggestions in the dashboard

### 5. Configure GitHub Integration (Optional)
1. Install DeepSource GitHub App
2. Enable automatic analysis on pull requests
3. Get real-time feedback on code changes

### 6. Customize Analysis
Edit .deepsource.toml to:
- Enable/disable specific analyzers
- Configure analysis rules
- Set up test coverage patterns
- Ignore specific files or patterns
"""
        
        instructions_path = self.project_root / "DEEPSOURCE_SETUP.md"
        try:
            with open(instructions_path, 'w') as f:
                f.write(instructions)
            
            self.setup_results['configs_created'].append('DEEPSOURCE_SETUP.md')
            print("  ✅ DEEPSOURCE_SETUP.md created successfully")
            
        except Exception as e:
            self.setup_results['errors'].append(f"Failed to create DEEPSOURCE_SETUP.md: {str(e)}")
            print(f"  ❌ Failed to create DEEPSOURCE_SETUP.md: {e}")
    
    def run_setup(self):
        """Run the complete quality tools setup"""
        print("🚀 Setting up automated quality tools...")
        
        # Install tools
        self.install_python_tools()
        
        # Create configurations
        self.create_pyproject_toml()
        self.create_flake8_config()
        self.create_deepsource_config()
        self.create_pre_commit_config()
        
        # Create scripts
        self.create_quality_scripts()
        
        # Setup instructions
        self.setup_deepsource_instructions()
        
        # Generate recommendations
        self.setup_results['recommendations'] = [
            "Run 'python quality_fix.py' to automatically fix code style issues",
            "Run 'python quality_check.py' before commits to ensure quality",
            "Set up pre-commit hooks: pip install pre-commit && pre-commit install",
            "Follow DEEPSOURCE_SETUP.md to configure DeepSource dashboard",
            "Consider setting up CI/CD pipeline with quality checks"
        ]
        
        return self.setup_results
    
    def save_report(self, filename: str = None):
        """Save setup report"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"quality_tools_setup_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.setup_results, f, indent=2)
        
        print(f"Setup report saved to: {filename}")
        return filename

def main():
    """Main function"""
    project_root = os.getcwd()
    
    setup = QualityToolsSetup(project_root)
    results = setup.run_setup()
    
    # Print summary
    print(f"\n{'='*60}")
    print("QUALITY TOOLS SETUP SUMMARY")
    print(f"{'='*60}")
    print(f"Tools installed: {len(results['tools_installed'])}")
    print(f"Configs created: {len(results['configs_created'])}")
    print(f"Errors: {len(results['errors'])}")
    
    if results['tools_installed']:
        print(f"\n✅ Installed tools: {', '.join(results['tools_installed'])}")
    
    if results['configs_created']:
        print(f"\n📄 Created configs: {', '.join(results['configs_created'])}")
    
    if results['errors']:
        print(f"\n❌ Errors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    if results['recommendations']:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    # Save report
    setup.save_report()
    
    print(f"\n🎉 Quality tools setup completed!")

if __name__ == "__main__":
    main() 