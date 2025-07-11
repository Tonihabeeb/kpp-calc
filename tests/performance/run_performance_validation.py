import os
import sys
import pytest
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np
from metrics_tracker import GridServicesMetrics

class PerformanceTestRunner:
    def __init__(self):
        """Initialize the performance test runner"""
        self.metrics = GridServicesMetrics(
            output_file=f"performance_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        self.test_results: Dict[str, Any] = {}
        self.test_dependencies: Dict[str, List[str]] = {
            'test_battery_storage_response_time': [],
            'test_load_curtailment_efficiency': [],
            'test_economic_optimizer_calculation_speed': [],
            'test_coordinator_service_integration': [
                'test_battery_storage_response_time',
                'test_load_curtailment_efficiency',
                'test_economic_optimizer_calculation_speed'
            ],
            'test_concurrent_service_operations': [
                'test_coordinator_service_integration'
            ]
        }
        
    def run_tests(self) -> bool:
        """Run all performance tests in dependency order"""
        try:
            # Create test session
            session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            print(f"\nStarting Performance Validation Session: {session_id}")
            
            # Run tests in dependency order
            executed_tests = set()
            all_tests = list(self.test_dependencies.keys())
            
            while all_tests:
                # Find tests with satisfied dependencies
                runnable_tests = [
                    test for test in all_tests
                    if all(dep in executed_tests for dep in self.test_dependencies[test])
                ]
                
                if not runnable_tests:
                    remaining = [t for t in all_tests if t not in executed_tests]
                    print(f"\nError: Circular dependency detected in tests: {remaining}")
                    return False
                
                # Run the tests
                for test in runnable_tests:
                    print(f"\nExecuting test: {test}")
                    start_time = time.time()
                    
                    # Run test with pytest
                    result = pytest.main([
                        'phase4_performance_validation.py',
                        f'-k {test}',
                        '-v',
                        '--capture=no',
                        '--tb=short',
                    ])
                    
                    execution_time = time.time() - start_time
                    
                    # Record test result
                    self.test_results[test] = {
                        'status': 'PASSED' if result == 0 else 'FAILED',
                        'execution_time': execution_time,
                        'dependencies': self.test_dependencies[test],
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    executed_tests.add(test)
                    all_tests.remove(test)
                    
                    # Break if test failed and it has dependents
                    if result != 0 and any(test in deps for deps in self.test_dependencies.values()):
                        print(f"\nAborting: Test {test} failed and has dependent tests")
                        return False
            
            # Generate final report
            self.generate_report(session_id)
            return all(result['status'] == 'PASSED' for result in self.test_results.values())
            
        except Exception as e:
            print(f"\nError running performance tests: {e}")
            return False
            
    def generate_report(self, session_id: str):
        """Generate comprehensive performance report"""
        report = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'test_results': self.test_results,
            'metrics': self.metrics.get_all_statistics(),
            'performance_analysis': {
                'threshold_checks': self.metrics.check_performance_thresholds(),
                'trends': {},
                'anomalies': {},
                'recommendations': []
            }
        }
        
        # Analyze performance trends
        for metric in self.metrics.metrics:
            trend = self.metrics.analyze_trend(metric)
            anomalies = self.metrics.detect_anomalies(metric)
            
            if trend:
                report['performance_analysis']['trends'][metric] = trend
            if anomalies:
                report['performance_analysis']['anomalies'][metric] = anomalies
                
            # Generate recommendations
            stats = self.metrics.get_statistics(metric)
            if 'threshold_exceeded' in stats and stats['threshold_exceeded']:
                report['performance_analysis']['recommendations'].append({
                    'metric': metric,
                    'issue': 'Threshold Exceeded',
                    'current_value': stats['mean'],
                    'recommendation': self._get_recommendation(metric, stats)
                })
            
            if trend and trend['is_significant'] and trend['trend'] == 'degrading':
                report['performance_analysis']['recommendations'].append({
                    'metric': metric,
                    'issue': 'Performance Degradation',
                    'trend_slope': trend['slope'],
                    'recommendation': f"Investigate {metric} performance degradation"
                })
        
        # Save report
        report_file = f"performance_report_{session_id}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=4)
            
        # Print summary
        self._print_report_summary(report)
        
    def _get_recommendation(self, metric: str, stats: Dict[str, Any]) -> str:
        """Generate specific recommendations based on metric type and statistics"""
        if 'response_time' in metric:
            if stats['std'] > stats['mean'] * 0.5:
                return "High response time variance detected. Consider optimizing for consistent performance."
            return "Response time exceeds threshold. Review processing overhead and optimize critical paths."
            
        elif 'efficiency' in metric:
            if stats['min'] < 70:
                return "Critical efficiency drops detected. Review resource utilization and optimization algorithms."
            return "Efficiency below target. Consider fine-tuning parameters and resource allocation."
            
        elif 'stability' in metric:
            if stats['std'] > 0.1:
                return "High stability variance. Review control parameters and feedback mechanisms."
            return "Stability below threshold. Evaluate control system tuning and response characteristics."
            
        return "Review implementation and optimize performance"
        
    def _print_report_summary(self, report: Dict[str, Any]):
        """Print formatted summary of test results and recommendations"""
        print("\n" + "="*80)
        print(f"Performance Validation Summary - Session {report['session_id']}")
        print("="*80)
        
        # Test Results
        print("\nTest Results:")
        for test, result in report['test_results'].items():
            status_color = '\033[92m' if result['status'] == 'PASSED' else '\033[91m'
            print(f"{status_color}{test}: {result['status']}\033[0m")
            print(f"  Time: {result['execution_time']:.2f}s")
            if result['dependencies']:
                print(f"  Dependencies: {', '.join(result['dependencies'])}")
                
        # Performance Analysis
        print("\nPerformance Analysis:")
        threshold_checks = report['performance_analysis']['threshold_checks']
        for metric, checks in threshold_checks.items():
            for check_type, check in checks.items():
                status = '\033[92m✓\033[0m' if check['passed'] else '\033[91m✗\033[0m'
                print(f"\n{metric} - {check_type}:")
                print(f"  Status: {status}")
                print(f"  Actual: {check['actual']:.3f}")
                print(f"  Threshold: {check['threshold']:.3f}")
                print(f"  Margin: {check['margin']:.3f}")
                
        # Recommendations
        if report['performance_analysis']['recommendations']:
            print("\nRecommendations:")
            for rec in report['performance_analysis']['recommendations']:
                print(f"\n- {rec['metric']}:")
                print(f"  Issue: {rec['issue']}")
                print(f"  Recommendation: {rec['recommendation']}")
                
        print("\n" + "="*80)

def run_performance_tests():
    """Main entry point for running performance tests"""
    runner = PerformanceTestRunner()
    success = runner.run_tests()
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(run_performance_tests()) 