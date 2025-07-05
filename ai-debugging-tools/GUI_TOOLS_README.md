# KPP Simulator GUI Tools

This document provides an overview of all the graphical user interface (GUI) tools available for debugging and analyzing the KPP Simulator.

## 🚀 Quick Start

### Launch All Tools
```bash
# Launch the main dashboard
python kpp_debugging_dashboard.py

# Or use the simple launcher
python launch_gui.py

# Launch specific tools from command line
python launch_gui.py dashboard
python launch_gui.py callback_analyzer
python launch_gui.py performance_monitor
```

## 📋 Available GUI Tools

### 1. 🚀 KPP Debugging Dashboard
**File:** `kpp_debugging_dashboard.py`

A comprehensive dashboard that provides access to all debugging and analysis tools in one place.

**Features:**
- Centralized access to all tools
- Tool status indicators
- System resource monitoring
- Quick launch buttons
- Settings management

**Usage:**
```bash
python kpp_debugging_dashboard.py
```

### 2. 🔍 Callback & Endpoint Analyzer
**File:** `gui_callback_analyzer.py`

A GUI tool for analyzing callbacks and endpoints in the KPP Simulator to identify integration issues.

**Features:**
- Visual analysis of 231+ callbacks and 40+ endpoints
- Dependency graph visualization
- Issue detection and categorization
- Export capabilities (JSON, text)
- Real-time filtering and search

**Screenshots:**
- Summary tab with statistics
- Callbacks tab with detailed analysis
- Issues tab with problem detection
- Recommendations tab with improvement suggestions

**Usage:**
```bash
python gui_callback_analyzer.py
```

### 3. 📊 Performance Monitor
**File:** `gui_performance_monitor.py`

Real-time performance monitoring with live charts and system metrics.

**Features:**
- Real-time CPU and memory monitoring
- Simulation performance tracking
- Live charts and graphs
- Alert system for performance issues
- Process monitoring
- Data export capabilities

**Charts:**
- System Resources (CPU & Memory)
- Step Duration over time
- Error Rate tracking
- Chain Speed & Electrical Power

**Usage:**
```bash
python gui_performance_monitor.py
```

### 4. ⚙️ Simulation Engine
**File:** `app.py`

The main KPP Simulator web interface with real-time simulation controls.

**Features:**
- Web-based simulation interface
- Real-time data visualization
- Parameter adjustment
- Simulation control (start/stop/pause)
- Data export and logging

**Usage:**
```bash
python app.py
# Then open http://localhost:5000 in your browser
```

### 5. 🧪 Test Suite Runner
**File:** `run_tests.py`

GUI for running the comprehensive test suite.

**Features:**
- Test selection interface
- Real-time test results
- Coverage reporting
- Test history
- Failed test analysis

**Usage:**
```bash
python run_tests.py
```

## 🌐 External Tools Integration

### DeepSource
**URL:** https://deepsource.io

Static code analysis and quality improvement platform.

**Features:**
- Automated code review
- Security vulnerability detection
- Performance issue identification
- Code quality improvements
- Automated fixes

**Integration:**
- Click "DeepSource" button in dashboard
- Opens web interface in browser
- Upload project for analysis

### Workik
**URL:** https://workik.ai

AI-powered interactive debugging assistance.

**Features:**
- Context-aware debugging
- Real-time code suggestions
- Interactive problem solving
- AI-powered code analysis
- Learning-based improvements

**Integration:**
- Click "Workik" button in dashboard
- Opens web interface in browser
- Connect your codebase for AI assistance

## 🛠️ Installation & Setup

### Prerequisites
```bash
# Required Python packages
pip install tkinter matplotlib numpy psutil

# For charts and graphs
pip install matplotlib

# For system monitoring
pip install psutil
```

### File Structure
```
kpp force calc/
├── gui_callback_analyzer.py      # Callback analysis GUI
├── gui_performance_monitor.py    # Performance monitoring GUI
├── kpp_debugging_dashboard.py    # Main dashboard
├── launch_gui.py                 # Simple launcher
├── app.py                        # Main simulation engine
├── analyze_callbacks_and_endpoints.py  # Analysis backend
└── GUI_TOOLS_README.md           # This file
```

## 📊 Tool Capabilities Comparison

| Tool | Analysis | Monitoring | Debugging | Export | Real-time |
|------|----------|------------|-----------|---------|-----------|
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ |
| Callback Analyzer | ✅ | ❌ | ✅ | ✅ | ❌ |
| Performance Monitor | ❌ | ✅ | ✅ | ✅ | ✅ |
| Simulation Engine | ❌ | ✅ | ✅ | ✅ | ✅ |
| Test Suite | ✅ | ❌ | ✅ | ✅ | ❌ |

## 🔧 Configuration

### Dashboard Settings
- Auto-refresh interval
- Theme selection (default/dark/light)
- Tool preferences
- System monitoring options

### Performance Monitor Settings
- Update interval (default: 1000ms)
- Alert thresholds
- Data retention period
- Chart display options

### Callback Analyzer Settings
- Analysis depth
- Export formats
- Filter preferences
- Issue severity levels

## 📈 Usage Examples

### 1. Debugging Callback Issues
```bash
# Launch callback analyzer
python gui_callback_analyzer.py

# Steps:
# 1. Select project directory
# 2. Run analysis
# 3. Review issues tab
# 4. Export recommendations
```

### 2. Performance Optimization
```bash
# Launch performance monitor
python gui_performance_monitor.py

# Steps:
# 1. Start monitoring
# 2. Run simulation
# 3. Monitor real-time charts
# 4. Check for alerts
# 5. Export performance data
```

### 3. Complete Debugging Workflow
```bash
# Launch dashboard
python kpp_debugging_dashboard.py

# Steps:
# 1. Use callback analyzer to find issues
# 2. Use performance monitor to identify bottlenecks
# 3. Use DeepSource for code quality improvements
# 4. Use Workik for AI-powered debugging
# 5. Run tests to validate fixes
```

## 🚨 Troubleshooting

### Common Issues

**1. GUI not launching**
```bash
# Check Python installation
python --version

# Install required packages
pip install tkinter matplotlib numpy psutil

# Check file permissions
chmod +x launch_gui.py
```

**2. Performance monitor not updating**
- Check if monitoring is started
- Verify update interval settings
- Check system permissions for psutil

**3. Callback analyzer not finding files**
- Verify project path is correct
- Check file permissions
- Ensure Python files are present

**4. Charts not displaying**
```bash
# Install matplotlib backend
pip install matplotlib
pip install tkinter
```

### Error Messages

**"Script not found"**
- Verify the script file exists
- Check file path and permissions
- Ensure Python environment is correct

**"Module not found"**
```bash
# Install missing dependencies
pip install -r requirements.txt
```

**"Permission denied"**
```bash
# Fix file permissions
chmod +x *.py
```

## 📝 Development

### Adding New GUI Tools

1. Create the GUI script following the existing pattern
2. Add tool configuration to `kpp_debugging_dashboard.py`
3. Update `launch_gui.py` with new tool
4. Add documentation to this README

### Tool Template
```python
import tkinter as tk
from tkinter import ttk

class NewToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("New Tool")
        self.create_widgets()
    
    def create_widgets(self):
        # Add your GUI components here
        pass

def main():
    root = tk.Tk()
    app = NewToolGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
```

## 🤝 Contributing

### Guidelines
- Follow existing code style
- Add proper error handling
- Include documentation
- Test on multiple platforms
- Update this README

### Testing
```bash
# Run all GUI tests
python -m pytest tests/test_gui.py

# Test individual tools
python gui_callback_analyzer.py --test
python gui_performance_monitor.py --test
```

## 📞 Support

### Getting Help
1. Check this README for common issues
2. Review error messages carefully
3. Check system requirements
4. Verify file permissions

### Reporting Issues
- Include error messages
- Specify operating system
- Provide Python version
- Describe steps to reproduce

### Feature Requests
- Use GitHub issues
- Provide detailed descriptions
- Include use cases
- Suggest implementation approach

## 📄 License

These GUI tools are part of the KPP Simulator project and follow the same licensing terms.

---

**Last Updated:** July 2025  
**Version:** 1.0  
**Compatibility:** Python 3.8+, Windows/Linux/macOS 