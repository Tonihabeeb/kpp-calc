#!/usr/bin/env python3
"""
Simple startup script for the KPP Simulator
"""

import subprocess
import time
import sys
import os
import webbrowser
import threading

def start_backend():
    """Start the Flask backend"""
    print("🚀 Starting Flask backend...")
    try:
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n⏹️  Backend stopped by user")
    except Exception as e:
        print(f"❌ Backend error: {e}")

def start_frontend():
    """Start the Dash frontend"""
    print("🎨 Starting Dash frontend...")
    try:
        subprocess.run([sys.executable, "dash_app.py"], check=True)
    except KeyboardInterrupt:
        print("\n⏹️  Frontend stopped by user")
    except Exception as e:
        print(f"❌ Frontend error: {e}")

def main():
    print("🎯 KPP Simulator Startup")
    print("=" * 40)
    
    # Check if required files exist
    required_files = ["app.py", "dash_app.py", "kpp_crash_fixed_parameters.json"]
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Required file not found: {file}")
            return
    
    print("✅ All required files found")
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Wait for backend to start
    print("⏳ Waiting for backend to start...")
    time.sleep(3)
    
    # Start frontend in a separate thread
    frontend_thread = threading.Thread(target=start_frontend, daemon=True)
    frontend_thread.start()
    
    # Wait for frontend to start
    print("⏳ Waiting for frontend to start...")
    time.sleep(5)
    
    # Open browser
    print("🌐 Opening browser...")
    try:
        webbrowser.open("http://localhost:9102")
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print("   Please open http://localhost:9102 manually")
    
    print("\n🎉 KPP Simulator is ready!")
    print("📊 Dashboard: http://localhost:9102")
    print("🔧 Backend API: http://localhost:9100")
    print("\n💡 You can now:")
    print("   - Press the Start button to begin simulation")
    print("   - Adjust parameters in the control panels")
    print("   - View real-time data and charts")
    print("\n⏹️  Press Ctrl+C to stop all services")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down KPP Simulator...")

if __name__ == "__main__":
    main() 