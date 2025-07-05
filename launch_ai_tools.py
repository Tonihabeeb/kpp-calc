#!/usr/bin/env python3
"""
KPP Simulator AI Tools Launcher

A launcher script to start AI debugging tools from the ai-debugging-tools folder.
"""

import sys
import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

# Add the ai-debugging-tools folder to the path
TOOLS_DIR = os.path.join(os.path.dirname(__file__), "ai-debugging-tools")
sys.path.insert(0, TOOLS_DIR)

def main():
    """Main launcher function."""
    if len(sys.argv) > 1:
        # Command line mode
        tool = sys.argv[1].lower()
        launch_tool(tool)
    else:
        # GUI mode
        launch_gui_selector()

def launch_gui_selector():
    """Launch the GUI tool selector."""
    root = tk.Tk()
    root.title("KPP Simulator - AI Tools Launcher")
    root.geometry("500x400")
    
    # Main frame
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_label = ttk.Label(main_frame, text="🤖 KPP Simulator AI Debugging Tools", 
                           font=("Arial", 16, "bold"))
    title_label.pack(pady=(0, 20))
    
    # Description
    desc_label = ttk.Label(main_frame, 
                          text="Select an AI-powered debugging tool to launch:", 
                          font=("Arial", 10))
    desc_label.pack(pady=(0, 20))
    
    # Tool buttons
    tools = [
        ("🚀 Dashboard", "dashboard", "Complete AI debugging dashboard"),
        ("🔍 Callback Analyzer", "callback_analyzer", "AI-powered callback analysis"),
        ("📊 Performance Monitor", "performance_monitor", "Real-time AI monitoring"),
        ("⚙️ Simulation Engine", "simulation", "Launch main simulation"),
        ("🧪 Test Suite", "tests", "Run AI-enhanced tests"),
        ("📚 Documentation", "docs", "View AI debugging guides")
    ]
    
    for text, tool_id, description in tools:
        frame = ttk.Frame(main_frame)
        frame.pack(fill=tk.X, pady=5)
        
        btn = ttk.Button(frame, text=text, 
                        command=lambda t=tool_id: launch_tool_and_close(t, root))
        btn.pack(side=tk.LEFT, padx=(0, 10))
        
        desc_label = ttk.Label(frame, text=description, font=("Arial", 9))
        desc_label.pack(side=tk.LEFT)
    
    # External AI tools
    external_frame = ttk.LabelFrame(main_frame, text="External AI Tools", padding="10")
    external_frame.pack(fill=tk.X, pady=(20, 0))
    
    ttk.Button(external_frame, text="🔧 DeepSource AI", 
               command=lambda: launch_external("deepsource")).pack(side=tk.LEFT, padx=(0, 10))
    ttk.Button(external_frame, text="🤖 Workik AI", 
               command=lambda: launch_external("workik")).pack(side=tk.LEFT)
    
    # Status
    status_frame = ttk.Frame(main_frame)
    status_frame.pack(fill=tk.X, pady=(20, 0))
    
    status_label = ttk.Label(status_frame, 
                            text=f"Tools location: {TOOLS_DIR}", 
                            font=("Arial", 8), foreground="gray")
    status_label.pack(side=tk.LEFT)
    
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
        "simulation": "../app.py",  # Go up one level to find app.py
        "tests": "../run_tests.py"  # Go up one level to find run_tests.py
    }
    
    if tool_id == "docs":
        launch_documentation()
        return
    
    script = tool_scripts.get(tool_id)
    if not script:
        print(f"Unknown tool: {tool_id}")
        return
    
    # Construct full path
    if script.startswith("../"):
        # Script is in parent directory
        script_path = os.path.join(os.path.dirname(TOOLS_DIR), script[3:])
    else:
        # Script is in tools directory
        script_path = os.path.join(TOOLS_DIR, script)
    
    if not os.path.exists(script_path):
        print(f"Script not found: {script_path}")
        return
    
    try:
        print(f"Launching {tool_id} from {script_path}...")
        # Change to the script's directory before running
        script_dir = os.path.dirname(script_path)
        subprocess.Popen([sys.executable, script_path], cwd=script_dir)
    except Exception as e:
        print(f"Failed to launch {tool_id}: {e}")

def launch_external(tool_id):
    """Launch external web-based AI tools."""
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
    
    # Check for docs in parent directory
    docs_path = Path(os.path.dirname(TOOLS_DIR)) / "docs"
    if docs_path.exists():
        webbrowser.open(f"file://{docs_path.absolute()}")
        print("Documentation opened in browser")
    else:
        # Check for docs in tools directory
        tools_docs_path = Path(TOOLS_DIR) / "docs"
        if tools_docs_path.exists():
            webbrowser.open(f"file://{tools_docs_path.absolute()}")
            print("Documentation opened in browser")
        else:
            messagebox.showinfo("Documentation", 
                              "Documentation folder not found. Check the 'docs' directory.")

def show_help():
    """Show help information."""
    help_text = """
KPP Simulator AI Tools Launcher

Usage:
    python launch_ai_tools.py [tool]

Available AI tools:
    dashboard          - Launch the main AI debugging dashboard
    callback_analyzer  - Launch AI-powered callback analyzer
    performance_monitor - Launch AI performance monitoring tool
    simulation        - Launch the main simulation engine
    tests             - Launch AI-enhanced test suite
    docs              - Open AI debugging documentation

Examples:
    python launch_ai_tools.py dashboard
    python launch_ai_tools.py callback_analyzer
    python launch_ai_tools.py performance_monitor

External AI tools:
    deepsource        - Open DeepSource AI web interface
    workik            - Open Workik AI web interface

Tools location: ai-debugging-tools/
For more information, see ai-debugging-tools/GUI_TOOLS_README.md
"""
    print(help_text)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
    else:
        main() 