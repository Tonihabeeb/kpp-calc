"""
GUI for Callback and Endpoint Analysis Tool

A graphical interface for analyzing callbacks and endpoints in the KPP Simulator.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import threading
import os
from pathlib import Path
from analyze_callbacks_and_endpoints import CallbackEndpointAnalyzer

class CallbackAnalyzerGUI:
    """GUI application for callback and endpoint analysis."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("KPP Simulator - Callback & Endpoint Analyzer")
        self.root.geometry("1200x800")
        
        # Analysis results
        self.analysis_results = None
        self.analyzer = None
        
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
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="KPP Simulator Callback & Endpoint Analyzer", 
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
        status_bar.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def create_control_panel(self, parent):
        """Create the control panel with analysis options."""
        control_frame = ttk.LabelFrame(parent, text="Analysis Controls", padding="10")
        control_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Project path
        ttk.Label(control_frame, text="Project Path:").grid(row=0, column=0, sticky=tk.W)
        self.path_var = tk.StringVar(value=".")
        path_entry = ttk.Entry(control_frame, textvariable=self.path_var, width=50)
        path_entry.grid(row=0, column=1, padx=(5, 5))
        
        browse_btn = ttk.Button(control_frame, text="Browse", command=self.browse_project)
        browse_btn.grid(row=0, column=2)
        
        # Analysis options
        options_frame = ttk.Frame(control_frame)
        options_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        self.analyze_callbacks_var = tk.BooleanVar(value=True)
        self.analyze_endpoints_var = tk.BooleanVar(value=True)
        self.analyze_integration_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="Analyze Callbacks", 
                       variable=self.analyze_callbacks_var).grid(row=0, column=0, padx=(0, 20))
        ttk.Checkbutton(options_frame, text="Analyze Endpoints", 
                       variable=self.analyze_endpoints_var).grid(row=0, column=1, padx=(0, 20))
        ttk.Checkbutton(options_frame, text="Analyze Integration", 
                       variable=self.analyze_integration_var).grid(row=0, column=2)
        
        # Analysis button
        self.analyze_btn = ttk.Button(control_frame, text="Run Analysis", 
                                     command=self.run_analysis)
        self.analyze_btn.grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(control_frame, variable=self.progress_var, 
                                           maximum=100)
        self.progress_bar.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), 
                              pady=(10, 0))
    
    def create_notebook(self, parent):
        """Create notebook with different analysis views."""
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Summary tab
        self.create_summary_tab()
        
        # Callbacks tab
        self.create_callbacks_tab()
        
        # Endpoints tab
        self.create_endpoints_tab()
        
        # Issues tab
        self.create_issues_tab()
        
        # Recommendations tab
        self.create_recommendations_tab()
        
        # Raw data tab
        self.create_raw_data_tab()
    
    def create_summary_tab(self):
        """Create summary tab with overview statistics."""
        summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(summary_frame, text="Summary")
        
        # Summary text
        self.summary_text = scrolledtext.ScrolledText(summary_frame, height=20)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Export button
        export_btn = ttk.Button(summary_frame, text="Export Summary", 
                               command=self.export_summary)
        export_btn.pack(pady=(0, 10))
    
    def create_callbacks_tab(self):
        """Create callbacks tab with detailed callback information."""
        callbacks_frame = ttk.Frame(self.notebook)
        self.notebook.add(callbacks_frame, text="Callbacks")
        
        # Callback treeview
        columns = ("Name", "Type", "File", "Line", "Calls", "Called By")
        self.callback_tree = ttk.Treeview(callbacks_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.callback_tree.heading(col, text=col)
            self.callback_tree.column(col, width=100)
        
        # Scrollbars
        callback_scroll_y = ttk.Scrollbar(callbacks_frame, orient=tk.VERTICAL, 
                                        command=self.callback_tree.yview)
        callback_scroll_x = ttk.Scrollbar(callbacks_frame, orient=tk.HORIZONTAL, 
                                        command=self.callback_tree.xview)
        self.callback_tree.configure(yscrollcommand=callback_scroll_y.set, 
                                   xscrollcommand=callback_scroll_x.set)
        
        # Pack widgets
        self.callback_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        callback_scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        callback_scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        callbacks_frame.columnconfigure(0, weight=1)
        callbacks_frame.rowconfigure(0, weight=1)
        
        # Filter frame
        filter_frame = ttk.Frame(callbacks_frame)
        filter_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(filter_frame, text="Filter by type:").pack(side=tk.LEFT)
        self.callback_filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.callback_filter_var, 
                                   values=["All", "route", "callback", "method", "simulation_step"])
        filter_combo.pack(side=tk.LEFT, padx=(5, 0))
        filter_combo.bind("<<ComboboxSelected>>", self.filter_callbacks)
    
    def create_endpoints_tab(self):
        """Create endpoints tab with detailed endpoint information."""
        endpoints_frame = ttk.Frame(self.notebook)
        self.notebook.add(endpoints_frame, text="Endpoints")
        
        # Endpoint treeview
        columns = ("Route", "Methods", "File", "Line", "Error Handling", "Dependencies")
        self.endpoint_tree = ttk.Treeview(endpoints_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.endpoint_tree.heading(col, text=col)
            self.endpoint_tree.column(col, width=100)
        
        # Scrollbars
        endpoint_scroll_y = ttk.Scrollbar(endpoints_frame, orient=tk.VERTICAL, 
                                        command=self.endpoint_tree.yview)
        endpoint_scroll_x = ttk.Scrollbar(endpoints_frame, orient=tk.HORIZONTAL, 
                                        command=self.endpoint_tree.xview)
        self.endpoint_tree.configure(yscrollcommand=endpoint_scroll_y.set, 
                                   xscrollcommand=endpoint_scroll_x.set)
        
        # Pack widgets
        self.endpoint_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        endpoint_scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        endpoint_scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        endpoints_frame.columnconfigure(0, weight=1)
        endpoints_frame.rowconfigure(0, weight=1)
    
    def create_issues_tab(self):
        """Create issues tab with detected problems."""
        issues_frame = ttk.Frame(self.notebook)
        self.notebook.add(issues_frame, text="Issues")
        
        # Issues treeview
        columns = ("Type", "Severity", "File", "Line", "Message")
        self.issue_tree = ttk.Treeview(issues_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.issue_tree.heading(col, text=col)
            self.issue_tree.column(col, width=120)
        
        # Scrollbars
        issue_scroll_y = ttk.Scrollbar(issues_frame, orient=tk.VERTICAL, 
                                     command=self.issue_tree.yview)
        issue_scroll_x = ttk.Scrollbar(issues_frame, orient=tk.HORIZONTAL, 
                                     command=self.issue_tree.xview)
        self.issue_tree.configure(yscrollcommand=issue_scroll_y.set, 
                                xscrollcommand=issue_scroll_x.set)
        
        # Pack widgets
        self.issue_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        issue_scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        issue_scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        issues_frame.columnconfigure(0, weight=1)
        issues_frame.rowconfigure(0, weight=1)
        
        # Issue details frame
        details_frame = ttk.LabelFrame(issues_frame, text="Issue Details")
        details_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.issue_details_text = scrolledtext.ScrolledText(details_frame, height=8)
        self.issue_details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Bind selection event
        self.issue_tree.bind("<<TreeviewSelect>>", self.show_issue_details)
    
    def create_recommendations_tab(self):
        """Create recommendations tab with improvement suggestions."""
        recommendations_frame = ttk.Frame(self.notebook)
        self.notebook.add(recommendations_frame, text="Recommendations")
        
        # Recommendations text
        self.recommendations_text = scrolledtext.ScrolledText(recommendations_frame, height=20)
        self.recommendations_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Export button
        export_btn = ttk.Button(recommendations_frame, text="Export Recommendations", 
                               command=self.export_recommendations)
        export_btn.pack(pady=(0, 10))
    
    def create_raw_data_tab(self):
        """Create raw data tab with JSON export."""
        raw_frame = ttk.Frame(self.notebook)
        self.notebook.add(raw_frame, text="Raw Data")
        
        # Raw data text
        self.raw_data_text = scrolledtext.ScrolledText(raw_frame, height=20)
        self.raw_data_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Export button
        export_btn = ttk.Button(raw_frame, text="Export JSON", command=self.export_json)
        export_btn.pack(pady=(0, 10))
    
    def browse_project(self):
        """Browse for project directory."""
        directory = filedialog.askdirectory(title="Select Project Directory")
        if directory:
            self.path_var.set(directory)
    
    def run_analysis(self):
        """Run the callback and endpoint analysis."""
        project_path = self.path_var.get()
        
        if not os.path.exists(project_path):
            messagebox.showerror("Error", f"Project path does not exist: {project_path}")
            return
        
        # Disable analyze button and show progress
        self.analyze_btn.config(state="disabled")
        self.status_var.set("Running analysis...")
        self.progress_var.set(0)
        
        # Run analysis in separate thread
        def analysis_thread():
            try:
                self.analyzer = CallbackEndpointAnalyzer(project_path)
                self.analysis_results = self.analyzer.analyze_project()
                
                # Update GUI in main thread
                self.root.after(0, self.analysis_complete)
                
            except Exception as e:
                self.root.after(0, lambda: self.analysis_error(str(e)))
        
        thread = threading.Thread(target=analysis_thread)
        thread.daemon = True
        thread.start()
    
    def analysis_complete(self):
        """Called when analysis is complete."""
        self.analyze_btn.config(state="normal")
        self.status_var.set("Analysis complete")
        self.progress_var.set(100)
        
        # Update all tabs
        self.update_summary_tab()
        self.update_callbacks_tab()
        self.update_endpoints_tab()
        self.update_issues_tab()
        self.update_recommendations_tab()
        self.update_raw_data_tab()
        
        messagebox.showinfo("Success", "Analysis completed successfully!")
    
    def analysis_error(self, error_message):
        """Called when analysis encounters an error."""
        self.analyze_btn.config(state="normal")
        self.status_var.set("Analysis failed")
        self.progress_var.set(0)
        messagebox.showerror("Analysis Error", f"Analysis failed: {error_message}")
    
    def update_summary_tab(self):
        """Update summary tab with analysis results."""
        if not self.analysis_results:
            return
        
        summary = self.analysis_results.get('summary', {})
        
        summary_text = f"""
CALLBACK AND ENDPOINT ANALYSIS SUMMARY
=====================================

Total Callbacks: {summary.get('total_callbacks', 0)}
Total Endpoints: {summary.get('total_endpoints', 0)}
Total Issues: {summary.get('total_issues', 0)}

Callback Types:
"""
        
        for cb_type, count in summary.get('callback_types', {}).items():
            summary_text += f"  {cb_type}: {count}\n"
        
        summary_text += f"\nEndpoint Methods:\n"
        for method, count in summary.get('endpoint_methods', {}).items():
            summary_text += f"  {method}: {count}\n"
        
        summary_text += f"\nIssue Severities:\n"
        for severity, count in summary.get('issue_severities', {}).items():
            summary_text += f"  {severity}: {count}\n"
        
        summary_text += f"\nMost Complex Callbacks:\n"
        for cb in summary.get('most_complex_callbacks', [])[:5]:
            summary_text += f"  {cb['name']} ({cb['calls']} calls) - {cb['type']}\n"
        
        summary_text += f"\nMost Dependent Callbacks:\n"
        for cb in summary.get('most_dependent_callbacks', [])[:5]:
            summary_text += f"  {cb['name']} ({cb['called_by']} callers) - {cb['type']}\n"
        
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, summary_text)
    
    def update_callbacks_tab(self):
        """Update callbacks tab with analysis results."""
        if not self.analysis_results:
            return
        
        # Clear existing items
        for item in self.callback_tree.get_children():
            self.callback_tree.delete(item)
        
        # Add callback data
        for callback in self.analysis_results.get('callbacks', []):
            self.callback_tree.insert('', 'end', values=(
                callback.get('name', ''),
                callback.get('function_type', ''),
                callback.get('file_path', ''),
                callback.get('line_number', ''),
                len(callback.get('calls', [])),
                len(callback.get('called_by', []))
            ))
    
    def update_endpoints_tab(self):
        """Update endpoints tab with analysis results."""
        if not self.analysis_results:
            return
        
        # Clear existing items
        for item in self.endpoint_tree.get_children():
            self.endpoint_tree.delete(item)
        
        # Add endpoint data
        for endpoint in self.analysis_results.get('endpoints', []):
            self.endpoint_tree.insert('', 'end', values=(
                endpoint.get('route', ''),
                ', '.join(endpoint.get('methods', [])),
                endpoint.get('file_path', ''),
                endpoint.get('line_number', ''),
                'Yes' if endpoint.get('error_handling') else 'No',
                len(endpoint.get('dependencies', []))
            ))
    
    def update_issues_tab(self):
        """Update issues tab with analysis results."""
        if not self.analysis_results:
            return
        
        # Clear existing items
        for item in self.issue_tree.get_children():
            self.issue_tree.delete(item)
        
        # Add issue data
        for issue in self.analysis_results.get('issues', []):
            self.issue_tree.insert('', 'end', values=(
                issue.get('issue_type', ''),
                issue.get('severity', ''),
                issue.get('file_path', ''),
                issue.get('line_number', ''),
                issue.get('message', '')[:50] + '...' if len(issue.get('message', '')) > 50 else issue.get('message', '')
            ))
    
    def update_recommendations_tab(self):
        """Update recommendations tab with analysis results."""
        if not self.analysis_results:
            return
        
        recommendations_text = "RECOMMENDATIONS\n"
        recommendations_text += "===============\n\n"
        
        for i, rec in enumerate(self.analysis_results.get('recommendations', []), 1):
            recommendations_text += f"{i}. {rec.get('title', '')} ({rec.get('priority', '')} priority)\n"
            recommendations_text += f"   {rec.get('description', '')}\n\n"
            recommendations_text += "   Actions:\n"
            for action in rec.get('actions', []):
                recommendations_text += f"   - {action}\n"
            recommendations_text += "\n"
        
        self.recommendations_text.delete(1.0, tk.END)
        self.recommendations_text.insert(1.0, recommendations_text)
    
    def update_raw_data_tab(self):
        """Update raw data tab with JSON export."""
        if not self.analysis_results:
            return
        
        json_text = json.dumps(self.analysis_results, indent=2)
        self.raw_data_text.delete(1.0, tk.END)
        self.raw_data_text.insert(1.0, json_text)
    
    def filter_callbacks(self, event=None):
        """Filter callbacks by type."""
        filter_type = self.callback_filter_var.get()
        
        # Clear existing items
        for item in self.callback_tree.get_children():
            self.callback_tree.delete(item)
        
        if not self.analysis_results:
            return
        
        # Add filtered callback data
        for callback in self.analysis_results.get('callbacks', []):
            if filter_type == "All" or callback.get('function_type') == filter_type:
                self.callback_tree.insert('', 'end', values=(
                    callback.get('name', ''),
                    callback.get('function_type', ''),
                    callback.get('file_path', ''),
                    callback.get('line_number', ''),
                    len(callback.get('calls', [])),
                    len(callback.get('called_by', []))
                ))
    
    def show_issue_details(self, event=None):
        """Show details for selected issue."""
        selection = self.issue_tree.selection()
        if not selection:
            return
        
        # Get selected issue
        item = self.issue_tree.item(selection[0])
        issue_index = self.issue_tree.index(selection[0])
        
        if not self.analysis_results or issue_index >= len(self.analysis_results.get('issues', [])):
            return
        
        issue = self.analysis_results['issues'][issue_index]
        
        details_text = f"Issue Details\n"
        details_text += f"=============\n\n"
        details_text += f"Type: {issue.get('issue_type', '')}\n"
        details_text += f"Severity: {issue.get('severity', '')}\n"
        details_text += f"File: {issue.get('file_path', '')}\n"
        details_text += f"Line: {issue.get('line_number', '')}\n\n"
        details_text += f"Message: {issue.get('message', '')}\n\n"
        details_text += f"Recommendation: {issue.get('recommendation', '')}\n\n"
        details_text += f"Affected Components:\n"
        for component in issue.get('affected_components', []):
            details_text += f"  - {component}\n"
        
        self.issue_details_text.delete(1.0, tk.END)
        self.issue_details_text.insert(1.0, details_text)
    
    def export_summary(self):
        """Export summary to text file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w') as f:
                f.write(self.summary_text.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Summary exported to {filename}")
    
    def export_recommendations(self):
        """Export recommendations to text file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w') as f:
                f.write(self.recommendations_text.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Recommendations exported to {filename}")
    
    def export_json(self):
        """Export raw data to JSON file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename and self.analysis_results:
            with open(filename, 'w') as f:
                json.dump(self.analysis_results, f, indent=2)
            messagebox.showinfo("Success", f"JSON data exported to {filename}")


def main():
    """Main function to run the GUI application."""
    root = tk.Tk()
    app = CallbackAnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main() 