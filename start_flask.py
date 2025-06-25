#!/usr/bin/env python3
"""
Simple launcher for the Flask app to test pneumatic UI integration.
"""

import subprocess
import sys
import time
import os

def start_flask_app():
    """Start the Flask application"""
    print("Starting Flask application...")
    
    # Change to the correct directory
    os.chdir(r"h:\My Drive\kpp force calc")
    
    # Start the Flask app
    try:
        process = subprocess.Popen([sys.executable, "app.py"], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        print(f"Flask app started with PID: {process.pid}")
        print("Waiting for app to initialize...")
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✓ Flask app is running successfully!")
            print("✓ Open http://localhost:5000 in your browser to test the UI")
            print("✓ The pneumatic system UI should be visible in the 'Phase 7 Pneumatic System Analysis' section")
            print("\nPress Ctrl+C to stop the server")
            
            try:
                # Keep the process alive
                process.wait()
            except KeyboardInterrupt:
                print("\nStopping Flask app...")
                process.terminate()
                process.wait()
                print("Flask app stopped.")
        else:
            stdout, stderr = process.communicate()
            print(f"✗ Flask app failed to start:")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            
    except Exception as e:
        print(f"✗ Error starting Flask app: {e}")

if __name__ == "__main__":
    start_flask_app()
