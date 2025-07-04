#!/usr/bin/env python3
"""
Restart all KPP simulator servers with improved electrical engagement parameters
"""

import subprocess
import time
import os
import signal
import sys

def kill_existing_processes():
    """Kill any existing Python processes that might be running the servers"""
    print("🔄 Stopping existing servers...")
    
    try:
        # Try to stop gracefully first
        import requests
        
        servers = [
            "http://localhost:5000/stop",
            "http://localhost:5001/stop", 
            "http://localhost:5002/stop"
        ]
        
        for server in servers:
            try:
                requests.post(server, timeout=2)
                print(f"   Stopped: {server}")
            except:
                pass
                
    except ImportError:
        pass
    
    # Force kill any Python processes (be careful - this kills ALL Python processes)
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(['taskkill', '/f', '/im', 'python.exe'], 
                          capture_output=True, check=False)
        else:  # Unix-like
            subprocess.run(['pkill', '-f', 'python'], 
                          capture_output=True, check=False)
        time.sleep(2)
        print("   Killed existing Python processes")
    except Exception as e:
        print(f"   Warning: Could not kill processes: {e}")

def start_servers():
    """Start all three servers with improved parameters"""
    print("🚀 Starting KPP Simulator servers...")
    
    # Server configurations
    servers = [
        {
            'name': 'Flask Backend (Port 5000)',
            'command': ['python', 'app.py'],
            'wait': 3
        },
        {
            'name': 'Main Simulation Server (Port 5001)', 
            'command': ['python', 'main.py'],
            'wait': 2
        },
        {
            'name': 'Dash Frontend (Port 5002)',
            'command': ['python', 'dash_app.py'],
            'wait': 2
        }
    ]
    
    processes = []
    
    for server in servers:
        print(f"\n🔧 Starting {server['name']}...")
        
        try:
            # Start process in background
            process = subprocess.Popen(
                server['command'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            processes.append({
                'name': server['name'],
                'process': process,
                'command': ' '.join(server['command'])
            })
            
            print(f"   Started PID: {process.pid}")
            time.sleep(server['wait'])
            
            # Check if process is still running
            if process.poll() is None:
                print(f"   ✅ {server['name']} started successfully")
            else:
                stdout, stderr = process.communicate()
                print(f"   ❌ {server['name']} failed to start")
                print(f"   Error: {stderr.decode()}")
                
        except Exception as e:
            print(f"   ❌ Failed to start {server['name']}: {e}")
    
    return processes

def verify_servers():
    """Verify all servers are responding"""
    print("\n🔍 Verifying server status...")
    
    import requests
    
    servers = [
        ('Flask Backend', 'http://localhost:5000/status'),
        ('Main Server', 'http://localhost:5001/state'),
        ('Dash Frontend', 'http://localhost:5002/')
    ]
    
    all_good = True
    
    for name, url in servers:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {name}: Online")
            else:
                print(f"   ⚠️  {name}: Status {response.status_code}")
                all_good = False
        except Exception as e:
            print(f"   ❌ {name}: Not responding ({e})")
            all_good = False
    
    return all_good

def configure_electrical_system():
    """Configure the electrical system with improved parameters"""
    print("\n⚡ Configuring electrical system...")
    
    import requests
    
    # Enhanced electrical parameters for better engagement
    config_params = {
        "num_floaters": 10,
        "floater_volume": 0.4,
        "floater_mass_empty": 16.0,
        "air_pressure": 250000,
        "target_load_factor": 0.6,  # 60% electrical load
        "electrical_engagement_threshold": 1000.0,
        "min_mechanical_power_for_engagement": 1000.0,
        "load_management_enabled": True,
        "bootstrap_mode": True,
        "max_chain_speed": 60.0,
        "target_rpm": 375.0,
        "generator_efficiency": 0.93
    }
    
    try:
        # Update parameters on Flask server
        response = requests.post('http://localhost:5000/update_params', 
                               json=config_params, 
                               timeout=10)
        print(f"   📋 Updated parameters: {response.text}")
        
        # Start simulation with these parameters
        response = requests.post('http://localhost:5000/start', 
                               json=config_params, 
                               timeout=10)
        result = response.json()
        print(f"   🚀 Started simulation: {result}")
        
        if result.get('status') == 'ok':
            print("   ✅ Electrical system configured and started")
            return True
        else:
            print(f"   ❌ Start failed: {result}")
            return False
            
    except Exception as e:
        print(f"   ❌ Configuration failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 KPP Simulator Server Restart & Configuration")
    print("=" * 60)
    
    try:
        # Step 1: Stop existing servers
        kill_existing_processes()
        
        # Step 2: Start all servers
        processes = start_servers()
        
        # Step 3: Wait for startup
        print("\n⏳ Waiting for servers to initialize...")
        time.sleep(8)
        
        # Step 4: Verify servers
        if verify_servers():
            print("\n✅ All servers online!")
            
            # Step 5: Configure electrical system
            if configure_electrical_system():
                print("\n" + "=" * 60)
                print("🎉 KPP Simulator Ready!")
                print("✅ All servers running")
                print("✅ Electrical system configured") 
                print("✅ Load management enabled")
                print("✅ Generator will act as electromagnetic brake")
                print("\n🌐 Access points:")
                print("   - Flask Backend: http://localhost:5000")
                print("   - Main Server: http://localhost:5001") 
                print("   - Dash Dashboard: http://localhost:5002")
                print("=" * 60)
            else:
                print("\n❌ Electrical system configuration failed")
        else:
            print("\n❌ Some servers failed to start properly")
            print("   Check individual server logs for details")
            
    except KeyboardInterrupt:
        print("\n⏹️  Restart interrupted by user")
    except Exception as e:
        print(f"\n❌ Restart failed: {e}")
        import traceback
        traceback.print_exc() 