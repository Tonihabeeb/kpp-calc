#!/usr/bin/env python3
"""
KPP Simulator Dashboard Startup Script
Quick launcher for the new Dash-based frontend
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Main startup function"""
    print("=" * 60)
    print("🚀 KPP Simulator Dashboard Launcher")
    print("=" * 60)
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print(f"📁 Working directory: {script_dir}")
    print("🔧 Starting Dash application...")
    print("=" * 60)
    
    try:
        # Run the Dash app
        subprocess.run([sys.executable, "dash_app.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting dashboard: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    print("👋 Dashboard shutdown complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())
