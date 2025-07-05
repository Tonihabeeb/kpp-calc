#!/usr/bin/env python3
"""
KPP Simulator Server Startup Script
This script starts the Flask server with proper error handling
"""
import os
import sys
import subprocess

# Add current directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

def start_server():
    """Start the KPP Simulator Flask server"""
    try:
        print("Starting KPP Simulator Flask Server...")
        print("=" * 50)
        
        # Try to import and run the app
        import app
        print("✓ App module imported successfully")
        
        # Start the server
        print("Starting server on http://127.0.0.1:9100")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        
        app.app.run(debug=True, threaded=True, host='127.0.0.1', port=9100)
        
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        
        # Try fallback simple server
        print("\nTrying fallback simple server...")
        try:
            subprocess.run([sys.executable, "test_flask_simple.py"])
        except Exception as fallback_error:
            print(f"Fallback server also failed: {fallback_error}")

if __name__ == "__main__":
    start_server()
sys.path.insert(0, project_dir)

if __name__ == "__main__":
    print("Starting KPP Simulation Server for Phase 8 Testing...")
    print("Please wait while the server initializes...")

    try:
        from app import app

        print("\n✅ Flask app loaded successfully!")
        print("🚀 Starting server on http://localhost:9100")
        print("📊 All Phase 8 advanced systems integrated and ready!")
        print("\n🔗 Available endpoints:")
        print("   - Web UI: http://localhost:9100")
        print("   - API Status: http://localhost:9100/status")
        print(
            "   - Advanced Systems: /data/drivetrain_status, /data/electrical_status, etc."
        )
        print("\n" + "=" * 60)

        app.run(host="0.0.0.0", port=9100, debug=True, threaded=True)

    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
