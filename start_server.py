#!/usr/bin/env python3
"""
Quick server startup script for testing Phase 8 integration
"""

import sys
import os

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

if __name__ == "__main__":
    print("Starting KPP Simulation Server for Phase 8 Testing...")
    print("Please wait while the server initializes...")
    
    try:
        from app import app
        print("\n✅ Flask app loaded successfully!")
        print("🚀 Starting server on http://localhost:5000")
        print("📊 All Phase 8 advanced systems integrated and ready!")
        print("\n🔗 Available endpoints:")
        print("   - Web UI: http://localhost:5000")
        print("   - API Status: http://localhost:5000/status")
        print("   - Advanced Systems: /data/drivetrain_status, /data/electrical_status, etc.")
        print("\n" + "="*60)
        
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
