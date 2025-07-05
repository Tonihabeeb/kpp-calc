"""
GUI Performance Monitor for KPP Simulator

A graphical interface for monitoring simulation performance in real-time.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import psutil
import json
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

class PerformanceMonitorGUI:
    """GUI application for performance monitoring."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("KPP Simulator - Performance Monitor")
        self.root.geometry("1400x900")
        
        # Performance data
        self.performance_data = {
            'timestamps': [],
            'cpu_usage': [],
            'memory_usage': [],
            'step_duration': [],
            'error_rate': [],
            'chain_speed': [],
            'electrical_power': []
        }
        
        # Monitoring state
        self.monitoring = False
        self.monitor_thread = None
        
        # Create GUI components
        self.create_widgets()
        
    def create_widgets(self):
        """Create and arrange GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="KPP Simulator Performance Monitor", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Control panel
        self.create_control_panel(main_frame)
        
        # Notebook for different views
        self.create_notebook(main_frame)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def create_control_panel(self, parent):
        """Create the control panel with monitoring options."""
        control_frame = ttk.LabelFrame(parent, text="Monitoring Controls", padding="10")
        control_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Start/Stop button
        self.monitor_btn = ttk.Button(control_frame, text="Start Monitoring", 
                                     command=self.toggle_monitoring)
        self.monitor_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Clear data button
        clear_btn = ttk.Button(control_frame, text="Clear Data", 
                              command=self.clear_data)
        clear_btn.grid(row=0, column=1, padx=(0, 10))
        
        # Export button
        export_btn = ttk.Button(control_frame, text="Export Data", 
                               command=self.export_data)
        export_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Update interval
        ttk.Label(control_frame, text="Update Interval (ms):").grid(row=0, column=3, padx=(20, 5))
        self.interval_var = tk.StringVar(value="1000")
        interval_entry = ttk.Entry(control_frame, textvariable=self.interval_var, width=10)
        interval_entry.grid(row=0, column=4, padx=(0, 10))
        
        # Current metrics
        metrics_frame = ttk.Frame(control_frame)
        metrics_frame.grid(row=1, column=0, columnspan=5, pady=(10, 0))
        
        # CPU usage
        self.cpu_var = tk.StringVar(value="CPU: 0%")
        ttk.Label(metrics_frame, textvariable=self.cpu_var, 
                 font=("Arial", 10, "bold")).grid(row=0, column=0, padx=(0, 20))
        
        # Memory usage
        self.memory_var = tk.StringVar(value="Memory: 0 MB")
        ttk.Label(metrics_frame, textvariable=self.memory_var, 
                 font=("Arial", 10, "bold")).grid(row=0, column=1, padx=(0, 20))
        
        # Step duration
        self.step_var = tk.StringVar(value="Step: 0 ms")
        ttk.Label(metrics_frame, textvariable=self.step_var, 
                 font=("Arial", 10, "bold")).grid(row=0, column=2, padx=(0, 20))
        
        # Error rate
        self.error_var = tk.StringVar(value="Errors: 0%")
        ttk.Label(metrics_frame, textvariable=self.error_var, 
                 font=("Arial", 10, "bold")).grid(row=0, column=3, padx=(0, 20))
        
        # Chain speed
        self.chain_var = tk.StringVar(value="Chain: 0 m/s")
        ttk.Label(metrics_frame, textvariable=self.chain_var, 
                 font=("Arial", 10, "bold")).grid(row=0, column=4, padx=(0, 20))
        
        # Electrical power
        self.power_var = tk.StringVar(value="Power: 0 kW")
        ttk.Label(metrics_frame, textvariable=self.power_var, 
                 font=("Arial", 10, "bold")).grid(row=0, column=5)
    
    def create_notebook(self, parent):
        """Create notebook with different monitoring views."""
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Real-time charts tab
        self.create_charts_tab()
        
        # System metrics tab
        self.create_system_tab()
        
        # Simulation metrics tab
        self.create_simulation_tab()
        
        # Alerts tab
        self.create_alerts_tab()
        
        # Logs tab
        self.create_logs_tab()
    
    def create_charts_tab(self):
        """Create real-time charts tab."""
        charts_frame = ttk.Frame(self.notebook)
        self.notebook.add(charts_frame, text="Real-time Charts")
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvasTkAgg(self.figure, charts_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create subplots
        self.ax1 = self.figure.add_subplot(2, 2, 1)  # CPU & Memory
        self.ax2 = self.figure.add_subplot(2, 2, 2)  # Step Duration
        self.ax3 = self.figure.add_subplot(2, 2, 3)  # Error Rate
        self.ax4 = self.figure.add_subplot(2, 2, 4)  # Chain Speed & Power
        
        self.figure.tight_layout()
    
    def create_system_tab(self):
        """Create system metrics tab."""
        system_frame = ttk.Frame(self.notebook)
        self.notebook.add(system_frame, text="System Metrics")
        
        # System info
        info_frame = ttk.LabelFrame(system_frame, text="System Information", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # CPU info
        cpu_info = f"CPU Cores: {psutil.cpu_count()}\n"
        cpu_info += f"CPU Frequency: {psutil.cpu_freq().current:.1f} MHz\n"
        cpu_info += f"CPU Usage: {psutil.cpu_percent()}%"
        
        ttk.Label(info_frame, text=cpu_info, justify=tk.LEFT).pack(anchor=tk.W)
        
        # Memory info
        memory = psutil.virtual_memory()
        memory_info = f"\nTotal Memory: {memory.total / (1024**3):.1f} GB\n"
        memory_info += f"Available Memory: {memory.available / (1024**3):.1f} GB\n"
        memory_info += f"Memory Usage: {memory.percent}%"
        
        ttk.Label(info_frame, text=memory_info, justify=tk.LEFT).pack(anchor=tk.W)
        
        # Disk info
        disk = psutil.disk_usage('/')
        disk_info = f"\nTotal Disk: {disk.total / (1024**3):.1f} GB\n"
        disk_info += f"Free Disk: {disk.free / (1024**3):.1f} GB\n"
        disk_info += f"Disk Usage: {disk.percent}%"
        
        ttk.Label(info_frame, text=disk_info, justify=tk.LEFT).pack(anchor=tk.W)
        
        # Process info
        process_frame = ttk.LabelFrame(system_frame, text="Process Information", padding="10")
        process_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Process treeview
        columns = ("PID", "Name", "CPU %", "Memory %", "Status")
        self.process_tree = ttk.Treeview(process_frame, columns=columns, show="headings")
        
        for col in columns:
            self.process_tree.heading(col, text=col)
            self.process_tree.column(col, width=100)
        
        process_scroll = ttk.Scrollbar(process_frame, orient=tk.VERTICAL, 
                                     command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=process_scroll.set)
        
        self.process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        process_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Refresh button
        refresh_btn = ttk.Button(process_frame, text="Refresh Processes", 
                               command=self.refresh_processes)
        refresh_btn.pack(pady=(10, 0))
    
    def create_simulation_tab(self):
        """Create simulation metrics tab."""
        sim_frame = ttk.Frame(self.notebook)
        self.notebook.add(sim_frame, text="Simulation Metrics")
        
        # Metrics display
        metrics_frame = ttk.LabelFrame(sim_frame, text="Current Simulation State", padding="10")
        metrics_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Create metric labels
        self.sim_metrics = {}
        metric_names = [
            "Chain Speed", "Electrical Power", "Mechanical Torque", 
            "Chain Tension", "Floater Count", "System Pressure",
            "Step Count", "Total Runtime", "Average Step Time"
        ]
        
        for i, name in enumerate(metric_names):
            row = i // 3
            col = i % 3
            
            frame = ttk.Frame(metrics_frame)
            frame.grid(row=row, column=col, padx=10, pady=5, sticky=(tk.W, tk.E))
            
            ttk.Label(frame, text=f"{name}:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
            var = tk.StringVar(value="0")
            self.sim_metrics[name] = var
            ttk.Label(frame, textvariable=var, font=("Arial", 10)).pack(anchor=tk.W)
        
        # Historical data
        history_frame = ttk.LabelFrame(sim_frame, text="Historical Data", padding="10")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # History treeview
        columns = ("Timestamp", "Chain Speed", "Power", "CPU %", "Memory %", "Step Time")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings")
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=120)
        
        history_scroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, 
                                     command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scroll.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_alerts_tab(self):
        """Create alerts tab."""
        alerts_frame = ttk.Frame(self.notebook)
        self.notebook.add(alerts_frame, text="Alerts")
        
        # Alerts treeview
        columns = ("Time", "Severity", "Type", "Message")
        self.alerts_tree = ttk.Treeview(alerts_frame, columns=columns, show="headings")
        
        for col in columns:
            self.alerts_tree.heading(col, text=col)
            self.alerts_tree.column(col, width=150)
        
        alerts_scroll = ttk.Scrollbar(alerts_frame, orient=tk.VERTICAL, 
                                    command=self.alerts_tree.yview)
        self.alerts_tree.configure(yscrollcommand=alerts_scroll.set)
        
        self.alerts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        alerts_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Alert details
        details_frame = ttk.LabelFrame(alerts_frame, text="Alert Details", padding="10")
        details_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.alert_details_text = scrolledtext.ScrolledText(details_frame, height=6)
        self.alert_details_text.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection event
        self.alerts_tree.bind("<<TreeviewSelect>>", self.show_alert_details)
    
    def create_logs_tab(self):
        """Create logs tab."""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs")
        
        # Logs text
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=20)
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Log controls
        controls_frame = ttk.Frame(logs_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(controls_frame, text="Clear Logs", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(controls_frame, text="Export Logs", 
                  command=self.export_logs).pack(side=tk.LEFT)
    
    def toggle_monitoring(self):
        """Toggle monitoring on/off."""
        if not self.monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.monitoring = True
        self.monitor_btn.config(text="Stop Monitoring")
        self.status_var.set("Monitoring active")
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.log_message("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False
        self.monitor_btn.config(text="Start Monitoring")
        self.status_var.set("Monitoring stopped")
        
        self.log_message("Performance monitoring stopped")
    
    def monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                memory_mb = memory.used / (1024 * 1024)
                
                # Simulate simulation metrics (replace with actual simulation data)
                step_duration = np.random.normal(50, 10)  # ms
                error_rate = np.random.uniform(0, 5)  # %
                chain_speed = np.random.uniform(10, 60)  # m/s
                electrical_power = np.random.uniform(20, 40)  # kW
                
                # Update data
                timestamp = time.time()
                self.performance_data['timestamps'].append(timestamp)
                self.performance_data['cpu_usage'].append(cpu_percent)
                self.performance_data['memory_usage'].append(memory_mb)
                self.performance_data['step_duration'].append(step_duration)
                self.performance_data['error_rate'].append(error_rate)
                self.performance_data['chain_speed'].append(chain_speed)
                self.performance_data['electrical_power'].append(electrical_power)
                
                # Keep only last 100 data points
                max_points = 100
                for key in self.performance_data:
                    if len(self.performance_data[key]) > max_points:
                        self.performance_data[key] = self.performance_data[key][-max_points:]
                
                # Update GUI in main thread
                self.root.after(0, self.update_display, {
                    'cpu': cpu_percent,
                    'memory': memory_mb,
                    'step': step_duration,
                    'error': error_rate,
                    'chain': chain_speed,
                    'power': electrical_power
                })
                
                # Check for alerts
                self.check_alerts(cpu_percent, memory_mb, step_duration, error_rate)
                
                # Sleep for update interval
                interval = int(self.interval_var.get())
                time.sleep(interval / 1000.0)
                
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Monitoring error: {e}"))
                time.sleep(1)
    
    def update_display(self, metrics):
        """Update display with current metrics."""
        # Update control panel metrics
        self.cpu_var.set(f"CPU: {metrics['cpu']:.1f}%")
        self.memory_var.set(f"Memory: {metrics['memory']:.0f} MB")
        self.step_var.set(f"Step: {metrics['step']:.1f} ms")
        self.error_var.set(f"Errors: {metrics['error']:.1f}%")
        self.chain_var.set(f"Chain: {metrics['chain']:.1f} m/s")
        self.power_var.set(f"Power: {metrics['power']:.1f} kW")
        
        # Update simulation metrics
        self.sim_metrics["Chain Speed"].set(f"{metrics['chain']:.1f} m/s")
        self.sim_metrics["Electrical Power"].set(f"{metrics['power']:.1f} kW")
        self.sim_metrics["Step Count"].set(str(len(self.performance_data['timestamps'])))
        self.sim_metrics["Average Step Time"].set(f"{metrics['step']:.1f} ms")
        
        # Update charts
        self.update_charts()
        
        # Update history
        self.update_history(metrics)
    
    def update_charts(self):
        """Update real-time charts."""
        if not self.performance_data['timestamps']:
            return
        
        # Clear previous plots
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        
        # Convert timestamps to relative time
        timestamps = np.array(self.performance_data['timestamps'])
        relative_time = timestamps - timestamps[0]
        
        # CPU & Memory plot
        self.ax1.plot(relative_time, self.performance_data['cpu_usage'], 'b-', label='CPU %')
        self.ax1.plot(relative_time, [m/100 for m in self.performance_data['memory_usage']], 'r-', label='Memory %')
        self.ax1.set_title('System Resources')
        self.ax1.set_ylabel('Usage %')
        self.ax1.legend()
        self.ax1.grid(True)
        
        # Step Duration plot
        self.ax2.plot(relative_time, self.performance_data['step_duration'], 'g-')
        self.ax2.set_title('Step Duration')
        self.ax2.set_ylabel('Time (ms)')
        self.ax2.grid(True)
        
        # Error Rate plot
        self.ax3.plot(relative_time, self.performance_data['error_rate'], 'r-')
        self.ax3.set_title('Error Rate')
        self.ax3.set_ylabel('Error %')
        self.ax3.grid(True)
        
        # Chain Speed & Power plot
        ax4_twin = self.ax4.twinx()
        self.ax4.plot(relative_time, self.performance_data['chain_speed'], 'b-', label='Chain Speed')
        ax4_twin.plot(relative_time, self.performance_data['electrical_power'], 'r-', label='Electrical Power')
        self.ax4.set_title('Simulation Performance')
        self.ax4.set_ylabel('Chain Speed (m/s)')
        ax4_twin.set_ylabel('Power (kW)')
        self.ax4.grid(True)
        
        # Update canvas
        self.figure.tight_layout()
        self.canvas.draw()
    
    def update_history(self, metrics):
        """Update history treeview."""
        # Add new entry
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.history_tree.insert('', 0, values=(
            timestamp,
            f"{metrics['chain']:.1f}",
            f"{metrics['power']:.1f}",
            f"{metrics['cpu']:.1f}",
            f"{metrics['memory']:.0f}",
            f"{metrics['step']:.1f}"
        ))
        
        # Keep only last 50 entries
        if len(self.history_tree.get_children()) > 50:
            self.history_tree.delete(self.history_tree.get_children()[-1])
    
    def check_alerts(self, cpu, memory, step, error):
        """Check for performance alerts."""
        alerts = []
        
        if cpu > 80:
            alerts.append(("High", "CPU", f"CPU usage is high: {cpu:.1f}%"))
        
        if memory > 1000:  # 1GB
            alerts.append(("High", "Memory", f"Memory usage is high: {memory:.0f} MB"))
        
        if step > 100:
            alerts.append(("Medium", "Performance", f"Step duration is slow: {step:.1f} ms"))
        
        if error > 10:
            alerts.append(("High", "Error", f"Error rate is high: {error:.1f}%"))
        
        # Add alerts to treeview
        for severity, alert_type, message in alerts:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.alerts_tree.insert('', 0, values=(timestamp, severity, alert_type, message))
            self.log_message(f"ALERT: {message}")
    
    def show_alert_details(self, event=None):
        """Show details for selected alert."""
        selection = self.alerts_tree.selection()
        if not selection:
            return
        
        item = self.alerts_tree.item(selection[0])
        details = f"Alert Details\n"
        details += f"=============\n\n"
        details += f"Time: {item['values'][0]}\n"
        details += f"Severity: {item['values'][1]}\n"
        details += f"Type: {item['values'][2]}\n"
        details += f"Message: {item['values'][3]}\n\n"
        details += f"Recommendation: Monitor system resources and check for bottlenecks."
        
        self.alert_details_text.delete(1.0, tk.END)
        self.alert_details_text.insert(1.0, details)
    
    def refresh_processes(self):
        """Refresh process list."""
        # Clear existing items
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        
        # Add current processes
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                info = proc.info
                self.process_tree.insert('', 'end', values=(
                    info['pid'],
                    info['name'][:20],
                    f"{info['cpu_percent']:.1f}",
                    f"{info['memory_percent']:.1f}",
                    info['status']
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    
    def log_message(self, message):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.logs_text.insert(tk.END, log_entry)
        self.logs_text.see(tk.END)
    
    def clear_data(self):
        """Clear all performance data."""
        for key in self.performance_data:
            self.performance_data[key] = []
        
        # Clear displays
        self.update_charts()
        
        # Clear history
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        self.log_message("Performance data cleared")
    
    def clear_logs(self):
        """Clear log messages."""
        self.logs_text.delete(1.0, tk.END)
    
    def export_data(self):
        """Export performance data to JSON file."""
        try:
            filename = f"performance_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(self.performance_data, f, indent=2)
            messagebox.showinfo("Success", f"Data exported to {filename}")
            self.log_message(f"Performance data exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")
    
    def export_logs(self):
        """Export logs to text file."""
        try:
            filename = f"performance_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write(self.logs_text.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Logs exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export logs: {e}")


def main():
    """Main function to run the GUI application."""
    root = tk.Tk()
    app = PerformanceMonitorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main() 