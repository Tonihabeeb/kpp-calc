#!/usr/bin/env python3
"""
Comprehensive KPP Simulator Startup and Diagnostic Tool
"""
import os
import sys
import time
import subprocess
import webbrowser

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def check_python_environment():
    """Check if Python environment is properly configured"""
    print("1. Checking Python Environment...")
    try:
        print(f"   Python version: {sys.version}")
        print(f"   Python executable: {sys.executable}")
        print("   ✓ Python environment OK")
        return True
    except Exception as e:
        print(f"   ✗ Python environment error: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n2. Checking Dependencies...")
    required_packages = ['flask', 'numpy', 'pandas', 'matplotlib', 'pydantic']
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✓ {package}")
        except ImportError:
            print(f"   ✗ {package} - MISSING")
            return False
    
    print("   ✓ All dependencies OK")
    return True

def test_imports():
    """Test critical imports"""
    print("\n3. Testing Critical Imports...")
    
    try:
        from config.parameter_schema import PARAM_SCHEMA
        print("   ✓ Config imports")
    except Exception as e:
        print(f"   ✗ Config imports failed: {e}")
        return False
    
    try:
        from simulation.engine import SimulationEngine
        print("   ✓ Simulation engine")
    except Exception as e:
        print(f"   ✗ Simulation engine failed: {e}")
        return False
    
    try:
        from utils.backend_logger import setup_backend_logger
        print("   ✓ Backend logger")
    except Exception as e:
        print(f"   ✗ Backend logger failed: {e}")
        return False
    
    print("   ✓ All imports OK")
    return True

def test_flask_app():
    """Test Flask app creation"""
    print("\n4. Testing Flask App...")
    
    try:
        import app
        print("   ✓ App module imported")
        
        if hasattr(app, 'app'):
            print("   ✓ Flask instance found")
            
            # Test a route
            with app.app.test_client() as client:
                response = client.get('/health')
                if response.status_code == 200:
                    print("   ✓ Health endpoint working")
                else:
                    print(f"   ! Health endpoint returned {response.status_code}")
                    
            return app.app
        else:
            print("   ✗ No Flask instance found")
            return None
            
    except Exception as e:
        print(f"   ✗ Flask app test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def start_server(flask_app):
    """Start the Flask server"""
    print("\n5. Starting Flask Server...")
    print("=" * 50)
    print("KPP Simulator Web Interface")
    print("Server will be available at: http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Try to open browser automatically
        time.sleep(1)
        try:
            webbrowser.open('http://127.0.0.1:5000')
        except:
            pass  # Browser opening is optional
            
        flask_app.run(debug=True, threaded=True, host='127.0.0.1', port=5000)
        
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
    except Exception as e:
        print(f"\nServer error: {e}")
        import traceback
        traceback.print_exc()

def run_fallback_server():
    """Run a simple fallback server"""
    print("\nStarting fallback simple server...")
    try:
        subprocess.run([sys.executable, "test_flask_simple.py"])
    except Exception as e:
        print(f"Fallback server failed: {e}")

def main():
    """Main diagnostic and startup routine"""
    print("KPP Simulator - Startup Diagnostic & Server")
    print("=" * 50)
    
    # Run all checks
    checks_passed = (
        check_python_environment() and
        check_dependencies() and
        test_imports()
    )
    
    if not checks_passed:
        print("\n✗ Some checks failed. Please fix the issues above.")
        return
    
    # Test Flask app
    flask_app = test_flask_app()
    
    if flask_app:
        print("\n✓ All checks passed! Starting main server...")
        start_server(flask_app)
    else:
        print("\n! Main app failed, trying fallback server...")
        run_fallback_server()

if __name__ == "__main__":
    main()
