import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats

class PerformanceMetricsTracker:
    def __init__(self, output_file: str = None):
        self.metrics: Dict[str, List[float]] = {}
        self.start_times: Dict[str, float] = {}
        self.output_file = output_file or f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.thresholds: Dict[str, Dict[str, float]] = {}
        
    def set_threshold(self, metric_name: str, threshold_type: str, value: float):
        """Set performance threshold for a metric"""
        if metric_name not in self.thresholds:
            self.thresholds[metric_name] = {}
        self.thresholds[metric_name][threshold_type] = value
        
    def start_measurement(self, metric_name: str):
        """Start timing a specific metric"""
        self.start_times[metric_name] = time.time()
        
    def end_measurement(self, metric_name: str) -> float:
        """End timing a specific metric and record the duration"""
        if metric_name not in self.start_times:
            raise ValueError(f"No start time found for metric: {metric_name}")
            
        duration = time.time() - self.start_times[metric_name]
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(duration)
        del self.start_times[metric_name]
        return duration
        
    def record_value(self, metric_name: str, value: float):
        """Record a specific metric value"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)
        
    def get_statistics(self, metric_name: str) -> Dict[str, float]:
        """Calculate comprehensive statistics for a specific metric"""
        if metric_name not in self.metrics:
            raise ValueError(f"No data found for metric: {metric_name}")
            
        values = np.array(self.metrics[metric_name])
        
        # Basic statistics
        stats_dict = {
            'mean': float(np.mean(values)),
            'median': float(np.median(values)),
            'std': float(np.std(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'count': len(values),
            'variance': float(np.var(values)),
            'skewness': float(stats.skew(values)),
            'kurtosis': float(stats.kurtosis(values))
        }
        
        # Percentiles
        percentiles = [1, 5, 25, 75, 95, 99]
        for p in percentiles:
            stats_dict[f'p{p}'] = float(np.percentile(values, p))
            
        # Check thresholds if set
        if metric_name in self.thresholds:
            for threshold_type, threshold_value in self.thresholds[metric_name].items():
                if threshold_type == 'max':
                    stats_dict['threshold_exceeded'] = any(v > threshold_value for v in values)
                elif threshold_type == 'min':
                    stats_dict['threshold_exceeded'] = any(v < threshold_value for v in values)
                elif threshold_type == 'mean':
                    stats_dict['threshold_exceeded'] = stats_dict['mean'] > threshold_value
                    
        return stats_dict
        
    def get_all_statistics(self) -> Dict[str, Dict[str, float]]:
        """Calculate statistics for all metrics"""
        return {
            metric: self.get_statistics(metric)
            for metric in self.metrics
        }
        
    def analyze_trend(self, metric_name: str, window_size: int = 10) -> Optional[Dict[str, Any]]:
        """Analyze trend for a specific metric using moving averages"""
        if metric_name not in self.metrics or len(self.metrics[metric_name]) < window_size:
            return None
            
        values = np.array(self.metrics[metric_name])
        moving_avg = np.convolve(values, np.ones(window_size)/window_size, mode='valid')
        
        # Calculate trend
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            range(len(moving_avg)), moving_avg
        )
        
        return {
            'slope': float(slope),
            'r_squared': float(r_value ** 2),
            'p_value': float(p_value),
            'is_significant': p_value < 0.05,
            'trend': 'improving' if slope < 0 else 'degrading' if slope > 0 else 'stable',
            'moving_average': moving_avg.tolist()
        }
        
    def detect_anomalies(self, metric_name: str, threshold: float = 3.0) -> List[Tuple[int, float]]:
        """Detect anomalies using Z-score method"""
        if metric_name not in self.metrics:
            return []
            
        values = np.array(self.metrics[metric_name])
        z_scores = np.abs(stats.zscore(values))
        anomalies = [(i, values[i]) for i in range(len(values)) if z_scores[i] > threshold]
        return anomalies
        
    def save_metrics(self):
        """Save metrics to JSON file with enhanced analysis"""
        stats = self.get_all_statistics()
        
        # Add trend analysis and anomalies for each metric
        analysis = {}
        for metric in self.metrics:
            analysis[metric] = {
                'statistics': stats[metric],
                'trend_analysis': self.analyze_trend(metric),
                'anomalies': self.detect_anomalies(metric)
            }
            
        with open(self.output_file, 'w') as f:
            json.dump(analysis, f, indent=4)
            
    def clear_metrics(self):
        """Clear all recorded metrics"""
        self.metrics.clear()
        self.start_times.clear()
        self.thresholds.clear()

class GridServicesMetrics(PerformanceMetricsTracker):
    """Specialized metrics tracker for grid services"""
    
    # Default thresholds
    RESPONSE_TIME_THRESHOLD = 0.25  # 250ms
    EFFICIENCY_THRESHOLD = 90.0     # 90%
    STABILITY_THRESHOLD = 0.95      # 95%
    
    def __init__(self, output_file: str = None):
        super().__init__(output_file)
        self._init_thresholds()
        
    def _init_thresholds(self):
        """Initialize default thresholds for grid services"""
        # Response time thresholds
        self.set_threshold('battery_response_time', 'max', self.RESPONSE_TIME_THRESHOLD)
        self.set_threshold('frequency_response_time', 'max', self.RESPONSE_TIME_THRESHOLD)
        self.set_threshold('voltage_response_time', 'max', self.RESPONSE_TIME_THRESHOLD)
        
        # Efficiency thresholds
        self.set_threshold('battery_efficiency', 'min', self.EFFICIENCY_THRESHOLD)
        self.set_threshold('load_curtailment_efficiency', 'min', self.EFFICIENCY_THRESHOLD)
        self.set_threshold('economic_efficiency', 'min', self.EFFICIENCY_THRESHOLD)
        
        # Stability thresholds
        self.set_threshold('frequency_stability', 'min', self.STABILITY_THRESHOLD)
        self.set_threshold('voltage_stability', 'min', self.STABILITY_THRESHOLD)
        
    def track_response_time(self, service_name: str, operation: str):
        """Track response time for a specific service operation"""
        metric_name = f"{service_name}_{operation}_response_time"
        self.start_measurement(metric_name)
        return lambda: self.end_measurement(metric_name)
        
    def track_efficiency(self, service_name: str, achieved: float, target: float):
        """Track efficiency metrics for a service"""
        efficiency = (achieved / target) * 100 if target != 0 else 0
        self.record_value(f"{service_name}_efficiency", efficiency)
        return efficiency
        
    def track_resource_usage(self, service_name: str, cpu_usage: float, memory_usage: float):
        """Track resource usage metrics"""
        self.record_value(f"{service_name}_cpu_usage", cpu_usage)
        self.record_value(f"{service_name}_memory_usage", memory_usage)
        
    def track_stability(self, service_name: str, measurement: float, setpoint: float):
        """Track stability metrics"""
        stability = 1.0 - min(abs(measurement - setpoint) / abs(setpoint) if setpoint != 0 else 0, 1.0)
        self.record_value(f"{service_name}_stability", stability * 100)
        return stability
        
    def check_performance_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Check if services meet performance thresholds with detailed analysis"""
        results = {}
        stats = self.get_all_statistics()
        
        for metric, values in stats.items():
            if metric not in self.thresholds:
                continue
                
            threshold_results = {}
            for threshold_type, threshold_value in self.thresholds[metric].items():
                if threshold_type == 'max':
                    passed = values['max'] <= threshold_value
                    margin = threshold_value - values['mean']
                elif threshold_type == 'min':
                    passed = values['min'] >= threshold_value
                    margin = values['mean'] - threshold_value
                else:
                    continue
                    
                threshold_results[threshold_type] = {
                    'passed': passed,
                    'threshold': threshold_value,
                    'actual': values['mean'],
                    'margin': margin,
                    'trend': self.analyze_trend(metric),
                    'anomalies': self.detect_anomalies(metric)
                }
                
            results[metric] = threshold_results
                
        return results 