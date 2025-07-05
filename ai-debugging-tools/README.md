# AI Debugging Tools for KPP Simulator

This folder contains all AI-powered debugging and analysis tools for the KPP Simulator.

## 📁 Folder Structure

```
ai-debugging-tools/
├── README.md                           # This file
├── ai_debugging_guide.md               # AI debugging integration guide
├── analyze_callbacks_and_endpoints.py  # Backend analysis engine
├── gui_callback_analyzer.py            # GUI for callback analysis
├── gui_performance_monitor.py          # GUI for performance monitoring
├── kpp_debugging_dashboard.py          # Main dashboard GUI
├── launch_gui.py                       # Simple launcher (internal)
├── GUI_TOOLS_README.md                 # Detailed GUI documentation
└── .deepsource.toml                    # DeepSource configuration
```

## 🚀 Quick Start

### From Root Directory
```bash
# Launch the main AI tools launcher
python launch_ai_tools.py

# Launch specific tools
python launch_ai_tools.py dashboard
python launch_ai_tools.py callback_analyzer
python launch_ai_tools.py performance_monitor
```

### From This Directory
```bash
# Launch individual tools directly
python gui_callback_analyzer.py
python gui_performance_monitor.py
python kpp_debugging_dashboard.py
```

## 🛠️ Available Tools

### 1. 🤖 AI Debugging Dashboard
**File:** `kpp_debugging_dashboard.py`

A comprehensive dashboard that provides centralized access to all AI debugging tools.

**Features:**
- Unified interface for all tools
- System resource monitoring
- Tool status indicators
- Quick launch buttons
- Settings management

### 2. 🔍 AI Callback Analyzer
**File:** `gui_callback_analyzer.py`

AI-powered analysis of callbacks and endpoints to identify integration issues.

**Features:**
- Visual analysis of 231+ callbacks and 40+ endpoints
- Dependency graph visualization
- AI-powered issue detection
- Export capabilities (JSON, text)
- Real-time filtering and search

### 3. 📊 AI Performance Monitor
**File:** `gui_performance_monitor.py`

Real-time performance monitoring with AI-enhanced analytics.

**Features:**
- Real-time CPU and memory monitoring
- AI-powered performance prediction
- Live charts and graphs
- Intelligent alert system
- Process monitoring
- Data export capabilities

### 4. 🔧 Backend Analysis Engine
**File:** `analyze_callbacks_and_endpoints.py`

The core analysis engine that powers the GUI tools.

**Features:**
- Static code analysis
- Dependency mapping
- Issue detection algorithms
- Performance analysis
- Integration testing

## 🌐 External AI Tools Integration

### DeepSource AI
- **Configuration:** `.deepsource.toml`
- **Web Interface:** https://deepsource.io
- **Features:** Static analysis, security scanning, automated fixes

### Workik AI
- **Web Interface:** https://workik.ai
- **Features:** AI-powered debugging, interactive assistance

## 📚 Documentation

### AI Debugging Guide
**File:** `ai_debugging_guide.md`

Comprehensive guide for implementing AI debugging strategies using DeepSource and Workik.

**Contents:**
- DeepSource static analysis setup
- Workik interactive debugging setup
- Code refactoring and improvements
- Implementation checklist
- Usage instructions

### GUI Tools Documentation
**File:** `GUI_TOOLS_README.md`

Detailed documentation for all GUI tools including:
- Installation and setup
- Usage examples
- Troubleshooting
- Development guidelines

## 🔧 Configuration

### DeepSource Configuration
**File:** `.deepsource.toml`

```toml
version = 1

[[analyzers]]
name = "python"
enabled = true

[[analyzers]]
name = "test-coverage"
enabled = true

[analyzers.python]
python_version = "3.8"

[[transformers]]
name = "pypi"
enabled = true
```

## 📊 Tool Capabilities

| Tool | Analysis | Monitoring | AI Features | Export | Real-time |
|------|----------|------------|-------------|---------|-----------|
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ |
| Callback Analyzer | ✅ | ❌ | ✅ | ✅ | ❌ |
| Performance Monitor | ❌ | ✅ | ✅ | ✅ | ✅ |
| Backend Engine | ✅ | ❌ | ✅ | ✅ | ❌ |

## 🚨 Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Make sure you're running from the correct directory
cd ai-debugging-tools
python gui_callback_analyzer.py
```

**2. Missing Dependencies**
```bash
# Install required packages
pip install tkinter matplotlib numpy psutil
```

**3. Path Issues**
```bash
# Use the launcher from root directory
python launch_ai_tools.py
```

### Error Messages

**"Module not found"**
- Check if you're in the correct directory
- Verify Python environment
- Install missing dependencies

**"Script not found"**
- Use the launcher from root directory
- Check file permissions
- Verify file paths

## 🔄 Updates and Maintenance

### Adding New Tools
1. Create the tool script in this directory
2. Update `launch_gui.py` with new tool
3. Add documentation to `GUI_TOOLS_README.md`
4. Update this README

### Updating Existing Tools
1. Modify the tool script
2. Test functionality
3. Update documentation
4. Version control changes

## 🤝 Contributing

### Guidelines
- Follow existing code style
- Add proper error handling
- Include documentation
- Test on multiple platforms
- Update relevant README files

### Development Workflow
1. Create feature branch
2. Implement changes
3. Test thoroughly
4. Update documentation
5. Submit pull request

## 📞 Support

### Getting Help
1. Check this README for common issues
2. Review `GUI_TOOLS_README.md` for detailed instructions
3. Check `ai_debugging_guide.md` for AI integration help
4. Verify system requirements

### Reporting Issues
- Include error messages
- Specify operating system
- Provide Python version
- Describe steps to reproduce

## 📄 License

These AI debugging tools are part of the KPP Simulator project and follow the same licensing terms.

---

**Last Updated:** July 2025  
**Version:** 1.0  
**Compatibility:** Python 3.8+, Windows/Linux/macOS  
**AI Tools:** DeepSource, Workik, Custom AI Analysis 