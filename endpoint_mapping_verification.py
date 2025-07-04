#!/usr/bin/env python3
"""
KPP Simulator Endpoint Mapping Verification
Comprehensive validation that all endpoints from both sides are well mapped

This tool:
1. Extracts all actual endpoints from the codebase
2. Validates reverse integration test coverage
3. Performs live endpoint verification
4. Generates comprehensive mapping reports
"""

import re
import json
import requests
import time
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)

class EndpointExtractor:
    """Extract endpoints from codebase files"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent
        self.endpoints = {
            'flask_routes': set(),
            'websocket_routes': set(),
            'dash_callbacks': set(),
            'observability_routes': set()
        }
        
    def extract_flask_routes(self):
        """Extract Flask routes from app.py"""
        flask_file = self.base_dir / "app.py"
        
        if not flask_file.exists():
            logger.warning("app.py not found")
            return
            
        with open(flask_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match @app.route decorators
        route_pattern = r'@app\.route\(["\']([^"\']+)["\'](?:,\s*methods=\[([^\]]+)\])?\)'
        matches = re.findall(route_pattern, content)
        
        for route, methods in matches:
            methods_list = []
            if methods:
                # Extract methods from the methods array
                method_pattern = r'["\']([^"\']+)["\']'
                methods_list = re.findall(method_pattern, methods)
            else:
                methods_list = ['GET']  # Default method
            
            for method in methods_list:
                endpoint = f"{method} {route}"
                self.endpoints['flask_routes'].add(endpoint)
        
        logger.info(f"Extracted {len(self.endpoints['flask_routes'])} Flask routes")
    
    def extract_websocket_routes(self):
        """Extract WebSocket routes from main.py"""
        websocket_file = self.base_dir / "main.py"
        
        if not websocket_file.exists():
            logger.warning("main.py not found")
            return
            
        with open(websocket_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match FastAPI WebSocket and HTTP routes
        ws_pattern = r'@app\.websocket\(["\']([^"\']+)["\']\)'
        http_pattern = r'@app\.(get|post|put|delete)\(["\']([^"\']+)["\']\)'
        
        # WebSocket routes
        ws_matches = re.findall(ws_pattern, content)
        for route in ws_matches:
            endpoint = f"WEBSOCKET {route}"
            self.endpoints['websocket_routes'].add(endpoint)
        
        # HTTP routes in FastAPI
        http_matches = re.findall(http_pattern, content)
        for method, route in http_matches:
            endpoint = f"{method.upper()} {route}"
            self.endpoints['websocket_routes'].add(endpoint)
        
        logger.info(f"Extracted {len(self.endpoints['websocket_routes'])} WebSocket/FastAPI routes")
    
    def extract_dash_callbacks(self):
        """Extract Dash callbacks from dash_app.py"""
        dash_file = self.base_dir / "dash_app.py"
        
        if not dash_file.exists():
            logger.warning("dash_app.py not found")
            return
            
        with open(dash_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match @app.callback or @callback decorators
        callback_pattern = r'@(?:app\.)?callback\('
        # Pattern to match Output, Input, State components
        output_pattern = r'Output\(["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\)'
        input_pattern = r'Input\(["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\)'
        
        # Find all callback definitions
        callback_matches = re.finditer(callback_pattern, content)
        callback_count = 0
        
        for match in callback_matches:
            callback_count += 1
            # Extract the callback definition section
            start_pos = match.start()
            # Find the function definition after the callback
            func_pattern = r'def\s+(\w+)\s*\('
            func_match = re.search(func_pattern, content[start_pos:start_pos+2000])
            
            if func_match:
                func_name = func_match.group(1)
                callback_info = f"CALLBACK {func_name}"
                self.endpoints['dash_callbacks'].add(callback_info)
        
        # Also extract component IDs that are referenced
        outputs = re.findall(output_pattern, content)
        inputs = re.findall(input_pattern, content)
        
        # Store component interactions
        for component_id, property_name in outputs + inputs:
            component_info = f"COMPONENT {component_id}.{property_name}"
            self.endpoints['dash_callbacks'].add(component_info)
        
        logger.info(f"Extracted {len(self.endpoints['dash_callbacks'])} Dash callback interactions")
    
    def extract_observability_routes(self):
        """Extract observability routes from observability.py"""
        obs_file = self.base_dir / "observability.py"
        
        if not obs_file.exists():
            logger.warning("observability.py not found")
            return
            
        with open(obs_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match flask_app.route decorators in observability
        route_pattern = r'@flask_app\.route\(["\']([^"\']+)["\'](?:,\s*methods=\[([^\]]+)\])?\)'
        matches = re.findall(route_pattern, content)
        
        for route, methods in matches:
            methods_list = []
            if methods:
                method_pattern = r'["\']([^"\']+)["\']'
                methods_list = re.findall(method_pattern, methods)
            else:
                methods_list = ['GET']
            
            for method in methods_list:
                endpoint = f"{method} {route}"
                self.endpoints['observability_routes'].add(endpoint)
        
        logger.info(f"Extracted {len(self.endpoints['observability_routes'])} observability routes")
    
    def extract_all_endpoints(self):
        """Extract all endpoints from all sources"""
        logger.info("Starting endpoint extraction...")
        
        self.extract_flask_routes()
        self.extract_websocket_routes()
        self.extract_dash_callbacks()
        self.extract_observability_routes()
        
        total_endpoints = sum(len(routes) for routes in self.endpoints.values())
        logger.info(f"Total endpoints extracted: {total_endpoints}")
        
        return self.endpoints

class TestCoverageAnalyzer:
    """Analyze test coverage of endpoints in reverse integration tests"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent
        self.tested_endpoints = set()
        
    def extract_tested_endpoints(self):
        """Extract endpoints that are tested in reverse integration tests"""
        test_file = self.base_dir / "tests" / "test_reverse_integration.py"
        
        if not test_file.exists():
            logger.warning("test_reverse_integration.py not found")
            return set()
            
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        coverage_by_type = {
            'flask_routes': 0,
            'websocket_routes': 0,
            'dash_callbacks': 0,
            'observability_routes': 0
        }
        
        # Extract Flask GET endpoints from test
        get_endpoints_match = re.search(r'get_endpoints\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if get_endpoints_match:
            endpoints = re.findall(r'["\']([^"\']+)["\']', get_endpoints_match.group(1))
            for endpoint in endpoints:
                self.tested_endpoints.add(f"GET {endpoint}")
                coverage_by_type['flask_routes'] += 1
        
        # Extract Flask POST endpoints from test
        post_endpoints_match = re.search(r'post_endpoints_data\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if post_endpoints_match:
            endpoints = re.findall(r'["\']([^"\']+)["\']', post_endpoints_match.group(1))
            for endpoint in endpoints:
                self.tested_endpoints.add(f"POST {endpoint}")
                coverage_by_type['flask_routes'] += 1
        
        # Extract WebSocket endpoints from test
        ws_endpoints_match = re.search(r'websocket_http_endpoints\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if ws_endpoints_match:
            endpoints = re.findall(r'["\']([^"\']+)["\']', ws_endpoints_match.group(1))
            for endpoint in endpoints:
                self.tested_endpoints.add(f"GET {endpoint}")
                coverage_by_type['websocket_routes'] += 1
            # Add WebSocket connection itself
            self.tested_endpoints.add("WEBSOCKET /ws")
            coverage_by_type['websocket_routes'] += 1
        
        # Extract Dash callbacks from test  
        dash_callbacks_match = re.search(r'dash_callbacks\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if dash_callbacks_match:
            callbacks = re.findall(r'["\']([^"\']+)["\']', dash_callbacks_match.group(1))
            for callback in callbacks:
                self.tested_endpoints.add(f"CALLBACK {callback}")
                coverage_by_type['dash_callbacks'] += 1
        
        # Extract Dash components from test
        dash_components_match = re.search(r'key_components\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if dash_components_match:
            components = re.findall(r'["\']([^"\']+)["\']', dash_components_match.group(1))
            for component in components:
                self.tested_endpoints.add(f"COMPONENT {component}")
                coverage_by_type['dash_callbacks'] += 1
        
        # Extract observability endpoints from test
        obs_endpoints_match = re.search(r'observability_endpoints\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if obs_endpoints_match:
            endpoints = re.findall(r'["\']([^"\']+)["\']', obs_endpoints_match.group(1))
            for endpoint in endpoints:
                self.tested_endpoints.add(f"GET {endpoint}")
                coverage_by_type['observability_routes'] += 1
        
        # Also add fallback pattern matching for HTTP requests
        request_patterns = [
            r'requests\.get\(["\']([^"\']+)["\']\)',
            r'requests\.post\(["\']([^"\']+)["\']\)',
            r'requests\.put\(["\']([^"\']+)["\']\)',
            r'requests\.delete\(["\']([^"\']+)["\']\)'
        ]
        
        for pattern in request_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Extract just the path from full URLs
                if match.startswith('http'):
                    url_parts = match.split('/')
                    if len(url_parts) > 3:
                        path = '/' + '/'.join(url_parts[3:])
                    else:
                        continue
                else:
                    path = match
                
                self.tested_endpoints.add(path)
        
        logger.info(f"Found {len(self.tested_endpoints)} tested endpoints")
        logger.info(f"Coverage by type: {coverage_by_type}")
        
        return self.tested_endpoints

class LiveEndpointValidator:
    """Validate endpoints by making live requests"""
    
    def __init__(self):
        self.base_urls = {
            'flask': 'http://localhost:9100',
            'websocket': 'http://localhost:9101',
            'dash': 'http://localhost:9102'
        }
        self.results = {}
        
    def validate_endpoint(self, method: str, path: str, base_url: str) -> Dict[str, Any]:
        """Validate a single endpoint"""
        url = f"{base_url}{path}"
        trace_id = str(uuid.uuid4())
        headers = {'X-Trace-ID': trace_id}
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=5)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, timeout=5, json={})
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, timeout=5, json={})
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=5)
            else:
                return {
                    'status': 'skipped',
                    'reason': f'Unsupported method: {method}',
                    'trace_id': trace_id
                }
            
            return {
                'status': 'success',
                'status_code': response.status_code,
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'trace_id': trace_id,
                'has_trace_header': 'X-Trace-ID' in response.headers,
                'content_length': len(response.content)
            }
            
        except requests.exceptions.ConnectionError:
            return {
                'status': 'connection_error',
                'reason': 'Service not running',
                'trace_id': trace_id
            }
        except requests.exceptions.Timeout:
            return {
                'status': 'timeout',
                'reason': 'Request timed out',
                'trace_id': trace_id
            }
        except Exception as e:
            return {
                'status': 'error',
                'reason': str(e),
                'trace_id': trace_id
            }
    
    def validate_flask_endpoints(self, endpoints: Set[str]) -> Dict[str, Any]:
        """Validate Flask endpoints"""
        logger.info("Validating Flask endpoints...")
        results = {}
        
        for endpoint in endpoints:
            parts = endpoint.split(' ', 1)
            if len(parts) != 2:
                continue
                
            method, path = parts
            result = self.validate_endpoint(method, path, self.base_urls['flask'])
            results[endpoint] = result
            
            # Log result
            status = result['status']
            if status == 'success':
                logger.info(f"✅ {endpoint}: {result['status_code']} ({result['response_time_ms']:.1f}ms)")
            elif status == 'connection_error':
                logger.warning(f"⚠️ {endpoint}: Service not running")
            else:
                logger.error(f"❌ {endpoint}: {result['reason']}")
        
        return results
    
    def validate_websocket_endpoints(self, endpoints: Set[str]) -> Dict[str, Any]:
        """Validate WebSocket/FastAPI endpoints"""
        logger.info("Validating WebSocket/FastAPI endpoints...")
        results = {}
        
        for endpoint in endpoints:
            if endpoint.startswith('WEBSOCKET'):
                # Skip WebSocket connections for now
                results[endpoint] = {
                    'status': 'skipped',
                    'reason': 'WebSocket validation not implemented'
                }
                continue
                
            parts = endpoint.split(' ', 1)
            if len(parts) != 2:
                continue
                
            method, path = parts
            result = self.validate_endpoint(method, path, self.base_urls['websocket'])
            results[endpoint] = result
            
            # Log result
            status = result['status']
            if status == 'success':
                logger.info(f"✅ {endpoint}: {result['status_code']} ({result['response_time_ms']:.1f}ms)")
            elif status == 'connection_error':
                logger.warning(f"⚠️ {endpoint}: Service not running")
            else:
                logger.error(f"❌ {endpoint}: {result['reason']}")
        
        return results
    
    def validate_dash_endpoints(self) -> Dict[str, Any]:
        """Validate Dash application accessibility"""
        logger.info("Validating Dash application...")
        
        result = self.validate_endpoint('GET', '/', self.base_urls['dash'])
        
        status = result['status']
        if status == 'success':
            logger.info(f"✅ Dash App: {result['status_code']} ({result['response_time_ms']:.1f}ms)")
        elif status == 'connection_error':
            logger.warning(f"⚠️ Dash App: Service not running")
        else:
            logger.error(f"❌ Dash App: {result['reason']}")
        
        return {'GET /': result}

class EndpointMappingReport:
    """Generate comprehensive endpoint mapping reports"""
    
    def __init__(self):
        self.report_data = {}
        
    def generate_report(self, extracted_endpoints: Dict, tested_endpoints: Set, 
                       validation_results: Dict) -> Dict[str, Any]:
        """Generate comprehensive mapping report"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_extracted_endpoints': 0,
                'total_tested_endpoints': len(tested_endpoints),
                'total_validated_endpoints': 0,
                'services_running': 0,
                'coverage_percentage': 0.0
            },
            'endpoint_categories': {},
            'test_coverage': {},
            'validation_results': validation_results,
            'recommendations': []
        }
        
        # Process each category
        for category, endpoints in extracted_endpoints.items():
            report['summary']['total_extracted_endpoints'] += len(endpoints)
            
            # Analyze test coverage for this category
            covered_endpoints = set()
            uncovered_endpoints = set()
            
            for endpoint in endpoints:
                # Check if endpoint is covered in tests
                is_covered = any(tested_path in endpoint for tested_path in tested_endpoints)
                
                if is_covered:
                    covered_endpoints.add(endpoint)
                else:
                    uncovered_endpoints.add(endpoint)
            
            coverage_percent = (len(covered_endpoints) / len(endpoints) * 100) if endpoints else 0
            
            report['endpoint_categories'][category] = {
                'total_endpoints': len(endpoints),
                'covered_endpoints': len(covered_endpoints),
                'uncovered_endpoints': len(uncovered_endpoints),
                'coverage_percentage': round(coverage_percent, 1),
                'endpoints_list': sorted(list(endpoints)),
                'covered_list': sorted(list(covered_endpoints)),
                'uncovered_list': sorted(list(uncovered_endpoints))
            }
        
        # Calculate overall coverage
        total_endpoints = report['summary']['total_extracted_endpoints']
        total_covered = sum(cat['covered_endpoints'] for cat in report['endpoint_categories'].values())
        
        if total_endpoints > 0:
            report['summary']['coverage_percentage'] = round(total_covered / total_endpoints * 100, 1)
        
        # Count running services
        flask_running = any(r.get('status') == 'success' for r in validation_results.get('flask', {}).values())
        websocket_running = any(r.get('status') == 'success' for r in validation_results.get('websocket', {}).values())
        dash_running = any(r.get('status') == 'success' for r in validation_results.get('dash', {}).values())
        
        running_services = sum([flask_running, websocket_running, dash_running])
        report['summary']['services_running'] = running_services
        report['summary']['total_validated_endpoints'] = sum(
            len(results) for results in validation_results.values()
        )
        
        # Generate recommendations
        recommendations = []
        
        if report['summary']['coverage_percentage'] < 100:
            recommendations.append("Achieve 100% test coverage - all endpoints must be tested")
        
        if running_services < 3:
            recommendations.append("Start all services for complete validation")
        
        for category, data in report['endpoint_categories'].items():
            if data['uncovered_endpoints'] > 0:
                recommendations.append(f"Add tests for {data['uncovered_endpoints']} uncovered {category}")
        
        if not recommendations:
            recommendations.append("Excellent! All endpoints are well mapped and tested")
        
        report['recommendations'] = recommendations
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save report to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"endpoint_mapping_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to: {filename}")
        return filename
    
    def print_summary(self, report: Dict[str, Any]):
        """Print report summary to console"""
        print("\n" + "="*80)
        print("🎯 KPP SIMULATOR ENDPOINT MAPPING VERIFICATION REPORT")
        print("="*80)
        
        summary = report['summary']
        print(f"📊 Summary:")
        print(f"  • Total Endpoints: {summary['total_extracted_endpoints']}")
        print(f"  • Test Coverage: {summary['coverage_percentage']:.1f}%")
        print(f"  • Services Running: {summary['services_running']}/3")
        print(f"  • Validated Endpoints: {summary['total_validated_endpoints']}")
        
        print(f"\n📁 Endpoint Categories:")
        for category, data in report['endpoint_categories'].items():
            print(f"  • {category}: {data['total_endpoints']} total, {data['covered_endpoints']} covered ({data['coverage_percentage']:.1f}%)")
        
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
        
        print("\n" + "="*80)

def main():
    """Main execution function"""
    logger.info("🚀 Starting KPP Simulator Endpoint Mapping Verification")
    
    # Step 1: Extract all endpoints from codebase
    logger.info("Step 1: Extracting endpoints from codebase...")
    extractor = EndpointExtractor()
    extracted_endpoints = extractor.extract_all_endpoints()
    
    # Step 2: Analyze test coverage
    logger.info("Step 2: Analyzing test coverage...")
    coverage_analyzer = TestCoverageAnalyzer()
    tested_endpoints = coverage_analyzer.extract_tested_endpoints()
    
    # Step 3: Validate endpoints with live requests
    logger.info("Step 3: Validating endpoints with live requests...")
    validator = LiveEndpointValidator()
    
    validation_results = {}
    validation_results['flask'] = validator.validate_flask_endpoints(extracted_endpoints['flask_routes'])
    validation_results['websocket'] = validator.validate_websocket_endpoints(extracted_endpoints['websocket_routes'])
    validation_results['dash'] = validator.validate_dash_endpoints()
    
    # Step 4: Generate comprehensive report
    logger.info("Step 4: Generating comprehensive report...")
    report_generator = EndpointMappingReport()
    report = report_generator.generate_report(extracted_endpoints, tested_endpoints, validation_results)
    
    # Step 5: Save and display report
    filename = report_generator.save_report(report)
    report_generator.print_summary(report)
    
    logger.info(f"✅ Endpoint mapping verification completed! Report: {filename}")
    
    return report

if __name__ == "__main__":
    main() 