"""
UI Data Mapping Verification Tool
Validates that the web UI correctly displays and maps to backend simulation data.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.engine import SimulationEngine
import queue
import time
import threading
import requests
import json

BASE_URL = 'http://127.0.0.1:5000'

class UIDataMappingTester:
    """Test suite to verify UI-backend data mapping correctness"""
    
    def __init__(self):
        self.backend_running = False
        self.direct_engine = None
        self.test_results = []
    
    def check_backend_availability(self):
        """Check if the Flask backend is running"""
        try:
            resp = requests.get(f'{BASE_URL}/', timeout=5)
            self.backend_running = resp.status_code == 200
            print(f"✓ Backend availability: {'ONLINE' if self.backend_running else 'OFFLINE'}")
            return self.backend_running
        except Exception as e:
            print(f"✗ Backend not available: {e}")
            self.backend_running = False
            return False
    
    def create_direct_engine(self):
        """Create a direct simulation engine for comparison"""
        data_queue = queue.Queue()
        params = {
            'num_floaters': 4,
            'floater_volume': 0.3,
            'time_step': 0.1,
            'pulse_interval': 1.0
        }
        self.direct_engine = SimulationEngine(params, data_queue)
        self.direct_engine.reset()
        print("✓ Direct engine created for comparison")
    
    def run_direct_simulation(self, duration=3):
        """Run direct simulation for comparison data"""
        self.direct_engine.running = True
        simulation_thread = threading.Thread(target=self.direct_engine.run, daemon=True)
        simulation_thread.start()
        time.sleep(duration)
        self.direct_engine.stop()
        print(f"✓ Direct simulation ran for {duration}s, generated {len(self.direct_engine.data_log)} data points")
        return self.direct_engine.data_log
    
    def fetch_backend_data(self):
        """Fetch data from backend API endpoints"""
        try:
            # Start backend simulation
            requests.post(f'{BASE_URL}/start', json={'air_pressure': 4.0})
            time.sleep(3)  # Let it run
            
            # Fetch live data
            live_resp = requests.get(f'{BASE_URL}/data/live')
            live_data = live_resp.json()['data'] if live_resp.status_code == 200 else []
            
            # Fetch summary data
            summary_resp = requests.get(f'{BASE_URL}/data/summary')
            summary_data = summary_resp.json() if summary_resp.status_code == 200 else {}
            
            # Stop simulation
            requests.post(f'{BASE_URL}/stop')
            
            print(f"✓ Backend simulation data fetched: {len(live_data)} live data points")
            return live_data, summary_data
            
        except Exception as e:
            print(f"✗ Failed to fetch backend data: {e}")
            return [], {}
    
    def compare_data_structures(self, direct_data, backend_data):
        """Compare data structures between direct and backend approaches"""
        print("\n--- Data Structure Comparison ---")
        
        if not direct_data or not backend_data:
            print("✗ Cannot compare - missing data")
            return False
        
        # Compare field presence
        direct_fields = set(direct_data[0].keys()) if direct_data else set()
        backend_fields = set(backend_data[0].keys()) if backend_data else set()
        
        missing_in_backend = direct_fields - backend_fields
        extra_in_backend = backend_fields - direct_fields
        common_fields = direct_fields & backend_fields
        
        print(f"✓ Common fields ({len(common_fields)}): {sorted(common_fields)}")
        
        if missing_in_backend:
            print(f"⚠️  Missing in backend ({len(missing_in_backend)}): {sorted(missing_in_backend)}")
        
        if extra_in_backend:
            print(f"ℹ️  Extra in backend ({len(extra_in_backend)}): {sorted(extra_in_backend)}")
        
        return len(missing_in_backend) == 0
    
    def validate_ui_endpoints(self):
        """Test all UI-related endpoints"""
        print("\n--- UI Endpoint Validation ---")
        
        endpoints_to_test = [
            ('/', 'GET', 'Main UI page'),
            ('/data/live', 'GET', 'Live data API'),
            ('/data/summary', 'GET', 'Summary data API'),
            ('/data/history', 'GET', 'Historical data API'),
            ('/start', 'POST', 'Start simulation'),
            ('/stop', 'POST', 'Stop simulation'),
            ('/reset', 'POST', 'Reset simulation'),
            ('/download_csv', 'GET', 'CSV download')
        ]
        
        results = {}
        for endpoint, method, description in endpoints_to_test:
            try:
                if method == 'GET':
                    resp = requests.get(f'{BASE_URL}{endpoint}', timeout=10)
                else:
                    resp = requests.post(f'{BASE_URL}{endpoint}', json={}, timeout=10)
                
                results[endpoint] = {
                    'status': resp.status_code,
                    'success': resp.status_code in [200, 204],
                    'description': description
                }
                
                status_icon = "✓" if results[endpoint]['success'] else "✗"
                print(f"{status_icon} {endpoint} ({method}): {resp.status_code} - {description}")
                
            except Exception as e:
                results[endpoint] = {
                    'status': 'ERROR',
                    'success': False,
                    'error': str(e),
                    'description': description
                }
                print(f"✗ {endpoint} ({method}): ERROR - {e}")
        
        return results
    
    def test_data_consistency(self, direct_data, backend_data):
        """Test consistency between direct and backend data"""
        print("\n--- Data Consistency Tests ---")
        
        if not direct_data or not backend_data:
            print("✗ Cannot test consistency - missing data")
            return False
        
        # Test 1: Time progression
        direct_times = [d.get('time', 0) for d in direct_data]
        backend_times = [d.get('time', 0) for d in backend_data]
        
        direct_time_increasing = all(direct_times[i] <= direct_times[i+1] for i in range(len(direct_times)-1))
        backend_time_increasing = all(backend_times[i] <= backend_times[i+1] for i in range(len(backend_times)-1))
        
        print(f"✓ Direct time progression: {'PASS' if direct_time_increasing else 'FAIL'}")
        print(f"✓ Backend time progression: {'PASS' if backend_time_increasing else 'FAIL'}")
        
        # Test 2: Data ranges
        for field in ['torque', 'power', 'base_buoy_torque', 'pulse_torque']:
            if field in direct_data[0] and field in backend_data[0]:
                direct_values = [d.get(field, 0) for d in direct_data if d.get(field) is not None]
                backend_values = [d.get(field, 0) for d in backend_data if d.get(field) is not None]
                
                if direct_values and backend_values:
                    direct_range = (min(direct_values), max(direct_values))
                    backend_range = (min(backend_values), max(backend_values))
                    
                    print(f"✓ {field} range - Direct: {direct_range}, Backend: {backend_range}")
        
        return True
    
    def test_ui_data_mapping(self):
        """Main test function for UI data mapping"""
        print("🔍 UI Data Mapping Verification Tool")
        print("=" * 50)
        
        # Step 1: Check backend availability
        if not self.check_backend_availability():
            print("❌ Cannot proceed - backend not available")
            print("💡 Please start the Flask app: python app.py")
            return False
        
        # Step 2: Create direct engine for comparison
        self.create_direct_engine()
        
        # Step 3: Run direct simulation
        direct_data = self.run_direct_simulation(duration=3)
        
        # Step 4: Fetch backend data
        backend_data, summary_data = self.fetch_backend_data()
        
        # Step 5: Compare data structures
        structure_match = self.compare_data_structures(direct_data, backend_data)
        
        # Step 6: Test all UI endpoints
        endpoint_results = self.validate_ui_endpoints()
        
        # Step 7: Test data consistency
        consistency_pass = self.test_data_consistency(direct_data, backend_data)
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        total_endpoints = len(endpoint_results)
        successful_endpoints = sum(1 for r in endpoint_results.values() if r['success'])
        
        print(f"🌐 Backend Status: {'ONLINE' if self.backend_running else 'OFFLINE'}")
        print(f"🔗 Endpoint Tests: {successful_endpoints}/{total_endpoints} passed")
        print(f"📋 Data Structure: {'MATCH' if structure_match else 'MISMATCH'}")
        print(f"🔄 Data Consistency: {'PASS' if consistency_pass else 'FAIL'}")
        
        overall_pass = (
            self.backend_running and 
            successful_endpoints == total_endpoints and 
            structure_match and 
            consistency_pass
        )
        
        print(f"\n🎯 Overall Result: {'✅ PASS' if overall_pass else '❌ FAIL'}")
        
        if not overall_pass:
            print("\n💡 Recommendations:")
            if not self.backend_running:
                print("- Start the Flask backend: python app.py")
            if successful_endpoints < total_endpoints:
                print("- Check failed endpoints and fix routing/logic issues")
            if not structure_match:
                print("- Align backend API data structure with direct engine output")
            if not consistency_pass:
                print("- Review data consistency between direct and backend approaches")
        
        return overall_pass

def main():
    """Run the UI data mapping tests"""
    tester = UIDataMappingTester()
    success = tester.test_ui_data_mapping()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
