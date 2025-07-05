"""
KPP Simulator Debugging Dashboard

A comprehensive GUI dashboard that provides access to all debugging and analysis tools.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import sys
import os
import threading
import webbrowser
from pathlib import Path

class KPPDebuggingDashboard:
    """Main dashboard for KPP Simulator debugging tools."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("KPP Simulator - Debugging Dashboard")
        self.root.geometry("1000x700")
        
        # Tool configurations
        self.tools = {
            'callback_analyzer': {
                'name': 'Callback & Endpoint Analyzer',
                'description': 'Analyze callbacks and endpoints for integration issues',
                'script': 'gui_callback_analyzer.py',
                'icon': '🔍',
                'category': 'Analysis'
            },
            'performance_monitor': {
                'name': 'Performance Monitor',
                'description': 'Real-time performance monitoring and system metrics',
                'script': 'gui_performance_monitor.py',
                'icon': '📊',
                'category': 'Monitoring'
            },
            'deepsource': {
                'name': 'DeepSource Analysis',
                'description': 'Static code analysis and quality checks',
                'script': None,
                'icon': '🔧',
                'category': 'Analysis',
                'external': True
            },
            'workik': {
                'name': 'Workik Debugger',
                'description': 'Interactive AI-powered debugging assistance',
                'script': None,
                'icon': '🤖',
                'category': 'Debugging',
                'external': True
            },
            'simulation_engine': {
                'name': 'Simulation Engine',
                'description': 'Launch the main KPP simulation engine',
                'script': 'app.py',
                'icon': '⚙️',
                'category': 'Simulation'
            },
            'test_suite': {
                'name': 'Test Suite Runner',
                'description': 'Run comprehensive test suite',
                'script': 'run_tests.py',
                'icon': '🧪',
                'category': 'Testing'
            },
            'documentation': {
                'name': 'Documentation',
                'description': 'View project documentation and guides',
                'script': None,
                'icon': '📚',
                'category': 'Help',
                'external': True
            }
        }
        
        # Create GUI components
        self.create_widgets()
        
    def create_widgets(self):
        """Create and arrange GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Header
        self.create_header(main_frame)
        
        # Tool categories
        self.create_tool_categories(main_frame)
        
        # Status bar
        self.create_status_bar(main_frame)
    
    def create_header(self, parent):
        """Create the dashboard header."""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Title
        title_label = ttk.Label(header_frame, 
                               text="🚀 KPP Simulator Debugging Dashboard", 
                               font=("Arial", 20, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Version and status
        status_frame = ttk.Frame(header_frame)
        status_frame.pack(side=tk.RIGHT)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                font=("Arial", 10))
        status_label.pack(side=tk.RIGHT)
        
        # Quick actions
        actions_frame = ttk.Frame(header_frame)
        actions_frame.pack(side=tk.RIGHT, padx=(0, 20))
        
        ttk.Button(actions_frame, text="Refresh", 
                  command=self.refresh_dashboard).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(actions_frame, text="Settings", 
                  command=self.show_settings).pack(side=tk.LEFT)
    
    def create_tool_categories(self, parent):
        """Create tool categories with cards."""
        # Categories frame
        categories_frame = ttk.Frame(parent)
        categories_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid
        categories_frame.columnconfigure(0, weight=1)
        categories_frame.columnconfigure(1, weight=1)
        categories_frame.columnconfigure(2, weight=1)
        
        # Group tools by category
        categories = {}
        for tool_id, tool_info in self.tools.items():
            category = tool_info['category']
            if category not in categories:
                categories[category] = []
            categories[category].append((tool_id, tool_info))
        
        # Create category sections
        row = 0
        for category, tools in categories.items():
            # Category label
            category_label = ttk.Label(categories_frame, text=category.upper(), 
                                     font=("Arial", 12, "bold"))
            category_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(20, 10))
            row += 1
            
            # Tool cards
            col = 0
            for tool_id, tool_info in tools:
                card = self.create_tool_card(categories_frame, tool_id, tool_info)
                card.grid(row=row, column=col, padx=10, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
            
            if col > 0:
                row += 1
    
    def create_tool_card(self, parent, tool_id, tool_info):
        """Create a tool card widget."""
        card_frame = ttk.LabelFrame(parent, text="", padding="15")
        
        # Icon and title
        header_frame = ttk.Frame(card_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        icon_label = ttk.Label(header_frame, text=tool_info['icon'], font=("Arial", 20))
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        title_label = ttk.Label(header_frame, text=tool_info['name'], 
                               font=("Arial", 12, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Description
        desc_label = ttk.Label(card_frame, text=tool_info['description'], 
                              wraplength=250, justify=tk.LEFT)
        desc_label.pack(fill=tk.X, pady=(0, 15))
        
        # Buttons
        button_frame = ttk.Frame(card_frame)
        button_frame.pack(fill=tk.X)
        
        if tool_info.get('external'):
            # External tool
            launch_btn = ttk.Button(button_frame, text="Open", 
                                   command=lambda: self.launch_external_tool(tool_id))
            launch_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            info_btn = ttk.Button(button_frame, text="Info", 
                                 command=lambda: self.show_tool_info(tool_id))
            info_btn.pack(side=tk.LEFT)
        else:
            # Local tool
            launch_btn = ttk.Button(button_frame, text="Launch", 
                                   command=lambda: self.launch_local_tool(tool_id))
            launch_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            if tool_info['script'] and os.path.exists(tool_info['script']):
                status_icon = "✅"
            else:
                status_icon = "❌"
            
            status_label = ttk.Label(button_frame, text=status_icon, font=("Arial", 12))
            status_label.pack(side=tk.LEFT, padx=(0, 5))
            
            info_btn = ttk.Button(button_frame, text="Info", 
                                 command=lambda: self.show_tool_info(tool_id))
            info_btn.pack(side=tk.LEFT)
        
        return card_frame
    
    def create_status_bar(self, parent):
        """Create the status bar."""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))
        
        # Project info
        project_info = f"Project: KPP Simulator | Python {sys.version.split()[0]}"
        ttk.Label(status_frame, text=project_info).pack(side=tk.LEFT)
        
        # System info
        import psutil
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        system_info = f"CPU: {cpu_usage:.1f}% | Memory: {memory.percent:.1f}%"
        ttk.Label(status_frame, text=system_info).pack(side=tk.RIGHT)
    
    def launch_local_tool(self, tool_id):
        """Launch a local tool script."""
        tool_info = self.tools[tool_id]
        script = tool_info['script']
        
        if not script or not os.path.exists(script):
            messagebox.showerror("Error", f"Script not found: {script}")
            return
        
        try:
            self.status_var.set(f"Launching {tool_info['name']}...")
            
            # Launch in separate thread to avoid blocking
            def launch_thread():
                try:
                    subprocess.Popen([sys.executable, script])
                    self.root.after(0, lambda: self.status_var.set(f"{tool_info['name']} launched"))
                except Exception as e:
                    self.root.after(0, lambda: self.handle_launch_error(tool_info['name'], e))
            
            thread = threading.Thread(target=launch_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.handle_launch_error(tool_info['name'], e)
    
    def launch_external_tool(self, tool_id):
        """Launch an external tool."""
        tool_info = self.tools[tool_id]
        
        if tool_id == 'deepsource':
            # Open DeepSource web interface
            webbrowser.open('https://deepsource.io')
            self.status_var.set("DeepSource opened in browser")
            
        elif tool_id == 'workik':
            # Open Workik web interface
            webbrowser.open('https://workik.ai')
            self.status_var.set("Workik opened in browser")
            
        elif tool_id == 'documentation':
            # Open local documentation
            docs_path = Path("docs")
            if docs_path.exists():
                webbrowser.open(f"file://{docs_path.absolute()}")
                self.status_var.set("Documentation opened")
            else:
                messagebox.showinfo("Documentation", 
                                  "Documentation folder not found. Check the 'docs' directory.")
    
    def handle_launch_error(self, tool_name, error):
        """Handle tool launch errors."""
        messagebox.showerror("Launch Error", 
                           f"Failed to launch {tool_name}: {str(error)}")
        self.status_var.set("Launch failed")
    
    def show_tool_info(self, tool_id):
        """Show detailed information about a tool."""
        tool_info = self.tools[tool_id]
        
        info_text = f"Tool: {tool_info['name']}\n"
        info_text += f"Category: {tool_info['category']}\n"
        info_text += f"Description: {tool_info['description']}\n\n"
        
        if tool_info.get('external'):
            info_text += "This is an external tool that opens in your web browser.\n"
            if tool_id == 'deepsource':
                info_text += "\nDeepSource provides:\n"
                info_text += "• Static code analysis\n"
                info_text += "• Security vulnerability detection\n"
                info_text += "• Code quality improvements\n"
                info_text += "• Automated fixes\n"
            elif tool_id == 'workik':
                info_text += "\nWorkik provides:\n"
                info_text += "• AI-powered debugging\n"
                info_text += "• Interactive code analysis\n"
                info_text += "• Real-time suggestions\n"
                info_text += "• Context-aware assistance\n"
        else:
            if tool_info['script']:
                info_text += f"Script: {tool_info['script']}\n"
                if os.path.exists(tool_info['script']):
                    info_text += "Status: Available ✅\n"
                else:
                    info_text += "Status: Not found ❌\n"
        
        messagebox.showinfo(f"Tool Information - {tool_info['name']}", info_text)
    
    def refresh_dashboard(self):
        """Refresh the dashboard."""
        self.status_var.set("Refreshing...")
        
        # Recreate the tool categories
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.create_widgets()
        self.status_var.set("Dashboard refreshed")
    
    def show_settings(self):
        """Show dashboard settings."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Dashboard Settings")
        settings_window.geometry("400x300")
        
        # Settings content
        ttk.Label(settings_window, text="Dashboard Settings", 
                 font=("Arial", 14, "bold")).pack(pady=20)
        
        # Auto-refresh setting
        refresh_frame = ttk.Frame(settings_window)
        refresh_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(refresh_frame, text="Auto-refresh interval (seconds):").pack(side=tk.LEFT)
        refresh_var = tk.StringVar(value="30")
        refresh_entry = ttk.Entry(refresh_frame, textvariable=refresh_var, width=10)
        refresh_entry.pack(side=tk.RIGHT)
        
        # Theme setting
        theme_frame = ttk.Frame(settings_window)
        theme_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(theme_frame, text="Theme:").pack(side=tk.LEFT)
        theme_var = tk.StringVar(value="default")
        theme_combo = ttk.Combobox(theme_frame, textvariable=theme_var, 
                                  values=["default", "dark", "light"])
        theme_combo.pack(side=tk.RIGHT)
        
        # Buttons
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(side=tk.BOTTOM, pady=20)
        
        ttk.Button(button_frame, text="Save", 
                  command=lambda: self.save_settings(settings_window)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=settings_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def save_settings(self, settings_window):
        """Save dashboard settings."""
        # Here you would save the settings to a configuration file
        messagebox.showinfo("Settings", "Settings saved successfully!")
        settings_window.destroy()


def main():
    """Main function to run the dashboard."""
    root = tk.Tk()
    app = KPPDebuggingDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main() 