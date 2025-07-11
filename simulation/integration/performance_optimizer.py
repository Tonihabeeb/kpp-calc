"""
Performance optimization utilities for KPP simulator.
"""

import time
import numpy as np
from typing import Dict, Any, List, Callable
import threading
from concurrent.futures import ThreadPoolExecutor

class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize performance optimizer"""
        self.config = config
        
        # Performance settings
        self.target_fps = config.get('target_fps', 50.0)
        self.max_frame_time = 1.0 / self.target_fps
        self.adaptive_timestep = config.get('adaptive_timestep', True)
        self.parallel_processing = config.get('parallel_processing', False)
        
        # Performance tracking
        self.frame_times = []
        self.optimization_history = []
        
        # Thread pool for parallel processing
        self.thread_pool = ThreadPoolExecutor(max_workers=4) if self.parallel_processing else None
        
        print("PerformanceOptimizer initialized")
        
    def optimize_timestep(self, current_frame_time: float, current_timestep: float) -> float:
        """Optimize timestep based on performance"""
        if not self.adaptive_timestep:
            return current_timestep
            
        # Store frame time
        self.frame_times.append(current_frame_time)
        if len(self.frame_times) > 100:
            self.frame_times.pop(0)
            
        # Calculate average frame time
        avg_frame_time = np.mean(self.frame_times)
        
        # Adjust timestep to maintain target FPS
        if avg_frame_time > self.max_frame_time * 1.1:
            # Too slow - reduce timestep
            new_timestep = current_timestep * 0.9
        elif avg_frame_time < self.max_frame_time * 0.9:
            # Too fast - increase timestep
            new_timestep = current_timestep * 1.1
        else:
            new_timestep = current_timestep
            
        # Limit timestep range
        new_timestep = max(0.001, min(0.1, new_timestep))
        
        # Log optimization
        optimization = {
            'time': time.time(),
            'avg_frame_time': avg_frame_time,
            'old_timestep': current_timestep,
            'new_timestep': new_timestep,
            'target_fps': self.target_fps
        }
        self.optimization_history.append(optimization)
        
        return new_timestep
        
    def parallel_execute(self, tasks: List[Callable]) -> List[Any]:
        """Execute tasks in parallel if enabled"""
        if not self.parallel_processing or not self.thread_pool:
            # Sequential execution
            return [task() for task in tasks]
            
        # Parallel execution
        futures = [self.thread_pool.submit(task) for task in tasks]
        return [future.result() for future in futures]
        
    def optimize_memory_usage(self, objects: List[Any]) -> None:
        """Optimize memory usage"""
        # Clear old data from objects
        for obj in objects:
            if hasattr(obj, 'clear_old_data'):
                obj.clear_old_data()
                
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance optimization report"""
        if not self.frame_times:
            return {'status': 'no_data'}
            
        return {
            'avg_frame_time': np.mean(self.frame_times),
            'min_frame_time': np.min(self.frame_times),
            'max_frame_time': np.max(self.frame_times),
            'current_fps': 1.0 / np.mean(self.frame_times),
            'target_fps': self.target_fps,
            'optimization_count': len(self.optimization_history),
            'parallel_processing': self.parallel_processing,
            'adaptive_timestep': self.adaptive_timestep
        }
        
    def cleanup(self) -> None:
        """Cleanup resources"""
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
