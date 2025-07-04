#!/usr/bin/env python3
"""
Real-Time Performance Monitor for KPP Simulator
Monitors system performance, data flow, and provides analytics
"""

import time
import json
import logging
import requests
import threading
from collections import deque
from datetime import datetime
import statistics

class KPPPerformanceMonitor:
    """
    Comprehensive performance monitoring for KPP real-time system
    """
    
    def __init__(self, backend_url="http://localhost:9100", websocket_url="http://localhost:9101", frontend_url="http://localhost:9103"):
        self.backend_url = backend_url
        self.websocket_url = websocket_url
        self.frontend_url = frontend_url
        
        # Performance metrics storage
        self.metrics_window = 300  # 5 minutes of data
        self.response_times = {
            'backend': deque(maxlen=self.metrics_window),
            'websocket': deque(maxlen=self.metrics_window),
            'frontend': deque(maxlen=self.metrics_window)
        }
        
        self.data_rates = {
            'backend_requests': deque(maxlen=self.metrics_window),
            'websocket_requests': deque(maxlen=self.metrics_window),
            'data_points': deque(maxlen=self.metrics_window)
        }
        
        self.error_counts = {
            'backend_errors': 0,
            'websocket_errors': 0,
            'timeout_errors': 0,
            'data_errors': 0
        }
        
        self.simulation_metrics = {
            'power_readings': deque(maxlen=self.metrics_window),
            'torque_readings': deque(maxlen=self.metrics_window),
            'efficiency_readings': deque(maxlen=self.metrics_window),
            'update_timestamps': deque(maxlen=self.metrics_window)
        }
        
        self.running = False
        self.monitor_thread = None
        
        # Performance targets (best practice thresholds)
        self.targets = {
            'max_response_time': 200,  # ms
            'min_update_rate': 4.0,   # Hz (updates per second)
            'max_error_rate': 0.02,   # 2% error rate
            'min_data_rate': 1000,    # bytes/second
            'max_jitter': 50          # ms variance in update timing
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def start_monitoring(self):
        """Start the performance monitoring loop"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop the performance monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Test backend performance
                backend_metrics = self._test_backend_performance()
                
                # Test WebSocket performance
                websocket_metrics = self._test_websocket_performance()
                
                # Calculate derived metrics
                self._update_derived_metrics()
                
                # Log performance summary every 30 seconds
                if len(self.response_times['backend']) > 0 and len(self.response_times['backend']) % 30 == 0:
                    self._log_performance_summary()
                
                time.sleep(1.0)  # Monitor every second
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(5.0)  # Wait longer on error
    
    def _test_backend_performance(self):
        """Test backend API performance"""
        try:
            start_time = time.time()
            
            # Test status endpoint
            response = requests.get(f"{self.backend_url}/status", timeout=2)
            status_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if response.status_code == 200:
                self.response_times['backend'].append(status_time)
                self.data_rates['backend_requests'].append(time.time())
                
                # Test live data if simulation is running
                status_data = response.json()
                if status_data.get('simulation_running'):
                    live_start = time.time()
                    live_response = requests.get(f"{self.backend_url}/data/live", timeout=3)
                    live_time = (time.time() - live_start) * 1000
                    
                    if live_response.status_code == 200:
                        live_data = live_response.json()
                        if live_data.get('data'):
                            # Record simulation data metrics
                            latest = live_data['data'][-1]
                            self.simulation_metrics['power_readings'].append(latest.get('power', 0))
                            self.simulation_metrics['torque_readings'].append(latest.get('torque', 0))
                            self.simulation_metrics['efficiency_readings'].append(latest.get('overall_efficiency', 0))
                            self.simulation_metrics['update_timestamps'].append(time.time())
                            
                        # Estimate data transfer rate
                        data_size = len(json.dumps(live_data))
                        self.data_rates['data_points'].append(data_size)
                        
                return {
                    'status_response_time': status_time,
                    'live_response_time': live_time if status_data.get('simulation_running') else None,
                    'simulation_running': status_data.get('simulation_running', False)
                }
            else:
                self.error_counts['backend_errors'] += 1
                return {'error': f"Backend returned {response.status_code}"}
                
        except requests.exceptions.Timeout:
            self.error_counts['timeout_errors'] += 1
            return {'error': 'Backend timeout'}
        except Exception as e:
            self.error_counts['backend_errors'] += 1
            return {'error': str(e)}
    
    def _test_websocket_performance(self):
        """Test WebSocket server performance"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.websocket_url}/state", timeout=2)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                self.response_times['websocket'].append(response_time)
                self.data_rates['websocket_requests'].append(time.time())
                
                ws_data = response.json()
                return {
                    'response_time': response_time,
                    'status': ws_data.get('status'),
                    'has_simulation_data': bool(ws_data.get('simulation_data'))
                }
            else:
                self.error_counts['websocket_errors'] += 1
                return {'error': f"WebSocket returned {response.status_code}"}
                
        except requests.exceptions.Timeout:
            self.error_counts['timeout_errors'] += 1
            return {'error': 'WebSocket timeout'}
        except Exception as e:
            self.error_counts['websocket_errors'] += 1
            return {'error': str(e)}
    
    def _update_derived_metrics(self):
        """Calculate derived performance metrics"""
        # Update rates calculation
        current_time = time.time()
        
        # Backend request rate (requests per second)
        recent_backend = [t for t in self.data_rates['backend_requests'] if current_time - t < 60]
        backend_rate = len(recent_backend) / 60.0 if recent_backend else 0
        
        # WebSocket request rate
        recent_websocket = [t for t in self.data_rates['websocket_requests'] if current_time - t < 60]
        websocket_rate = len(recent_websocket) / 60.0 if recent_websocket else 0
        
        # Data transfer rate (approximate)
        recent_data = [s for s in self.data_rates['data_points'] if len(self.data_rates['data_points']) > 0]
        avg_data_size = statistics.mean(recent_data) if recent_data else 0
        data_transfer_rate = avg_data_size * backend_rate  # bytes per second
        
        return {
            'backend_request_rate': backend_rate,
            'websocket_request_rate': websocket_rate,
            'data_transfer_rate': data_transfer_rate
        }
    
    def _log_performance_summary(self):
        """Log comprehensive performance summary"""
        try:
            # Response time statistics
            backend_times = list(self.response_times['backend'])
            websocket_times = list(self.response_times['websocket'])
            
            backend_stats = self._calculate_stats(backend_times) if backend_times else {}
            websocket_stats = self._calculate_stats(websocket_times) if websocket_times else {}
            
            # Update rate calculation
            derived = self._update_derived_metrics()
            
            # Error rate calculation
            total_requests = len(self.response_times['backend']) + len(self.response_times['websocket'])
            total_errors = sum(self.error_counts.values())
            error_rate = total_errors / max(total_requests, 1)
            
            # Simulation data health
            recent_power = list(self.simulation_metrics['power_readings'])[-10:]
            power_variance = statistics.stdev(recent_power) if len(recent_power) > 1 else 0
            
            # Performance assessment
            performance_score = self._calculate_performance_score(
                backend_stats.get('mean', 0),
                websocket_stats.get('mean', 0),
                derived.get('backend_request_rate', 0),
                error_rate
            )
            
            self.logger.info(f"""
=== KPP Real-Time Performance Summary ===
Response Times (ms):
  Backend: avg={backend_stats.get('mean', 0):.1f}, min={backend_stats.get('min', 0):.1f}, max={backend_stats.get('max', 0):.1f}
  WebSocket: avg={websocket_stats.get('mean', 0):.1f}, min={websocket_stats.get('min', 0):.1f}, max={websocket_stats.get('max', 0):.1f}

Update Rates (Hz):
  Backend: {derived.get('backend_request_rate', 0):.1f} req/s
  WebSocket: {derived.get('websocket_request_rate', 0):.1f} req/s
  Data Transfer: {derived.get('data_transfer_rate', 0):.0f} bytes/s

Error Statistics:
  Error Rate: {error_rate:.1%}
  Backend Errors: {self.error_counts['backend_errors']}
  WebSocket Errors: {self.error_counts['websocket_errors']}
  Timeouts: {self.error_counts['timeout_errors']}

Simulation Health:
  Power Variance: {power_variance:.1f}W
  Data Points: {len(self.simulation_metrics['power_readings'])}

Performance Score: {performance_score:.1f}/100
==========================================""")
            
        except Exception as e:
            self.logger.error(f"Error creating performance summary: {e}")
    
    def _calculate_stats(self, data):
        """Calculate basic statistics for a dataset"""
        if not data:
            return {}
        
        return {
            'mean': statistics.mean(data),
            'median': statistics.median(data),
            'min': min(data),
            'max': max(data),
            'stdev': statistics.stdev(data) if len(data) > 1 else 0
        }
    
    def _calculate_performance_score(self, backend_time, websocket_time, update_rate, error_rate):
        """Calculate overall performance score (0-100)"""
        score = 100.0
        
        # Penalize slow response times
        if backend_time > self.targets['max_response_time']:
            score -= (backend_time - self.targets['max_response_time']) / 10
        
        if websocket_time > self.targets['max_response_time']:
            score -= (websocket_time - self.targets['max_response_time']) / 10
        
        # Penalize low update rates
        if update_rate < self.targets['min_update_rate']:
            score -= (self.targets['min_update_rate'] - update_rate) * 10
        
        # Penalize high error rates
        if error_rate > self.targets['max_error_rate']:
            score -= (error_rate - self.targets['max_error_rate']) * 500
        
        return max(0, min(100, score))
    
    def get_performance_report(self):
        """Get detailed performance report"""
        derived = self._update_derived_metrics()
        
        backend_times = list(self.response_times['backend'])
        websocket_times = list(self.response_times['websocket'])
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'response_times': {
                'backend': self._calculate_stats(backend_times),
                'websocket': self._calculate_stats(websocket_times)
            },
            'update_rates': derived,
            'error_counts': dict(self.error_counts),
            'simulation_health': {
                'power_readings_count': len(self.simulation_metrics['power_readings']),
                'recent_power_avg': statistics.mean(list(self.simulation_metrics['power_readings'])[-10:]) if self.simulation_metrics['power_readings'] else 0,
                'data_freshness_seconds': time.time() - (list(self.simulation_metrics['update_timestamps'])[-1] if self.simulation_metrics['update_timestamps'] else time.time())
            },
            'performance_targets': self.targets,
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self):
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Check response times
        if self.response_times['backend']:
            avg_backend = statistics.mean(self.response_times['backend'])
            if avg_backend > self.targets['max_response_time']:
                recommendations.append(f"Backend response time ({avg_backend:.1f}ms) exceeds target ({self.targets['max_response_time']}ms). Consider optimizing database queries or caching.")
        
        if self.response_times['websocket']:
            avg_websocket = statistics.mean(self.response_times['websocket'])
            if avg_websocket > self.targets['max_response_time']:
                recommendations.append(f"WebSocket response time ({avg_websocket:.1f}ms) exceeds target. Consider reducing data payload size.")
        
        # Check update rates
        derived = self._update_derived_metrics()
        if derived.get('backend_request_rate', 0) < self.targets['min_update_rate']:
            recommendations.append("Backend update rate is below target. Increase polling frequency or check for blocking operations.")
        
        # Check error rates
        total_requests = len(self.response_times['backend']) + len(self.response_times['websocket'])
        if total_requests > 0:
            error_rate = sum(self.error_counts.values()) / total_requests
            if error_rate > self.targets['max_error_rate']:
                recommendations.append(f"Error rate ({error_rate:.1%}) exceeds target. Check network connectivity and service health.")
        
        if not recommendations:
            recommendations.append("System performance is within acceptable parameters.")
        
        return recommendations

if __name__ == "__main__":
    # Example usage
    monitor = KPPPerformanceMonitor()
    monitor.start_monitoring()
    
    try:
        # Run for 60 seconds as a demo
        time.sleep(60)
        
        # Generate final report
        report = monitor.get_performance_report()
        print("\n=== Final Performance Report ===")
        print(json.dumps(report, indent=2))
        
    except KeyboardInterrupt:
        print("Monitoring interrupted by user")
    finally:
        monitor.stop_monitoring() 