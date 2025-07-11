#!/usr/bin/env python3
"""
State Management Test
Focused test for drivetrain state management issues
"""

import requests
import time
import json
from datetime import datetime

class StateManagementTest:
    def __init__(self, base_url="http://localhost:9100"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {message}")
        
    def make_request(self, endpoint, method="GET", data=None):
        """Make HTTP request"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            return response
        except Exception as e:
            print(f"Request failed: {e}")
            return None
            
    def get_status(self):
        """Get current simulation status"""
        response = self.make_request("/api/simulation/status")
        if response and response.status_code == 200:
            return response.json()
        return None
        
    def get_metrics(self):
        """Get current metrics"""
        response = self.make_request("/api/simulation/metrics")
        if response and response.status_code == 200:
            return response.json()
        return None
        
    def test_state_transitions(self):
        """Test state transitions and identify issues"""
        print("🔍 Testing State Transitions")
        print("=" * 40)
        
        # 1. Check initial state
        self.log("1. Checking initial state...")
        status = self.get_status()
        if status:
            self.log(f"   Initial status: {status.get('status', 'unknown')}")
        else:
            self.log("   ❌ Failed to get initial status")
            return
            
        # 2. Try to start simulation
        self.log("2. Attempting to start simulation...")
        response = self.make_request("/api/simulation/start", method="POST")
        if response:
            self.log(f"   Start response: {response.status_code}")
            if response.status_code == 200:
                self.log("   ✅ Start successful")
            else:
                self.log(f"   ❌ Start failed: {response.text}")
        else:
            self.log("   ❌ Start request failed")
            
        # 3. Check state after start attempt
        self.log("3. Checking state after start attempt...")
        status = self.get_status()
        if status:
            self.log(f"   Status after start: {status.get('status', 'unknown')}")
        else:
            self.log("   ❌ Failed to get status after start")
            
        # 4. Get metrics to see if simulation is running
        self.log("4. Getting metrics...")
        metrics = self.get_metrics()
        if metrics:
            self.log(f"   Metrics available: {len(metrics)} items")
            if 'chain_tension' in metrics:
                self.log(f"   Chain tension: {metrics['chain_tension']:.0f} N")
            if 'chain_speed' in metrics:
                self.log(f"   Chain speed: {metrics['chain_speed']:.2f} m/s")
        else:
            self.log("   ❌ Failed to get metrics")
            
        # 5. Try to pause
        self.log("5. Attempting to pause simulation...")
        response = self.make_request("/api/simulation/pause", method="POST")
        if response:
            self.log(f"   Pause response: {response.status_code}")
            if response.status_code == 200:
                self.log("   ✅ Pause successful")
            else:
                self.log(f"   ❌ Pause failed: {response.text}")
        else:
            self.log("   ❌ Pause request failed")
            
        # 6. Check state after pause
        self.log("6. Checking state after pause...")
        status = self.get_status()
        if status:
            self.log(f"   Status after pause: {status.get('status', 'unknown')}")
        else:
            self.log("   ❌ Failed to get status after pause")
            
        # 7. Try to resume
        self.log("7. Attempting to resume simulation...")
        response = self.make_request("/api/simulation/resume", method="POST")
        if response:
            self.log(f"   Resume response: {response.status_code}")
            if response.status_code == 200:
                self.log("   ✅ Resume successful")
            else:
                self.log(f"   ❌ Resume failed: {response.text}")
        else:
            self.log("   ❌ Resume request failed")
            
        # 8. Check state after resume
        self.log("8. Checking state after resume...")
        status = self.get_status()
        if status:
            self.log(f"   Status after resume: {status.get('status', 'unknown')}")
        else:
            self.log("   ❌ Failed to get status after resume")
            
        # 9. Try to reset
        self.log("9. Attempting to reset simulation...")
        response = self.make_request("/api/simulation/reset", method="POST")
        if response:
            self.log(f"   Reset response: {response.status_code}")
            if response.status_code == 200:
                self.log("   ✅ Reset successful")
            else:
                self.log(f"   ❌ Reset failed: {response.text}")
        else:
            self.log("   ❌ Reset request failed")
            
        # 10. Check final state
        self.log("10. Checking final state...")
        status = self.get_status()
        if status:
            self.log(f"   Final status: {status.get('status', 'unknown')}")
        else:
            self.log("   ❌ Failed to get final status")
            
    def test_rapid_commands(self):
        """Test rapid command sequences that might cause state issues"""
        print("\n⚡ Testing Rapid Commands")
        print("=" * 40)
        
        # Reset first
        self.log("Resetting simulation...")
        self.make_request("/api/simulation/reset", method="POST")
        time.sleep(1)
        
        # Rapid start commands
        self.log("Sending rapid start commands...")
        for i in range(5):
            response = self.make_request("/api/simulation/start", method="POST")
            self.log(f"   Start {i+1}: {response.status_code if response else 'Failed'}")
            time.sleep(0.1)  # Very rapid
            
        # Check state
        status = self.get_status()
        self.log(f"State after rapid starts: {status.get('status', 'unknown') if status else 'Failed'}")
        
        # Rapid pause commands
        self.log("Sending rapid pause commands...")
        for i in range(5):
            response = self.make_request("/api/simulation/pause", method="POST")
            self.log(f"   Pause {i+1}: {response.status_code if response else 'Failed'}")
            time.sleep(0.1)  # Very rapid
            
        # Check state
        status = self.get_status()
        self.log(f"State after rapid pauses: {status.get('status', 'unknown') if status else 'Failed'}")
        
    def test_error_recovery(self):
        """Test error recovery scenarios"""
        print("\n🔄 Testing Error Recovery")
        print("=" * 40)
        
        # 1. Try to start when already running
        self.log("1. Testing start when already running...")
        response = self.make_request("/api/simulation/start", method="POST")
        if response and response.status_code == 400:
            self.log("   ✅ Properly rejected duplicate start")
        else:
            self.log(f"   ❌ Unexpected response: {response.status_code if response else 'None'}")
            
        # 2. Try to pause when not running
        self.log("2. Testing pause when not running...")
        # First reset to ensure clean state
        self.make_request("/api/simulation/reset", method="POST")
        time.sleep(1)
        
        response = self.make_request("/api/simulation/pause", method="POST")
        if response and response.status_code == 400:
            self.log("   ✅ Properly rejected pause when not running")
        else:
            self.log(f"   ❌ Unexpected response: {response.status_code if response else 'None'}")
            
        # 3. Try to resume when not paused
        self.log("3. Testing resume when not paused...")
        response = self.make_request("/api/simulation/resume", method="POST")
        if response and response.status_code == 400:
            self.log("   ✅ Properly rejected resume when not paused")
        else:
            self.log(f"   ❌ Unexpected response: {response.status_code if response else 'None'}")
            
    def run_comprehensive_test(self):
        """Run comprehensive state management test"""
        print("🧪 State Management Test")
        print("=" * 50)
        
        try:
            self.test_state_transitions()
            self.test_rapid_commands()
            self.test_error_recovery()
            
            print("\n" + "=" * 50)
            print("📋 State Management Analysis")
            print("=" * 50)
            print("This test helps identify:")
            print("• State synchronization issues")
            print("• Race conditions in rapid commands")
            print("• Error handling for invalid state transitions")
            print("• Drivetrain state management problems")
            
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")

def main():
    """Main test runner"""
    tester = StateManagementTest()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main() 