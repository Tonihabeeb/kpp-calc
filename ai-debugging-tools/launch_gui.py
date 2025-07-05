#!/usr/bin/env python3
"""
KPP Simulator GUI Launcher

A simple launcher script to start any of the GUI debugging tools.
"""

import sys
import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

def main():
    """Main launcher function."""
    if len(sys.argv) > 1:
        # Command line mode
        tool = sys.argv[1].lower()
        
        if tool in ['--help', '-h', 'help']:
            show_help()
        else:
            launch_tool(tool)
    else:
        # GUI mode
        launch_gui_selector()

def show_help():
    """Show help information."""
    help_text = """
KPP Simulator GUI Launcher

Usage:
    python launch_gui.py [tool]

Available tools:
    dashboard          - Launch the main debugging dashboard
    callback_analyzer  - Launch callback and endpoint analyzer
    performance_monitor - Launch performance monitoring tool
    simulation        - Launch the main simulation engine
    tests             - Launch test suite runner
    docs              - Open documentation

Examples:
    python launch_gui.py dashboard
    python launch_gui.py callback_analyzer
    python launch_gui.py performance_monitor

External tools:
    deepsource        - Open DeepSource web interface
    workik            - Open Workik web interface

For more information, see GUI_TOOLS_README.md
"""
    print(help_text)

def launch_gui_selector():
    """Launch the GUI tool selector."""
    root = tk.Tk()
    root.title("KPP Simulator - GUI Tool Launcher")
    root.geometry("400x300")
    
    # Main frame
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_label = ttk.Label(main_frame, text="Select GUI Tool to Launch", 
                           font=("Arial", 14, "bold"))
    title_label.pack(pady=(0, 20))
    
    # Tool buttons
    tools = [
        ("🚀 Dashboard", "dashboard", "Complete debugging dashboard"),
        ("🔍 Callback Analyzer", "callback_analyzer", "Analyze callbacks and endpoints"),
        ("📊 Performance Monitor", "performance_monitor", "Real-time performance monitoring"),
        ("⚙️ Simulation Engine", "simulation", "Launch main simulation"),
        ("🧪 Test Suite", "tests", "Run test suite"),
        ("📚 Documentation", "docs", "View documentation")
    ]
    
    for text, tool_id, description in tools:
        frame = ttk.Frame(main_frame)
        frame.pack(fill=tk.X, pady=5)
        
        btn = ttk.Button(frame, text=text, 
                        command=lambda t=tool_id: launch_tool_and_close(t, root))
        btn.pack(side=tk.LEFT, padx=(0, 10))
        
        desc_label = ttk.Label(frame, text=description, font=("Arial", 9))
        desc_label.pack(side=tk.LEFT)
    
    # External tools
    external_frame = ttk.LabelFrame(main_frame, text="External Tools", padding="10")
    external_frame.pack(fill=tk.X, pady=(20, 0))
    
    ttk.Button(external_frame, text="🔧 DeepSource", 
               command=lambda: launch_external("deepsource")).pack(side=tk.LEFT, padx=(0, 10))
    ttk.Button(external_frame, text="🤖 Workik", 
               command=lambda: launch_external("workik")).pack(side=tk.LEFT)
    
    root.mainloop()

def launch_tool_and_close(tool_id, root):
    """Launch tool and close the selector."""
    root.destroy()
    launch_tool(tool_id)

def launch_tool(tool_id):
    """Launch a specific tool."""
    tool_scripts = {
        "dashboard": "kpp_debugging_dashboard.py",
        "callback_analyzer": "gui_callback_analyzer.py",
        "performance_monitor": "gui_performance_monitor.py",
        "simulation": "app.py",
        "tests": "run_tests.py"
    }
    
    if tool_id == "docs":
        launch_documentation()
        return
    
    script = tool_scripts.get(tool_id)
    if not script:
        print(f"Unknown tool: {tool_id}")
        return
    
    if not os.path.exists(script):
        print(f"Script not found: {script}")
        return
    
    try:
        print(f"Launching {tool_id}...")
        subprocess.Popen([sys.executable, script])
    except Exception as e:
        print(f"Failed to launch {tool_id}: {e}")

def launch_external(tool_id):
    """Launch external web-based tools."""
    import webbrowser
    
    urls = {
        "deepsource": "https://deepsource.io",
        "workik": "https://workik.ai"
    }
    
    url = urls.get(tool_id)
    if url:
        webbrowser.open(url)
        print(f"Opened {tool_id} in browser")
    else:
        print(f"Unknown external tool: {tool_id}")

def launch_documentation():
    """Launch local documentation."""
    import webbrowser
    from pathlib import Path
    
    docs_path = Path("docs")
    if docs_path.exists():
        webbrowser.open(f"file://{docs_path.absolute()}")
        print("Documentation opened in browser")
    else:
        print("Documentation folder not found")

if __name__ == "__main__":
    main() 