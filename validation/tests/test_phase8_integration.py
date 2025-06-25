#!/usr/bin/env python3
"""
Phase 8 Integration Test Script
Tests that all advanced systems are properly integrated and providing data.
"""

import requests
import time
import json
import sys
from typing import Dict, List

class Phase8IntegrationTester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []
        
    def run_comprehensive_test(self):
        """Run comprehensive integration test"""
        print("🧪 PHASE 8 COMPREHENSIVE INTEGRATION TEST")
        print("=" * 60)
        
        # Test 1: Start simulation
        if not self._test_simulation_start():
            print("❌ Failed to start simulation - aborting tests")
            return False
            
        # Wait for systems to initialize
        print("⏳ Waiting for systems to initialize...")
        time.sleep(5)
        
        # Test 2: Core endpoints
        if not self._test_core_endpoints():
            print("❌ Core endpoints test failed")
            return False
            
        # Test 3: Advanced system endpoints
        if not self._test_advanced_system_endpoints():
            print("❌ Advanced system endpoints test failed")
            return False
            
        # Test 4: Data quality validation
        if not self._test_data_quality():
            print("❌ Data quality validation failed")
            return False
            
        # Test 5: System integration validation
        if not self._test_system_integration():
            print("❌ System integration validation failed")
            return False
            
        # Test 6: Control system functionality
        if not self._test_control_functionality():
            print("❌ Control system functionality test failed")
            return False
            
        # Stop simulation
        self._stop_simulation()
        
        # Print results
        self._print_test_results()
        
        return all(result['passed'] for result in self.test_results)
    
    def _test_simulation_start(self) -> bool:
        """Test simulation startup"""
        print("1. Testing simulation startup...")
        try:
            response = requests.post(f"{self.base_url}/start", json={}, timeout=10)
            success = response.status_code == 200
            self._add_result("Simulation Start", success, "Simulation started successfully" if success else f"Failed with status {response.status_code}")
            return success
        except Exception as e:
            self._add_result("Simulation Start", False, f"Exception: {e}")
            return False
    
    def _test_core_endpoints(self) -> bool:
        """Test core simulation endpoints"""
        print("2. Testing core endpoints...")
        
        endpoints = [
            "/data/summary",
            "/data/history",
            "/data/pneumatic_status"
        ]
        
        all_passed = True
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                success = response.status_code == 200
                self._add_result(f"Core Endpoint {endpoint}", success, 
                               "OK" if success else f"Status {response.status_code}")
                if not success:
                    all_passed = False
            except Exception as e:
                self._add_result(f"Core Endpoint {endpoint}", False, f"Exception: {e}")
                all_passed = False
        
        return all_passed
    
    def _test_advanced_system_endpoints(self) -> bool:
        """Test all new integrated system endpoints"""
        print("3. Testing advanced system endpoints...")
        
        advanced_endpoints = [
            "/data/drivetrain_status",
            "/data/electrical_status", 
            "/data/control_status",
            "/data/grid_services_status",
            "/data/enhanced_losses",
            "/data/system_overview"
        ]
        
        all_passed = True
        for endpoint in advanced_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                success = response.status_code == 200
                
                if success:
                    data = response.json()
                    has_data = data and len(data) > 0
                    self._add_result(f"Advanced Endpoint {endpoint}", has_data, 
                                   f"Data received: {len(data)} fields" if has_data else "No data returned")
                    if not has_data:
                        all_passed = False
                else:
                    self._add_result(f"Advanced Endpoint {endpoint}", False, f"Status {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                self._add_result(f"Advanced Endpoint {endpoint}", False, f"Exception: {e}")
                all_passed = False
        
        return all_passed
    
    def _test_data_quality(self) -> bool:
        """Test data quality and realism"""
        print("4. Testing data quality and realism...")
        
        try:
            # Get drivetrain data
            response = requests.get(f"{self.base_url}/data/drivetrain_status", timeout=5)
            if response.status_code != 200:
                self._add_result("Data Quality - Drivetrain", False, "Could not fetch drivetrain data")
                return False
                
            drivetrain_data = response.json()
            
            # Validate drivetrain data ranges
            flywheel_rpm = drivetrain_data.get('flywheel_speed_rpm', 0)
            system_efficiency = drivetrain_data.get('system_efficiency', 0)
            chain_tension = drivetrain_data.get('chain_tension', 0)
            
            # Check realistic ranges
            flywheel_valid = 0 <= flywheel_rpm <= 1000  # 0-1000 RPM
            efficiency_valid = 0 <= system_efficiency <= 1.0  # 0-100%
            tension_valid = -10000 <= chain_tension <= 10000  # Reasonable tension range
            
            quality_passed = flywheel_valid and efficiency_valid and tension_valid
            
            self._add_result("Data Quality - Drivetrain", quality_passed,
                           f"Flywheel: {flywheel_rpm:.1f} RPM, Efficiency: {system_efficiency:.3f}, Tension: {chain_tension:.1f} N")
            
            # Get electrical data
            response = requests.get(f"{self.base_url}/data/electrical_status", timeout=5)
            if response.status_code == 200:
                electrical_data = response.json()
                grid_power = electrical_data.get('grid_power_output', 0)
                grid_voltage = electrical_data.get('grid_voltage', 0)
                grid_frequency = electrical_data.get('grid_frequency', 0)
                
                # Check electrical data ranges
                power_valid = -1000000 <= grid_power <= 1000000  # ±1MW range
                voltage_valid = 100 <= grid_voltage <= 1000  # 100-1000V range
                frequency_valid = 50 <= grid_frequency <= 70  # 50-70Hz range
                
                electrical_quality = power_valid and voltage_valid and frequency_valid
                
                self._add_result("Data Quality - Electrical", electrical_quality,
                               f"Power: {grid_power/1000:.1f} kW, Voltage: {grid_voltage:.1f} V, Frequency: {grid_frequency:.1f} Hz")
                
                quality_passed = quality_passed and electrical_quality
            
            return quality_passed
            
        except Exception as e:
            self._add_result("Data Quality Test", False, f"Exception: {e}")
            return False
    
    def _test_system_integration(self) -> bool:
        """Test that systems are properly integrated"""
        print("5. Testing system integration...")
        
        try:
            # Get system overview to see if all systems are reporting
            response = requests.get(f"{self.base_url}/data/system_overview", timeout=5)
            if response.status_code != 200:
                self._add_result("System Integration", False, "Could not fetch system overview")
                return False
            
            overview_data = response.json()
            
            # Check that major system sections exist
            required_sections = [
                'system_status',
                'power_generation', 
                'mechanical_systems',
                'control_systems'
            ]
            
            sections_present = all(section in overview_data for section in required_sections)
            
            self._add_result("System Integration - Overview Structure", sections_present,
                           f"Required sections present: {sections_present}")
            
            # Check for data consistency across systems
            # Compare power values between different endpoints
            drivetrain_response = requests.get(f"{self.base_url}/data/drivetrain_status", timeout=5)
            electrical_response = requests.get(f"{self.base_url}/data/electrical_status", timeout=5)
            
            if drivetrain_response.status_code == 200 and electrical_response.status_code == 200:
                drivetrain_data = drivetrain_response.json()
                electrical_data = electrical_response.json()
                
                # Check that power values are consistent
                mechanical_power = drivetrain_data.get('power_flow', {}).get('output_power', 0)
                electrical_power = electrical_data.get('grid_power_output', 0)
                
                # Allow for some difference due to system losses
                power_consistency = abs(mechanical_power - electrical_power) < max(abs(mechanical_power) * 0.5, 1000)
                
                self._add_result("System Integration - Power Consistency", power_consistency,
                               f"Mechanical: {mechanical_power/1000:.1f} kW, Electrical: {electrical_power/1000:.1f} kW")
            
            return sections_present
            
        except Exception as e:
            self._add_result("System Integration Test", False, f"Exception: {e}")
            return False
    
    def _test_control_functionality(self) -> bool:
        """Test control system functionality"""
        print("6. Testing control functionality...")
        
        try:
            # Test control status endpoint
            response = requests.get(f"{self.base_url}/data/control_status", timeout=5)
            if response.status_code != 200:
                self._add_result("Control Functionality", False, "Could not fetch control status")
                return False
            
            control_data = response.json()
            
            # Check that control system is responding
            control_mode = control_data.get('control_mode', 'unknown')
            system_health = control_data.get('system_health', 0)
            
            control_active = control_mode != 'unknown' and system_health > 0
            
            self._add_result("Control Functionality - Status", control_active,
                           f"Mode: {control_mode}, Health: {system_health:.2f}")
            
            # Test transient status endpoint
            response = requests.get(f"{self.base_url}/data/transient_status", timeout=5)
            transient_available = response.status_code == 200
            
            self._add_result("Control Functionality - Transient Controller", transient_available,
                           "Transient controller accessible" if transient_available else "Transient controller not available")
            
            return control_active
            
        except Exception as e:
            self._add_result("Control Functionality Test", False, f"Exception: {e}")
            return False
    
    def _stop_simulation(self):
        """Stop the simulation"""
        try:
            requests.post(f"{self.base_url}/stop", timeout=5)
        except:
            pass
    
    def _add_result(self, test_name: str, passed: bool, details: str):
        """Add test result"""
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name} - {details}")
    
    def _print_test_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        total_tests = len(self.test_results)
        
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Phase 8 integration is successful!")
            print("\nKey achievements:")
            print("✅ Advanced drivetrain system fully operational")
            print("✅ Integrated electrical system providing grid power")
            print("✅ Control systems managing simulation parameters")
            print("✅ Grid services coordinator active")
            print("✅ Enhanced loss modeling providing detailed analysis")
            print("✅ System overview dashboard operational")
            print("✅ All API endpoints responding with valid data")
            print("✅ Data quality validation passed")
            print("✅ System integration validation passed")
        else:
            print("\n⚠️  SOME TESTS FAILED - Phase 8 integration needs attention")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"❌ {result['test']}: {result['details']}")

def main():
    """Main test execution"""
    print("Starting Phase 8 Integration Test...")
    print("Make sure the simulation server is running on http://localhost:5000")
    print()
    
    tester = Phase8IntegrationTester()
    success = tester.run_comprehensive_test()
    
    print(f"\n{'='*60}")
    if success:
        print("🎊 PHASE 8 INTEGRATION TEST: COMPLETE SUCCESS!")
        print("The KPP simulation has been successfully upgraded with all advanced systems.")
        return 0
    else:
        print("💥 PHASE 8 INTEGRATION TEST: FAILED")
        print("Some systems are not properly integrated. Check the detailed results above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
