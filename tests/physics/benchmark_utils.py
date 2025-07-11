"""
Performance benchmarking utilities for physics components.
"""

import time
import psutil
import numpy as np
from typing import Callable, Dict, Any
from functools import wraps

def benchmark_function(func: Callable) -> Callable:
    """Decorator to benchmark function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        execution_time = end_time - start_time
        memory_used = end_memory - start_memory
        
        # Store benchmark results
        if not hasattr(wrapper, 'benchmark_results'):
            wrapper.benchmark_results = []
        
        wrapper.benchmark_results.append({
            'execution_time': execution_time,
            'memory_used': memory_used,
            'timestamp': time.time()
        })
        
        return result
    
    return wrapper

def get_benchmark_stats(func: Callable) -> Dict[str, Any]:
    """Get benchmark statistics for a function"""
    if not hasattr(func, 'benchmark_results'):
        return {}
    
    times = [r['execution_time'] for r in func.benchmark_results]
    memories = [r['memory_used'] for r in func.benchmark_results]
    
    return {
        'count': len(times),
        'mean_time': np.mean(times),
        'std_time': np.std(times),
        'min_time': np.min(times),
        'max_time': np.max(times),
        'mean_memory': np.mean(memories),
        'max_memory': np.max(memories)
    }

class PerformanceValidator:
    """Validator for performance requirements"""
    
    def __init__(self, max_execution_time: float = 0.1, max_memory_mb: float = 100.0):
        self.max_execution_time = max_execution_time
        self.max_memory_mb = max_memory_mb * 1024 * 1024  # Convert to bytes
    
    def validate_performance(self, func: Callable) -> bool:
        """Validate function performance"""
        stats = get_benchmark_stats(func)
        
        if not stats:
            return False
        
        time_ok = stats['mean_time'] <= self.max_execution_time
        memory_ok = stats['max_memory'] <= self.max_memory_mb
        
        return time_ok and memory_ok
