import os
import sys
import time
import requests
import subprocess
import importlib

COMPONENT_MANAGER_PATH = os.path.join('kpp_simulator', 'managers', 'component_manager.py')


def check_and_install_dependencies():
    """Check and install required dependencies."""
    required_packages = ['yaml', 'requests']
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f'✅ {package} already installed.')
        except ImportError:
            print(f'📦 Installing {package}...')
            try:
                if package == 'yaml':
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyyaml'])
                else:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f'✅ {package} installed successfully.')
            except subprocess.CalledProcessError as e:
                print(f'❌ Failed to install {package}: {e}')
                return False
    return True


def check_and_fix_operation_history():
    """Check for operation_history in ComponentManager and add if missing."""
    with open(COMPONENT_MANAGER_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    found = any('self.operation_history' in line for line in lines)
    if found:
        print('✅ operation_history already present.')
        return False  # No change needed

    # Find logger setup line
    for idx, line in enumerate(lines):
        if 'self.logger = logging.getLogger' in line:
            insert_idx = idx + 1
            break
    else:
        print('❌ Could not find logger setup in ComponentManager.')
        return False

    # Insert operation_history after logger setup
    lines.insert(insert_idx, '        # Operation history for tracking system operations\n        self.operation_history = []\n\n')
    with open(COMPONENT_MANAGER_PATH, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print('🛠️  Added operation_history to ComponentManager.')
    return True


def restart_flask_server():
    """Restart the Flask server."""
    print('🔄 Restarting Flask server...')
    try:
        # Kill existing Flask process if running
        subprocess.run(['taskkill', '/f', '/im', 'python.exe'], capture_output=True)
        time.sleep(2)
        
        # Start Flask server in background
        subprocess.Popen([sys.executable, 'app.py'], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
        print('✅ Flask server restarted in background.')
        return True
    except Exception as e:
        print(f'❌ Failed to restart Flask server: {e}')
        print('⚠️  Please manually restart the Flask server.')
        return False


def test_compressor_endpoint():
    """Test the /api/simulation/compressor endpoint."""
    url = 'http://localhost:9100/api/simulation/compressor'
    try:
        resp = requests.post(url, json={'action': 'start'}, timeout=5)
        print(f'Compressor endpoint status: {resp.status_code}')
        print(f'Response: {resp.text}')
        if resp.status_code == 200 and 'success' in resp.json() and resp.json()['success']:
            print('✅ Compressor started successfully via API.')
            return True
        else:
            print('❌ Compressor API call failed.')
            return False
    except Exception as e:
        print(f'❌ Error calling compressor endpoint: {e}')
        return False


def main():
    print('--- Automated KPP Simulator Setup and Fix ---')
    
    # Step 1: Check and install dependencies
    print('\n📦 Step 1: Checking Dependencies')
    if not check_and_install_dependencies():
        print('❌ Failed to install required dependencies.')
        return
    
    # Step 2: Check and fix operation_history
    print('\n🔧 Step 2: Checking Component Manager')
    changed = check_and_fix_operation_history()
    
    # Step 3: Restart Flask server if needed
    if changed:
        print('\n🔄 Step 3: Restarting Flask Server')
        if restart_flask_server():
            print('⏳ Waiting for Flask server to start...')
            time.sleep(10)  # Give more time for server to start
        else:
            print('⚠️  Please manually restart the Flask server and run the test again.')
            return
    else:
        print('\n✅ No code changes needed.')
    
    # Step 4: Test compressor endpoint
    print('\n🧪 Step 4: Testing Compressor Endpoint')
    success = test_compressor_endpoint()
    
    # Summary
    print('\n--- Summary ---')
    if success:
        print('🎉 All automated steps completed successfully!')
        print('✅ Dependencies installed')
        print('✅ Component Manager fixed')
        print('✅ Flask server running')
        print('✅ Compressor endpoint working')
    else:
        print('❌ Some steps failed. Check the output above for details.')

if __name__ == '__main__':
    main() 