#!/usr/bin/env python3
"""
Stage 4 Integration Test for KPP Simulator
Real-Time Data Integration Testing

Tests the enhanced SSE client, data validation, error handling,
and real-time UI updates with comprehensive error scenarios.
"""

import json
import time
import threading
import requests
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Stage4IntegrationTester:
    def __init__(self):
        self.base_url = 'http://localhost:5000'
        self.test_results = []
        self.errors = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        
        if not success:
            self.errors.append(result)
    
    def test_server_availability(self):
        """Test if the Flask server is running"""
        try:
            response = requests.get(f'{self.base_url}/', timeout=5)
            self.log_test(
                'server_availability',
                response.status_code == 200,
                f'Server responded with status {response.status_code}',
                {'response_time': response.elapsed.total_seconds()}
            )
            return response.status_code == 200
        except Exception as e:
            self.log_test(
                'server_availability',
                False,
                f'Server not accessible: {str(e)}'
            )
            return False
    
    def test_parameter_validation_api(self):
        """Test parameter validation on backend"""
        test_cases = [
            # Valid parameters
            {
                'name': 'valid_parameters',
                'params': {
                    'num_floaters': 10,
                    'air_pressure': 300000,
                    'h1_enabled': True
                },
                'should_succeed': True
            },
            # Invalid type
            {
                'name': 'invalid_type',
                'params': {
                    'num_floaters': 'invalid',
                    'air_pressure': 300000
                },
                'should_succeed': False
            },
            # Out of range
            {
                'name': 'out_of_range',
                'params': {
                    'num_floaters': -5,
                    'air_pressure': 300000
                },
                'should_succeed': False
            },
            # Missing required field (if any)
            {
                'name': 'empty_parameters',
                'params': {},
                'should_succeed': True  # Should use defaults
            }
        ]
        
        for case in test_cases:
            try:
                response = requests.patch(
                    f'{self.base_url}/set_params',
                    json=case['params'],
                    timeout=5
                )
                
                success = (response.status_code == 200) == case['should_succeed']
                
                self.log_test(
                    f'parameter_validation_{case["name"]}',
                    success,
                    f'Expected success: {case["should_succeed"]}, got status: {response.status_code}',
                    {
                        'request_params': case['params'],
                        'response_status': response.status_code,
                        'response_body': response.text[:200]
                    }
                )
                
            except Exception as e:
                self.log_test(
                    f'parameter_validation_{case["name"]}',
                    False,
                    f'Request failed: {str(e)}'
                )
    
    def test_sse_stream_availability(self):
        """Test SSE stream availability and data format"""
        try:
            import sseclient  # pip install sseclient-py
            
            response = requests.get(f'{self.base_url}/stream', stream=True, timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    'sse_stream_availability',
                    False,
                    f'SSE stream returned status {response.status_code}'
                )
                return
            
            # Test data reception - use direct response iteration for better compatibility
            # SSEClient type hints might be incorrect, so we'll use type: ignore
            client = sseclient.SSEClient(response)  # type: ignore
            data_received = []
            start_time = time.time()
            
            for event in client.events():
                if time.time() - start_time > 5:  # Test for 5 seconds
                    break
                
                try:
                    data = json.loads(event.data)
                    data_received.append(data)
                except json.JSONDecodeError:
                    self.log_test(
                        'sse_data_format',
                        False,
                        f'Invalid JSON in SSE stream: {event.data[:100]}'
                    )
                    return
            
            if len(data_received) > 0:
                self.log_test(
                    'sse_stream_availability',
                    True,
                    f'SSE stream working, received {len(data_received)} messages',
                    {'sample_data': data_received[0] if data_received else None}
                )
                
                # Test data structure
                self.test_sse_data_structure(data_received[0] if data_received else {})
            else:
                self.log_test(
                    'sse_stream_availability',
                    False,
                    'No data received from SSE stream'
                )
                
        except ImportError:
            print("⚠️ Warning: sseclient-py not installed, skipping SSE stream test")
            print("   Install with: pip install sseclient-py")
        except Exception as e:
            self.log_test(
                'sse_stream_availability',
                False,
                f'SSE stream test failed: {str(e)}'
            )
    
    def test_sse_data_structure(self, sample_data):
        """Test the structure of SSE data"""
        expected_fields = ['time', 'power', 'torque']
        optional_fields = ['efficiency', 'floaters', 'physics_status', 'system_status', 'heartbeat']
        
        # Check required fields
        missing_required = [field for field in expected_fields if field not in sample_data and 'heartbeat' not in sample_data]
        
        if missing_required:
            self.log_test(
                'sse_data_structure',
                False,
                f'Missing required fields: {missing_required}',
                {'sample_data': sample_data}
            )
        else:
            self.log_test(
                'sse_data_structure',
                True,
                'SSE data structure is valid',
                {
                    'present_fields': list(sample_data.keys()),
                    'data_types': {k: type(v).__name__ for k, v in sample_data.items()}
                }
            )
    
    def test_simulation_control_endpoints(self):
        """Test simulation control endpoints"""
        endpoints = [
            ('start', 'POST'),
            ('pause', 'POST'),
            ('stop', 'POST'),
            ('reset', 'POST'),
            ('step', 'POST'),
            ('pulse', 'POST')
        ]
        
        for endpoint, method in endpoints:
            try:
                response = requests.request(
                    method,
                    f'{self.base_url}/{endpoint}',
                    json={},
                    timeout=5
                )
                
                # Accept both 200 and 202 as success for control endpoints
                success = response.status_code in [200, 202]
                
                self.log_test(
                    f'simulation_control_{endpoint}',
                    success,
                    f'{method} /{endpoint} returned status {response.status_code}',
                    {'response_time': response.elapsed.total_seconds()}
                )
                
            except Exception as e:
                self.log_test(
                    f'simulation_control_{endpoint}',
                    False,
                    f'Control endpoint failed: {str(e)}'
                )
    
    def test_frontend_files_accessibility(self):
        """Test that all frontend files are accessible"""
        frontend_files = [
            '/static/js/error-handler.js',
            '/static/js/realtime-data-manager.js',
            '/static/js/parameter-manager.js',
            '/static/js/chart-manager.js',
            '/static/js/floater-table.js',
            '/static/js/enhanced-main.js',
            '/static/css/physics-styles.css',
            '/static/css/style.css'
        ]
        
        for file_path in frontend_files:
            try:
                response = requests.get(f'{self.base_url}{file_path}', timeout=5)
                
                success = response.status_code == 200
                
                self.log_test(
                    f'frontend_file_{file_path.split("/")[-1]}',
                    success,
                    f'File accessible: {file_path}' if success else f'File not found: {file_path}',
                    {
                        'status_code': response.status_code,
                        'content_length': len(response.content),
                        'content_type': response.headers.get('content-type', 'unknown')
                    }
                )
                
            except Exception as e:
                self.log_test(
                    f'frontend_file_{file_path.split("/")[-1]}',
                    False,
                    f'Failed to access {file_path}: {str(e)}'
                )
    
    def test_error_scenarios(self):
        """Test error handling scenarios"""
        # Test invalid endpoint
        try:
            response = requests.get(f'{self.base_url}/invalid_endpoint', timeout=5)
            self.log_test(
                'error_handling_404',
                response.status_code == 404,
                f'Invalid endpoint correctly returned 404 (got {response.status_code})'
            )
        except Exception as e:
            self.log_test(
                'error_handling_404',
                False,
                f'Error testing invalid endpoint: {str(e)}'
            )
        
        # Test malformed JSON
        try:
            response = requests.patch(
                f'{self.base_url}/set_params',
                data='invalid json',
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            self.log_test(
                'error_handling_malformed_json',
                response.status_code >= 400,
                f'Malformed JSON correctly rejected (status {response.status_code})'
            )
        except Exception as e:
            self.log_test(
                'error_handling_malformed_json',
                False,
                f'Error testing malformed JSON: {str(e)}'
            )
    
    def run_performance_test(self):
        """Test system performance under load"""
        print("\\n🚀 Running performance tests...")
        
        # Test parameter update performance
        start_time = time.time()
        successful_requests = 0
        
        for i in range(10):
            try:
                response = requests.patch(
                    f'{self.base_url}/set_params',
                    json={'num_floaters': 5 + i},
                    timeout=2
                )
                if response.status_code == 200:
                    successful_requests += 1
            except:
                pass
        
        elapsed = time.time() - start_time
        requests_per_second = successful_requests / elapsed if elapsed > 0 else 0
        
        self.log_test(
            'performance_parameter_updates',
            requests_per_second > 5,  # At least 5 requests per second
            f'Parameter updates: {requests_per_second:.2f} req/sec',
            {
                'successful_requests': successful_requests,
                'elapsed_time': elapsed,
                'requests_per_second': requests_per_second
            }
        )
    
    def generate_report(self):
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"\\n" + "="*60)
        print(f"🧪 STAGE 4 INTEGRATION TEST REPORT")
        print(f"="*60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.errors:
            print(f"\\n🚨 FAILED TESTS:")
            for error in self.errors:
                print(f"   - {error['test']}: {error['message']}")
        
        print(f"\\n📊 Test Details:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['test']}: {result['message']}")
        
        # Save detailed report
        report_data = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': (passed_tests/total_tests)*100,
                'timestamp': datetime.now().isoformat()
            },
            'test_results': self.test_results,
            'errors': self.errors
        }
        
        with open('stage4_test_results.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\\n📁 Detailed report saved to: stage4_test_results.json")
        
        return failed_tests == 0
    
    def run_all_tests(self):
        """Run all Stage 4 integration tests"""
        print("🧪 Starting Stage 4 Integration Tests...")
        print("Testing: Enhanced SSE, Data Validation, Error Handling\\n")
        
        # Basic connectivity
        if not self.test_server_availability():
            print("❌ Server not available, skipping remaining tests")
            return self.generate_report()
        
        # Core functionality tests
        self.test_parameter_validation_api()
        self.test_sse_stream_availability()
        self.test_simulation_control_endpoints()
        self.test_frontend_files_accessibility()
        self.test_error_scenarios()
        
        # Performance tests
        self.run_performance_test()
        
        # Generate report
        return self.generate_report()

def main():
    """Main test execution"""
    tester = Stage4IntegrationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\\n🎉 All Stage 4 tests passed! Real-time data integration is working correctly.")
        sys.exit(0)
    else:
        print("\\n❌ Some Stage 4 tests failed. Please check the issues above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
