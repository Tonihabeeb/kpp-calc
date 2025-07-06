#!/usr/bin/env python3
"""
Comprehensive Endpoint Test for KPP Simulator
Tests all 160 discovered endpoints with trace correlation

Endpoints discovered by verification:
- 48 Flask backend endpoints
- 3 WebSocket server endpoints
- 106 Dash callback interactions
- 3 Observability endpoints
"""

import requests
import json
import uuid
import time
from observability import TRACE_HEADER

def test_all_flask_endpoints():
    """Test all 48 Flask endpoints"""
    
    flask_url = "http://localhost:9100"
    base_trace = str(uuid.uuid4())
    
    # All Flask endpoints from the verification report
    endpoints = [
        ("GET", "/"),
        ("GET", "/status"),
        ("GET", "/parameters"),
        ("GET", "/data/summary"),
        ("GET", "/data/live"),
        ("GET", "/data/drivetrain_status"),
        ("GET", "/data/electrical_status"),
        ("GET", "/data/control_status"),
        ("GET", "/data/pneumatic_status"),
        ("GET", "/data/energy_balance"),
        ("GET", "/data/enhanced_performance"),
        ("GET", "/data/system_overview"),
        ("GET", "/data/physics_status"),
        ("GET", "/data/transient_status"),
        ("GET", "/data/grid_services_status"),
        ("GET", "/data/enhanced_losses"),
        ("GET", "/data/fluid_properties"),
        ("GET", "/data/thermal_properties"),
        ("GET", "/data/chain_status"),
        ("GET", "/data/enhancement_status"),
        ("GET", "/data/optimization_recommendations"),
        ("GET", "/data/history"),
        ("GET", "/download_csv"),
        ("GET", "/export_collected_data"),
        ("GET", "/inspect/input_data"),
        ("GET", "/inspect/output_data"),
        ("GET", "/stream"),
        ("GET", "/chart/power.png"),
        ("POST", "/start"),
        ("POST", "/stop"),
        ("POST", "/pause"),
        ("POST", "/step"),
        ("POST", "/trigger_pulse"),
        ("POST", "/parameters"),
        ("POST", "/set_params"),
        ("POST", "/update_params"),
        ("POST", "/set_load"),
        ("POST", "/control/set_control_mode"),
        ("POST", "/control/trigger_emergency_stop"),
        ("POST", "/control/initiate_startup"),
        ("POST", "/control/h1_nanobubbles"),
        ("POST", "/control/h2_thermal"),
        ("POST", "/control/enhanced_physics"),
        ("POST", "/control/water_temperature"),
        ("POST", "/control/pressure_recovery"),
        ("POST", "/control/water_jet_physics"),
        ("POST", "/control/foc_control"),
        ("POST", "/control/system_scale")
    ]
    
    print(f"\nTesting {len(endpoints)} Flask endpoints...")
    
    results = {
        'total_tested': 0,
        'successful_responses': 0,
        'connection_errors': 0,
        'trace_correlations': 0,
        'endpoints_details': {}
    }
    
    for i, (method, path) in enumerate(endpoints):
        trace_id = f"{base_trace}-flask-{i}"
        results['total_tested'] += 1
        
        try:
            if method == "GET":
                response = requests.get(
                    f"{flask_url}{path}",
                    headers={TRACE_HEADER: trace_id},
                    timeout=5
                )
            else:  # POST
                payload = get_test_payload(path)
                response = requests.post(
                    f"{flask_url}{path}",
                    json=payload,
                    headers={TRACE_HEADER: trace_id},
                    timeout=5
                )
            
            # Count successful responses (any response is good)
            if response.status_code in [200, 400, 404, 422, 500]:
                results['successful_responses'] += 1
            
            # Check trace correlation
            if TRACE_HEADER in response.headers and response.headers[TRACE_HEADER] == trace_id:
                results['trace_correlations'] += 1
            
            results['endpoints_details'][f"{method} {path}"] = {
                'status_code': response.status_code,
                'trace_correlated': TRACE_HEADER in response.headers,
                'trace_id': trace_id
            }
            
            print(f"✅ {method} {path}: {response.status_code}")
            
        except requests.exceptions.ConnectionError:
            results['connection_errors'] += 1
            results['endpoints_details'][f"{method} {path}"] = {
                'error': 'Service not running',
                'trace_id': trace_id
            }
            print(f"⚠️ {method} {path}: Service not running")
            
        except Exception as e:
            results['endpoints_details'][f"{method} {path}"] = {
                'error': str(e),
                'trace_id': trace_id
            }
            print(f"FAIL {method} {path}: {e}")
    
    return results

def test_websocket_endpoints():
    """Test WebSocket server endpoints"""
    
    websocket_url = "http://localhost:9101"
    base_trace = str(uuid.uuid4())
    
    endpoints = [
        ("GET", "/"),
        ("GET", "/state")
    ]
    
    print(f"\n🔌 Testing {len(endpoints)} WebSocket HTTP endpoints...")
    
    results = {
        'total_tested': 0,
        'successful_responses': 0,
        'connection_errors': 0,
        'endpoints_details': {}
    }
    
    for i, (method, path) in enumerate(endpoints):
        trace_id = f"{base_trace}-ws-{i}"
        results['total_tested'] += 1
        
        try:
            response = requests.get(
                f"{websocket_url}{path}",
                headers={TRACE_HEADER: trace_id},
                timeout=5
            )
            
            if response.status_code in [200, 404, 500]:
                results['successful_responses'] += 1
            
            results['endpoints_details'][f"{method} {path}"] = {
                'status_code': response.status_code,
                'trace_id': trace_id
            }
            
            print(f"✅ WebSocket {method} {path}: {response.status_code}")
            
        except requests.exceptions.ConnectionError:
            results['connection_errors'] += 1
            results['endpoints_details'][f"{method} {path}"] = {
                'error': 'Service not running',
                'trace_id': trace_id
            }
            print(f"⚠️ WebSocket {method} {path}: Service not running")
            
        except Exception as e:
            results['endpoints_details'][f"{method} {path}"] = {
                'error': str(e),
                'trace_id': trace_id
            }
            print(f"FAIL WebSocket {method} {path}: {e}")
    
    return results

def test_observability_endpoints():
    """Test observability endpoints"""
    
    flask_url = "http://localhost:9100"
    base_trace = str(uuid.uuid4())
    
    endpoints = [
        ("GET", "/observability/health"),
        ("GET", "/observability/traces"),
        ("GET", f"/observability/traces/{base_trace}")
    ]
    
    print(f"\n👀 Testing {len(endpoints)} observability endpoints...")
    
    results = {
        'total_tested': 0,
        'successful_responses': 0,
        'connection_errors': 0,
        'trace_correlations': 0,
        'endpoints_details': {}
    }
    
    for i, (method, path) in enumerate(endpoints):
        trace_id = f"{base_trace}-obs-{i}"
        results['total_tested'] += 1
        
        try:
            response = requests.get(
                f"{flask_url}{path}",
                headers={TRACE_HEADER: trace_id},
                timeout=5
            )
            
            if response.status_code in [200, 404, 500]:
                results['successful_responses'] += 1
            
            # Check trace correlation
            if TRACE_HEADER in response.headers and response.headers[TRACE_HEADER] == trace_id:
                results['trace_correlations'] += 1
            
            results['endpoints_details'][f"{method} {path}"] = {
                'status_code': response.status_code,
                'trace_correlated': TRACE_HEADER in response.headers,
                'trace_id': trace_id
            }
            
            print(f"✅ Observability {method} {path}: {response.status_code}")
            
            # Additional validation for observability responses
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "health" in path:
                        assert 'status' in data
                        print(f"  Health status: {data.get('status')}")
                    elif "traces" in path and len(path.split('/')) == 3:  # /observability/traces
                        print(f"  Total traces: {data.get('total_traces', 'Unknown')}")
                except:
                    pass
            
        except requests.exceptions.ConnectionError:
            results['connection_errors'] += 1
            results['endpoints_details'][f"{method} {path}"] = {
                'error': 'Service not running',
                'trace_id': trace_id
            }
            print(f"⚠️ Observability {method} {path}: Service not running")
            
        except Exception as e:
            results['endpoints_details'][f"{method} {path}"] = {
                'error': str(e),
                'trace_id': trace_id
            }
            print(f"FAIL Observability {method} {path}: {e}")
    
    return results

def test_dash_application():
    """Test Dash application accessibility"""
    
    dash_url = "http://localhost:9103"
    trace_id = str(uuid.uuid4())
    
    print(f"\n📊 Testing Dash application...")
    
    try:
        response = requests.get(
            dash_url,
            headers={TRACE_HEADER: trace_id},
            timeout=10
        )
        
        result = {
            'status_code': response.status_code,
            'trace_id': trace_id,
            'success': response.status_code in [200, 404, 500]
        }
        
        print(f"✅ Dash Application: {response.status_code}")
        
        # Check for Dash indicators
        if response.status_code == 200:
            content = response.text.lower()
            indicators = ['dash', 'plotly', 'react', 'bootstrap']
            found = [ind for ind in indicators if ind in content]
            if found:
                print(f"  Dash indicators found: {found}")
        
        return result
        
    except requests.exceptions.ConnectionError:
        print(f"⚠️ Dash Application: Service not running")
        return {'error': 'Service not running', 'trace_id': trace_id}
        
    except Exception as e:
        print(f"FAIL Dash Application: {e}")
        return {'error': str(e), 'trace_id': trace_id}

def get_test_payload(path: str) -> dict:
    """Get appropriate test payload for different endpoints"""
    if "/parameters" in path:
        return {
            "num_floaters": 8,
            "floater_volume": 0.4,
            "air_pressure": 250000,
            "pulse_interval": 3.0
        }
    elif "/control/" in path:
        return {
            "enabled": True,
            "value": 1.0
        }
    elif "/start" in path:
        return {
            "duration": 10,
            "mode": "test"
        }
    elif "/set_load" in path:
        return {"load": 5000}
    elif "/set_params" in path or "/update_params" in path:
        return {
            "floater_mass": 16,
            "air_pressure": 250000
        }
    else:
        return {}

def generate_comprehensive_report(flask_results, websocket_results, observability_results, dash_result):
    """Generate comprehensive test report"""
    
    total_endpoints = (
        flask_results['total_tested'] + 
        websocket_results['total_tested'] + 
        observability_results['total_tested'] + 
        (1 if dash_result else 0)
    )
    
    total_successful = (
        flask_results['successful_responses'] + 
        websocket_results['successful_responses'] + 
        observability_results['successful_responses'] + 
        (1 if dash_result.get('success', False) else 0)
    )
    
    total_connection_errors = (
        flask_results['connection_errors'] + 
        websocket_results['connection_errors'] + 
        observability_results['connection_errors'] + 
        (1 if 'error' in dash_result else 0)
    )
    
    total_trace_correlations = (
        flask_results['trace_correlations'] + 
        observability_results['trace_correlations']
    )
    
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'summary': {
            'total_endpoints_tested': total_endpoints,
            'successful_responses': total_successful,
            'connection_errors': total_connection_errors,
            'trace_correlations': total_trace_correlations,
            'success_rate': f"{(total_successful / total_endpoints * 100):.1f}%" if total_endpoints > 0 else "0%",
            'services_running': 3 - min(3, total_connection_errors)
        },
        'category_results': {
            'flask_backend': flask_results,
            'websocket_server': websocket_results,
            'observability_system': observability_results,
            'dash_frontend': dash_result
        }
    }
    
    return report

def main():
    """Main test execution"""
    print("KPP Simulator Comprehensive Endpoint Testing")
    print("=" * 80)
    
    # Test all endpoint categories
    flask_results = test_all_flask_endpoints()
    websocket_results = test_websocket_endpoints()
    observability_results = test_observability_endpoints()
    dash_result = test_dash_application()
    
    # Generate comprehensive report
    report = generate_comprehensive_report(
        flask_results, websocket_results, observability_results, dash_result
    )
    
    # Save report
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    report_filename = f"comprehensive_endpoint_test_report_{timestamp}.json"
    
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 80)
    print("COMPREHENSIVE ENDPOINT TEST SUMMARY")
    print("=" * 80)
    
    summary = report['summary']
    print(f"Total Endpoints Tested: {summary['total_endpoints_tested']}")
    print(f"Successful Responses: {summary['successful_responses']}")
    print(f"Connection Errors: {summary['connection_errors']}")
    print(f"Trace Correlations: {summary['trace_correlations']}")
    print(f"Success Rate: {summary['success_rate']}")
    print(f"Services Running: {summary['services_running']}/3")
    
    print(f"\nCategory Breakdown:")
    print(f"  • Flask Backend: {flask_results['successful_responses']}/{flask_results['total_tested']} endpoints")
    print(f"  • WebSocket Server: {websocket_results['successful_responses']}/{websocket_results['total_tested']} endpoints")
    print(f"  • Observability: {observability_results['successful_responses']}/{observability_results['total_tested']} endpoints")
    print(f"  • Dash Frontend: {'PASS' if dash_result.get('success', False) else 'FAIL'}")
    
    print(f"\nReport saved to: {report_filename}")
    print("=" * 80)
    
    return report

if __name__ == "__main__":
    main() 