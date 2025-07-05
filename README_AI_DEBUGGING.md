# KPP Simulator AI Debugging Integration

## Overview

This directory contains the AI debugging integration for the KPP (Kinetic Power Plant) Simulator. The integration provides a two-layered approach to code quality and debugging:

1. **DeepSource**: Automated static code analysis
2. **Workik**: Interactive AI-assisted debugging
3. **Custom Tools**: Performance monitoring and thread safety analysis

## Quick Start

### 1. Install Dependencies

```bash
# Install DeepSource CLI
pip install deepsource

# Install additional debugging tools
pip install -r requirements-debugging.txt
```

### 2. Run Static Analysis

```bash
# Run DeepSource analysis
python deepsource_analysis_runner.py

# Or run directly with DeepSource CLI
deepsource analyze
```

### 3. Run AI Debugging Workflow

```bash
# Run comprehensive debugging analysis
python debugging_workflow.py
```

## Configuration Files

### `.deepsource.toml`
Configuration file for DeepSource static analysis:
- Python analyzer enabled
- Test coverage analyzer enabled
- Framework-specific rules for Flask, Dash, NumPy, SciPy
- Custom exclude patterns for logs and test files
- Performance and security rules

### `ai_debugging_guide.md`
Comprehensive guide explaining:
- Repository analysis and architecture
- Critical issues identified
- Workik context configuration
- Simulated debugging workflows
- Code refactoring examples

## Tools and Scripts

### `deepsource_analysis_runner.py`
Automated DeepSource analysis runner that:
- Checks DeepSource installation
- Runs static analysis
- Applies automatic fixes
- Generates detailed reports
- Categorizes issues by severity

### `debugging_workflow.py`
AI debugging workflow implementation:
- Static code analysis simulation
- Performance monitoring
- Thread safety analysis
- Memory usage tracking
- Issue categorization and recommendations

## Key Features

### 1. Static Analysis (DeepSource)
- **Bug Detection**: Identifies potential runtime errors
- **Security Issues**: Finds security vulnerabilities
- **Performance Problems**: Detects inefficient code patterns
- **Style Violations**: Ensures code consistency
- **Automatic Fixes**: Applies safe automatic corrections

### 2. Interactive Debugging (Workik)
- **Context-Aware Analysis**: Understands KPP simulator architecture
- **Intelligent Breakpoints**: Suggests optimal debugging points
- **Variable Tracking**: Monitors critical simulation variables
- **Edge Case Detection**: Identifies potential failure scenarios
- **AI Suggestions**: Provides intelligent code improvement recommendations

### 3. Performance Monitoring
- **Memory Usage Tracking**: Monitors state dictionary sizes
- **Execution Time Analysis**: Measures function performance
- **Thread Safety Analysis**: Identifies race conditions
- **Resource Leak Detection**: Finds memory and resource leaks

## Critical Issues Identified

### 1. Simulation Engine (`simulation/engine.py`)
- **Unhandled Exceptions**: Complex physics calculations without proper error handling
- **Memory Leaks**: Large state dictionaries accumulating in memory
- **Thread Safety**: Global state mutations without proper synchronization

### 2. Web Server (`app.py`)
- **Blocking Operations**: Synchronous simulation operations in Flask routes
- **Error Handling**: Missing exception handling in API endpoints
- **Resource Management**: No limits on concurrent requests

### 3. Configuration System (`config/`)
- **Validation**: Missing input validation for configuration parameters
- **Type Safety**: Insufficient type checking for complex configurations

## Usage Examples

### Running DeepSource Analysis

```python
from deepsource_analysis_runner import DeepSourceAnalyzer

# Initialize analyzer
analyzer = DeepSourceAnalyzer()

# Run analysis
results = analyzer.run_analysis()

# Apply fixes
fixes = analyzer.apply_autofixes()

# Generate report
report = analyzer.generate_report()
```

### Using AI Debugging Workflow

```python
from debugging_workflow import AIDebuggingWorkflow

# Initialize workflow
workflow = AIDebuggingWorkflow()

# Run static analysis
issues = workflow.run_static_analysis()

# Run performance analysis
metrics = workflow.run_performance_analysis(simulation_function)

# Generate comprehensive report
report = workflow.generate_report()
```

### Thread-Safe State Management

```python
from debugging_workflow import ThreadSafeStateManager

# Initialize with memory limits
state_manager = ThreadSafeStateManager(max_size=1000)

# Add state with automatic cleanup
state_manager.add_state({
    "time": time.time(),
    "power": 100.0,
    "status": "running"
})
```

## Best Practices

### 1. Code Quality
- Run DeepSource analysis before each commit
- Address critical issues immediately
- Apply automatic fixes when available
- Review and test manual fixes thoroughly

### 2. Performance
- Monitor memory usage during long simulations
- Use thread-safe data structures for global state
- Implement proper cleanup for large objects
- Set performance thresholds and monitor violations

### 3. Debugging
- Use Workik context for complex debugging sessions
- Set breakpoints at critical decision points
- Monitor variable state changes
- Document edge cases and failure scenarios

### 4. Testing
- Run debugging workflow as part of CI/CD pipeline
- Validate fixes with existing test suite
- Test performance improvements under load
- Verify thread safety in multi-threaded scenarios

## Integration with Development Workflow

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run DeepSource analysis
python deepsource_analysis_runner.py

# Check for critical issues
if [ $? -ne 0 ]; then
    echo "Critical issues found. Please fix before committing."
    exit 1
fi
```

### CI/CD Pipeline
```yaml
# .github/workflows/debugging.yml
name: AI Debugging Analysis

on: [push, pull_request]

jobs:
  debugging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install deepsource
          pip install -r requirements-debugging.txt
      - name: Run DeepSource analysis
        run: python deepsource_analysis_runner.py
      - name: Run AI debugging workflow
        run: python debugging_workflow.py
```

## Troubleshooting

### Common Issues

1. **DeepSource CLI not found**
   ```bash
   pip install deepsource
   ```

2. **Analysis timeout**
   - Increase timeout in `.deepsource.toml`
   - Exclude large files or directories

3. **Memory issues during analysis**
   - Reduce analysis scope
   - Exclude test files and logs

4. **False positives**
   - Review and adjust rules in `.deepsource.toml`
   - Add specific exclusions for known false positives

### Getting Help

- Check the `ai_debugging_guide.md` for detailed explanations
- Review DeepSource documentation for rule configuration
- Use the debugging workflow for interactive analysis
- Monitor performance metrics for optimization opportunities

## Contributing

When contributing to the AI debugging integration:

1. Follow the existing code style and patterns
2. Add tests for new debugging features
3. Update documentation for new tools
4. Validate changes with the existing KPP simulator codebase
5. Ensure backward compatibility with existing workflows

## License

This AI debugging integration is part of the KPP Simulator project and follows the same licensing terms. 