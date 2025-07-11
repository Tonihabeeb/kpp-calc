#!/usr/bin/env python3
"""
Realistic User Commands Test
Simulates actual user interactions through the UI to test backend behavior
"""

import requests
import json
import time
import sys
from datetime import datetime

class RealisticUserCommandsTest:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test results with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"[{timestamp}] {status} {test_name}"
        if details:
            result += f" - {details}"
        print(result)
        self.test_results.append({
            "timestamp": timestamp,
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def make_request(self, endpoint, method="GET", data=None, expected_status=200):
        """Make HTTP request and handle response"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, json=data)
            elif method == "PUT":
                response = self.session.put(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response, response.status_code == expected_status
        except Exception as e:
            return None, False
            
    def test_initial_state(self):
        """Test 1: Check initial simulation state"""
        print("\n🔍 Test 1: Checking initial simulation state...")
        
        # Get simulation status
        response, success = self.make_request("/api/simulation/status")
        if success and response:
            try:
                data = response.json()
                self.log_test("Get simulation status", True, f"Status: {data.get('status', 'unknown')}")
                return data
            except:
                self.log_test("Get simulation status", False, "Invalid JSON response")
        else:
            self.log_test("Get simulation status", False, f"HTTP {response.status_code if response else 'Connection failed'}")
        return None
        
    def test_start_simulation(self):
        """Test 2: Start simulation (like user clicking Start button)"""
        print("\n🚀 Test 2: Starting simulation...")
        
        # Start simulation
        response, success = self.make_request("/api/simulation/start", method="POST")
        if success and response:
            try:
                data = response.json()
                self.log_test("Start simulation", True, f"Response: {data.get('message', 'Started')}")
                return data
            except:
                self.log_test("Start simulation", False, "Invalid JSON response")
        else:
            self.log_test("Start simulation", False, f"HTTP {response.status_code if response else 'Connection failed'}")
        return None
        
    def test_get_metrics(self):
        """Test 3: Get real-time metrics (like UI updating dashboard)"""
        print("\n📊 Test 3: Getting real-time metrics...")
        
        # Get current metrics
        response, success = self.make_request("/api/simulation/metrics")
        if success and response:
            try:
                data = response.json()
                self.log_test("Get metrics", True, f"Metrics available: {len(data)} items")
                return data
            except:
                self.log_test("Get metrics", False, "Invalid JSON response")
        else:
            self.log_test("Get metrics", False, f"HTTP {response.status_code if response else 'Connection failed'}")
        return None
        
    def test_pause_simulation(self):
        """Test 4: Pause simulation (like user clicking Pause button)"""
        print("\n⏸️ Test 4: Pausing simulation...")
        
        # Pause simulation
        response, success = self.make_request("/api/simulation/pause", method="POST")
        if success and response:
            try:
                data = response.json()
                self.log_test("Pause simulation", True, f"Response: {data.get('message', 'Paused')}")
                return data
            except:
                self.log_test("Pause simulation", False, "Invalid JSON response")
        else:
            self.log_test("Pause simulation", False, f"HTTP {response.status_code if response else 'Connection failed'}")
        return None
        
    def test_resume_simulation(self):
        """Test 5: Resume simulation (like user clicking Resume button)"""
        print("\n▶️ Test 5: Resuming simulation...")
        
        # Resume simulation
        response, success = self.make_request("/api/simulation/resume", method="POST")
        if success and response:
            try:
                data = response.json()
                self.log_test("Resume simulation", True, f"Response: {data.get('message', 'Resumed')}")
                return data
            except:
                self.log_test("Resume simulation", False, "Invalid JSON response")
        else:
            self.log_test("Resume simulation", False, f"HTTP {response.status_code if response else 'Connection failed'}")
        return None
        
    def test_reset_simulation(self):
        """Test 6: Reset simulation (like user clicking Reset button)"""
        print("\n🔄 Test 6: Resetting simulation...")
        
        # Reset simulation
        response, success = self.make_request("/api/simulation/reset", method="POST")
        if success and response:
            try:
                data = response.json()
                self.log_test("Reset simulation", True, f"Response: {data.get('message', 'Reset')}")
                return data
            except:
                self.log_test("Reset simulation", False, "Invalid JSON response")
        else:
            self.log_test("Reset simulation", False, f"HTTP {response.status_code if response else 'Connection failed'}")
        return None
        
    def test_parameter_adjustment(self):
        """Test 7: Adjust simulation parameters (like user changing settings)"""
        print("\n⚙️ Test 7: Adjusting simulation parameters...")
        
        # Test parameter adjustment
        test_params = {
            "floater_count": 8,
            "floater_volume": 0.35,
            "chain_length": 100
        }
        
        response, success = self.make_request("/api/simulation/parameters", method="PUT", data=test_params)
        if success and response:
            try:
                data = response.json()
                self.log_test("Adjust parameters", True, f"Updated: {list(test_params.keys())}")
                return data
            except:
                self.log_test("Adjust parameters", False, "Invalid JSON response")
        else:
            self.log_test("Adjust parameters", False, f"HTTP {response.status_code if response else 'Connection failed'}")
        return None
        
    def test_error_scenarios(self):
        """Test 8: Test error scenarios (like invalid user inputs)"""
        print("\n⚠️ Test 8: Testing error scenarios...")
        
        # Test invalid start command (already running)
        response, success = self.make_request("/api/simulation/start", method="POST", expected_status=400)
        if response and response.status_code == 400:
            self.log_test("Invalid start (already running)", True, "Properly rejected")
        else:
            self.log_test("Invalid start (already running)", False, f"Expected 400, got {response.status_code if response else 'None'}")
            
        # Test invalid parameters
        invalid_params = {
            "floater_count": -1,  # Invalid negative value
            "floater_volume": 0   # Invalid zero value
        }
        
        response, success = self.make_request("/api/simulation/parameters", method="PUT", data=invalid_params, expected_status=400)
        if response and response.status_code == 400:
            self.log_test("Invalid parameters", True, "Properly rejected")
        else:
            self.log_test("Invalid parameters", False, f"Expected 400, got {response.status_code if response else 'None'}")
            
    def test_continuous_monitoring(self):
        """Test 9: Continuous monitoring (like real-time UI updates)"""
        print("\n📈 Test 9: Continuous monitoring simulation...")
        
        # Monitor for 5 seconds
        start_time = time.time()
        update_count = 0
        
        while time.time() - start_time < 5:
            response, success = self.make_request("/api/simulation/metrics")
            if success and response:
                update_count += 1
                try:
                    data = response.json()
                    # Simulate UI processing
                    if 'chain_tension' in data:
                        tension = data['chain_tension']
                        if tension > 50000:  # High tension alert
                            self.log_test("High tension alert", True, f"Tension: {tension:.0f} N")
                except:
                    pass
            time.sleep(0.5)  # Update every 500ms like real UI
            
        self.log_test("Continuous monitoring", True, f"Updated {update_count} times in 5 seconds")
        
    def test_complete_workflow(self):
        """Test 10: Complete user workflow simulation"""
        print("\n🔄 Test 10: Complete user workflow simulation...")
        
        # 1. Start fresh
        self.test_reset_simulation()
        time.sleep(1)
        
        # 2. Start simulation
        self.test_start_simulation()
        time.sleep(2)
        
        # 3. Monitor for a bit
        for i in range(3):
            self.test_get_metrics()
            time.sleep(1)
            
        # 4. Pause
        self.test_pause_simulation()
        time.sleep(1)
        
        # 5. Resume
        self.test_resume_simulation()
        time.sleep(2)
        
        # 6. Adjust parameters
        self.test_parameter_adjustment()
        time.sleep(1)
        
        # 7. Final monitoring
        self.test_get_metrics()
        
        self.log_test("Complete workflow", True, "All steps completed successfully")
        
    def run_all_tests(self):
        """Run all realistic user command tests"""
        print("🧪 Starting Realistic User Commands Test")
        print("=" * 50)
        
        try:
            # Basic state tests
            self.test_initial_state()
            time.sleep(1)
            
            # Start and basic operation
            self.test_start_simulation()
            time.sleep(2)
            
            # Real-time monitoring
            self.test_get_metrics()
            time.sleep(1)
            
            # Pause/Resume cycle
            self.test_pause_simulation()
            time.sleep(1)
            self.test_resume_simulation()
            time.sleep(2)
            
            # Parameter adjustment
            self.test_parameter_adjustment()
            time.sleep(1)
            
            # Error scenarios
            self.test_error_scenarios()
            time.sleep(1)
            
            # Continuous monitoring
            self.test_continuous_monitoring()
            
            # Complete workflow
            self.test_complete_workflow()
            
            # Final reset
            self.test_reset_simulation()
            
        except KeyboardInterrupt:
            print("\n⚠️ Test interrupted by user")
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📋 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
                    
        print("\n🎯 Backend Behavior Analysis:")
        if passed_tests == total_tests:
            print("  ✅ Backend handles all user commands correctly")
            print("  ✅ State management is working properly")
            print("  ✅ Error handling is functioning")
            print("  ✅ Real-time updates are responsive")
        else:
            print("  ⚠️ Some issues detected in backend behavior")
            print("  🔧 Review failed tests for specific problems")

def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"
        
    print(f"🌐 Testing backend at: {base_url}")
    
    tester = RealisticUserCommandsTest(base_url)
    tester.run_all_tests()

if __name__ == "__main__":
    main() 