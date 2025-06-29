#!/usr/bin/env python3
"""
Quick System Health Check for KPP Simulator
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def quick_health_check():
    """Perform a quick health check of the simulator"""
    print("KPP Simulator - Quick Health Check")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Basic imports
    total_tests += 1
    try:
        import flask, numpy, pandas, matplotlib
        print("✓ Core dependencies available")
        tests_passed += 1
    except ImportError as e:
        print(f"✗ Missing dependencies: {e}")
    
    # Test 2: Config system
    total_tests += 1
    try:
        from config.parameter_schema import PARAM_SCHEMA
        print(f"✓ Config system working ({len(PARAM_SCHEMA)} parameters)")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Config system failed: {e}")
    
    # Test 3: Simulation engine
    total_tests += 1
    try:
        from simulation.engine import SimulationEngine
        import queue
        
        params = {
            "num_floaters": 4,
            "floater_volume": 0.3,
            "floater_mass_empty": 18.0,
            "floater_area": 0.035,
            "airPressure": 3.0
        }
        data_queue = queue.Queue()
        engine = SimulationEngine(params, data_queue)
        engine.reset()
        engine.step()
        
        print("✓ Simulation engine working")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Simulation engine failed: {e}")
    
    # Test 4: Flask app
    total_tests += 1
    try:
        import app
        if hasattr(app, 'app'):
            with app.app.test_client() as client:
                response = client.get('/health')
                if response.status_code == 200:
                    print("✓ Flask app and API working")
                    tests_passed += 1
                else:
                    print(f"✗ Flask app issues (status: {response.status_code})")
        else:
            print("✗ Flask app not found")
    except Exception as e:
        print(f"✗ Flask app failed: {e}")
    
    # Test 5: Frontend files
    total_tests += 1
    required_files = [
        "templates/index.html",
        "static/css/style.css", 
        "static/js/main.js"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if not missing_files:
        print("✓ Frontend files present")
        tests_passed += 1
    else:
        print(f"✗ Missing frontend files: {missing_files}")
    
    # Summary
    print("\n" + "=" * 40)
    print(f"Health Check: {tests_passed}/{total_tests} tests passed")
    success_rate = (tests_passed / total_tests) * 100
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 SYSTEM HEALTHY - Ready to run!")
        return True
    elif success_rate >= 60:
        print("⚠️  SYSTEM FUNCTIONAL - Some issues detected")
        return True
    else:
        print("❌ SYSTEM ISSUES - Needs attention")
        return False

if __name__ == "__main__":
    healthy = quick_health_check()
    
    if healthy:
        print("\nTo start the simulator:")
        print("1. Run: python app.py")
        print("2. Open: http://127.0.0.1:5000")
        
        # Try to start the server automatically
        try:
            print("\nAttempting to start server...")
            import app
            app.app.run(debug=True, host='127.0.0.1', port=5000, threaded=True)
        except KeyboardInterrupt:
            print("\nServer stopped by user")
        except Exception as e:
            print(f"Server start failed: {e}")
    else:
        print("\nPlease fix the issues above before starting the simulator.")
