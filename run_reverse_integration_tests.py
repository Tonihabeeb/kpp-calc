#!/usr/bin/env python3
"""
Comprehensive Reverse Integration Test Runner for KPP Simulator
Tests complete flows from backend endpoints → main server → frontend

This runner:
1. Starts all required services (Flask, WebSocket, Dash)
2. Runs reverse integration tests with real services
3. Provides comprehensive reporting
4. Cleans up services after testing
"""

import os
import sys
import time
import json
import subprocess
import logging
import signal
import threading
from pathlib import Path
from datetime import datetime
import requests
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('reverse_integration_tests.log')
    ]
)
logger = logging.getLogger(__name__)

class KPPServiceManager:
    """Manages all KPP services for comprehensive testing"""
    
    def __init__(self):
        self.services = {}
        self.base_dir = Path(__file__).parent
        self.ports = {
            'flask': 9100,       # Flask backend (app.py)
            'websocket': 9101,   # WebSocket server (main.py)
            'dash': 9103         # Dash frontend (dash_app.py)
        }
        self.startup_wait = {
            'flask': 5,
            'websocket': 3,
            'dash': 8
        }
        
    def kill_existing_services(self):
        """Kill any existing services on our ports"""
        logger.info("Checking for existing services on target ports...")
        
        for service_name, port in self.ports.items():
            try:
                # Find processes using the port
                connections = psutil.net_connections()
                for conn in connections:
                    if conn.laddr.port == port and conn.status == 'LISTEN':
                        try:
                            process = psutil.Process(conn.pid)
                            logger.info(f"Killing existing {service_name} service (PID: {conn.pid}) on port {port}")
                            process.terminate()
                            time.sleep(1)
                            if process.is_running():
                                process.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
            except Exception as e:
                logger.warning(f"Error checking port {port}: {e}")
    
    def start_flask_backend(self):
        """Start Flask backend service"""
        logger.info("Starting Flask backend service...")
        
        # Set environment variables for Flask
        env = os.environ.copy()
        env['FLASK_APP'] = 'app.py'
        env['FLASK_ENV'] = 'development'
        env['FLASK_DEBUG'] = '1'
        
        try:
            process = subprocess.Popen([
                sys.executable, 'app.py'
            ], 
            cwd=self.base_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
            )
            
            self.services['flask'] = process
            logger.info(f"Flask backend started with PID: {process.pid}")
            
            # Wait for service to start
            time.sleep(self.startup_wait['flask'])
            
            # Check if service is healthy
            return self.check_service_health('flask')
            
        except Exception as e:
            logger.error(f"Failed to start Flask backend: {e}")
            return False
    
    def start_websocket_server(self):
        """Start WebSocket server"""
        logger.info("Starting WebSocket server...")
        
        try:
            process = subprocess.Popen([
                sys.executable, 'main.py'
            ], 
            cwd=self.base_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
            )
            
            self.services['websocket'] = process
            logger.info(f"WebSocket server started with PID: {process.pid}")
            
            # Wait for service to start
            time.sleep(self.startup_wait['websocket'])
            
            # Check if service is healthy
            return self.check_service_health('websocket')
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            return False
    
    def start_dash_frontend(self):
        """Start Dash frontend service"""
        logger.info("Starting Dash frontend service...")
        
        try:
            process = subprocess.Popen([
                sys.executable, 'dash_app.py'
            ], 
            cwd=self.base_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
            )
            
            self.services['dash'] = process
            logger.info(f"Dash frontend started with PID: {process.pid}")
            
            # Wait for service to start
            time.sleep(self.startup_wait['dash'])
            
            # Check if service is healthy
            return self.check_service_health('dash')
            
        except Exception as e:
            logger.error(f"Failed to start Dash frontend: {e}")
            return False
    
    def check_service_health(self, service_name, max_retries=10):
        """Check if a service is healthy"""
        port = self.ports[service_name]
        url = f"http://localhost:{port}"
        
        # Special health check URLs
        health_urls = {
            'flask': f"{url}/status",
            'websocket': f"{url}/",
            'dash': f"{url}/"
        }
        
        check_url = health_urls.get(service_name, url)
        
        for i in range(max_retries):
            try:
                response = requests.get(check_url, timeout=5)
                if response.status_code in [200, 404, 500]:  # Any response is good
                    logger.info(f"[OK] {service_name} service is healthy at {check_url}")
                    return True
            except requests.exceptions.RequestException:
                logger.info(f"Waiting for {service_name} service... (attempt {i+1}/{max_retries})")
                time.sleep(2)
        
        logger.error(f"[FAIL] {service_name} service failed to start at {check_url}")
        return False
    
    def start_all_services(self):
        """Start all required services"""
        logger.info("[START] Starting all KPP services...")
        
        # Kill existing services first
        self.kill_existing_services()
        time.sleep(2)
        
        # Start services in order
        services_status = {}
        
        # 1. Start Flask backend
        services_status['flask'] = self.start_flask_backend()
        
        # 2. Start WebSocket server
        services_status['websocket'] = self.start_websocket_server()
        
        # 3. Start Dash frontend
        services_status['dash'] = self.start_dash_frontend()
        
        # Report status
        logger.info("[STATUS] Service startup status:")
        for service, status in services_status.items():
            status_icon = "[OK]" if status else "[FAIL]"
            logger.info(f"  {status_icon} {service}: {'Running' if status else 'Failed'}")
        
        # Check if all services are running
        all_healthy = all(services_status.values())
        
        if all_healthy:
            logger.info("[SUCCESS] All services started successfully!")
            return True
        else:
            logger.error("[ERROR] Some services failed to start")
            return False
    
    def stop_all_services(self):
        """Stop all running services"""
        logger.info("[STOP] Stopping all KPP services...")
        
        for service_name, process in self.services.items():
            if process:
                try:
                    logger.info(f"Stopping {service_name} service (PID: {process.pid})...")
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=5)
                        logger.info(f"[OK] {service_name} service stopped gracefully")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"[WARN] {service_name} service didn't stop gracefully, forcing kill...")
                        process.kill()
                        process.wait()
                        logger.info(f"[OK] {service_name} service killed")
                        
                except Exception as e:
                    logger.error(f"Error stopping {service_name}: {e}")
        
        self.services.clear()
        logger.info("[DONE] All services stopped")
    
    def get_service_logs(self, service_name):
        """Get logs from a service"""
        if service_name in self.services:
            process = self.services[service_name]
            try:
                # Get stdout and stderr
                stdout_data = process.stdout.read() if process.stdout else ""
                stderr_data = process.stderr.read() if process.stderr else ""
                
                return {
                    'stdout': stdout_data,
                    'stderr': stderr_data,
                    'returncode': process.returncode
                }
            except Exception as e:
                logger.error(f"Error getting logs for {service_name}: {e}")
                return {'error': str(e)}
        
        return {'error': f'Service {service_name} not found'}
    
    def get_system_status(self):
        """Get comprehensive system status"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'ports': self.ports,
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'cwd': str(self.base_dir)
            }
        }
        
        # Check each service
        for service_name, port in self.ports.items():
            service_status = {
                'port': port,
                'running': service_name in self.services,
                'healthy': self.check_service_health(service_name, max_retries=1)
            }
            
            if service_name in self.services:
                process = self.services[service_name]
                service_status.update({
                    'pid': process.pid,
                    'returncode': process.returncode
                })
            
            status['services'][service_name] = service_status
        
        return status

class ReverseIntegrationTestRunner:
    """Runs comprehensive reverse integration tests"""
    
    def __init__(self):
        self.service_manager = KPPServiceManager()
        self.test_results = {
            'start_time': None,
            'end_time': None,
            'duration': None,
            'services_started': False,
            'tests_run': False,
            'test_results': {},
            'service_logs': {},
            'system_status': {}
        }
    
    def run_tests_with_live_services(self):
        """Run tests with live services"""
        logger.info("[TEST] Running reverse integration tests with live services...")
        
        try:
            # Run pytest with the reverse integration tests
            result = subprocess.run([
                sys.executable, '-m', 'pytest', 
                'tests/test_reverse_integration.py',
                '-v',
                '--tb=short',
                '--capture=no',
                '--color=yes'
            ], 
            cwd=self.service_manager.base_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
            )
            
            self.test_results['test_results'] = {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
            logger.info(f"Test execution completed with return code: {result.returncode}")
            
            if result.returncode == 0:
                logger.info("✅ All reverse integration tests PASSED!")
            else:
                logger.error("❌ Some reverse integration tests FAILED")
                logger.error(f"STDOUT:\n{result.stdout}")
                logger.error(f"STDERR:\n{result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            logger.error("⏰ Tests timed out after 5 minutes")
            self.test_results['test_results'] = {
                'error': 'Tests timed out',
                'success': False
            }
            return False
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            self.test_results['test_results'] = {
                'error': str(e),
                'success': False
            }
            return False
    
    def run_complete_test_suite(self):
        """Run the complete reverse integration test suite"""
        logger.info("[TARGET] Starting Complete Reverse Integration Test Suite")
        logger.info("=" * 80)
        
        self.test_results['start_time'] = datetime.now().isoformat()
        
        try:
            # Phase 1: Start all services
            logger.info("[PHASE1] Phase 1: Starting all services...")
            services_started = self.service_manager.start_all_services()
            self.test_results['services_started'] = services_started
            
            if not services_started:
                logger.error("[ERROR] Failed to start services - aborting tests")
                return False
            
            # Phase 2: Run tests
            logger.info("[PHASE2] Phase 2: Running reverse integration tests...")
            tests_passed = self.run_tests_with_live_services()
            self.test_results['tests_run'] = True
            
            # Phase 3: Collect service logs
            logger.info("[PHASE3] Phase 3: Collecting service logs...")
            for service_name in self.service_manager.services:
                self.test_results['service_logs'][service_name] = self.service_manager.get_service_logs(service_name)
            
            # Phase 4: Get system status
            logger.info("[PHASE4] Phase 4: Collecting system status...")
            self.test_results['system_status'] = self.service_manager.get_system_status()
            
            return tests_passed
            
        except Exception as e:
            logger.error(f"Critical error in test suite: {e}")
            self.test_results['error'] = str(e)
            return False
        
        finally:
            # Always cleanup
            self.service_manager.stop_all_services()
            self.test_results['end_time'] = datetime.now().isoformat()
            
            # Calculate duration
            if self.test_results['start_time'] and self.test_results['end_time']:
                start = datetime.fromisoformat(self.test_results['start_time'])
                end = datetime.fromisoformat(self.test_results['end_time'])
                self.test_results['duration'] = (end - start).total_seconds()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("[REPORT] Generating comprehensive test report...")
        
        report = {
            'test_suite': 'KPP Reverse Integration Tests',
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'services_started': self.test_results.get('services_started', False),
                'tests_run': self.test_results.get('tests_run', False),
                'tests_passed': self.test_results.get('test_results', {}).get('success', False),
                'duration_seconds': self.test_results.get('duration', 0)
            },
            'results': self.test_results,
            'recommendations': []
        }
        
        # Add recommendations based on results
        if not report['summary']['services_started']:
            report['recommendations'].append("Check service startup logs and port availability")
        
        if not report['summary']['tests_passed']:
            report['recommendations'].append("Review test output for specific failures")
            report['recommendations'].append("Check service health and network connectivity")
        
        if report['summary']['tests_passed']:
            report['recommendations'].append("All tests passed! System is ready for production")
        
        # Save report
        report_file = f"reverse_integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"[SAVE] Test report saved to: {report_file}")
        
        # Print summary
        logger.info("=" * 80)
        logger.info("[TARGET] REVERSE INTEGRATION TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"[OK] Services Started: {report['summary']['services_started']}")
        logger.info(f"[OK] Tests Run: {report['summary']['tests_run']}")
        logger.info(f"[OK] Tests Passed: {report['summary']['tests_passed']}")
        logger.info(f"[TIME] Duration: {report['summary']['duration_seconds']:.2f} seconds")
        
        if report['recommendations']:
            logger.info("[IDEA] Recommendations:")
            for rec in report['recommendations']:
                logger.info(f"  • {rec}")
        
        return report

def main():
    """Main test runner function"""
    logger.info("[START] KPP Reverse Integration Test Runner")
    logger.info("=" * 80)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("[STOP] Received shutdown signal")
        if 'test_runner' in globals():
            test_runner.service_manager.stop_all_services()
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create test runner
    test_runner = ReverseIntegrationTestRunner()
    
    try:
        # Run complete test suite
        success = test_runner.run_complete_test_suite()
        
        # Generate report
        report = test_runner.generate_report()
        
        # Exit with appropriate code
        if success:
            logger.info("[SUCCESS] Reverse integration tests completed successfully!")
            sys.exit(0)
        else:
            logger.error("[ERROR] Reverse integration tests failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"[ERROR] Critical error: {e}")
        test_runner.service_manager.stop_all_services()
        sys.exit(1)

if __name__ == "__main__":
    main() 