import subprocess
import sys
import os
import time
import requests

# Change to the correct directory
os.chdir(r"h:\My Drive\kpp force calc")

print("Testing Phase 7 Pneumatic System UI Integration")
print("=" * 50)

# Try to check if Flask is already running
try:
    response = requests.get("http://localhost:5000", timeout=2)
    print("✓ Flask app is already running!")
    app_running = True
except:
    print("Flask app is not running, attempting to start...")
    app_running = False

# If not running, try to start it
if not app_running:
    try:
        # Start Flask app in background
        print("Starting Flask application...")
        process = subprocess.Popen([sys.executable, "app.py"], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        print("Waiting for Flask app to start...")
        time.sleep(5)
        
        # Test if it's responding
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            print("✓ Flask app started successfully!")
            app_running = True
        else:
            print(f"✗ Flask app returned status {response.status_code}")
            
    except Exception as e:
        print(f"✗ Failed to start Flask app: {e}")

# Test pneumatic endpoints if app is running
if app_running:
    print("\nTesting pneumatic endpoints...")
    
    endpoints = [
        "/data/pneumatic_status",
        "/data/optimization_recommendations",
        "/data/energy_balance",
        "/data/summary"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:5000{endpoint}", timeout=5)
            print(f"{endpoint}: Status {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Response keys: {list(data.keys())}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n" + "="*50)
    print("MANUAL TESTING INSTRUCTIONS:")
    print("="*50)
    print("1. Open http://localhost:5000 in your browser")
    print("2. Scroll down to find 'Phase 7 Pneumatic System Analysis' section")
    print("3. Click 'Start' button to begin simulation")
    print("4. Observe these pneumatic metrics updating:")
    print("   - Tank Pressure (bar)")
    print("   - System Efficiency (%)")
    print("   - Capacity Factor (%)")
    print("   - Thermal Efficiency (%)")
    print("   - Performance Metrics (Average/Peak Efficiency, Power Factor, Availability)")
    print("   - Energy Balance (Input/Output Energy, Overall Efficiency)")
    print("   - Optimization Recommendations")
    print("5. Verify metrics update every 2 seconds")
    print("6. Check that recommendations appear as simulation progresses")
    print("\nExpected behavior:")
    print("- Pneumatic metrics should show realistic values (not all zeros)")
    print("- Tank pressure should vary during operation")
    print("- Efficiency metrics should be between 0-100%")
    print("- Optimization recommendations should appear after a few seconds")
else:
    print("\n✗ Cannot test UI - Flask app is not running")
    print("Try running 'python app.py' manually and then open http://localhost:5000")

print("\nTest completed!")
