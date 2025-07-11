"""
PyChrono configuration for KPP simulator physics.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ChronoConfig:
    """Configuration for PyChrono physics engine"""
    
    # Solver settings
    solver_type: str = "SOR"  # Successive Over-Relaxation
    max_iterations: int = 100
    tolerance: float = 1e-6
    
    # Time stepping
    time_step: float = 0.02  # seconds
    max_time_step: float = 0.05
    min_time_step: float = 0.001
    
    # Physics world settings
    gravity: tuple = (0.0, -9.81, 0.0)  # m/s²
    enable_collision: bool = False
    collision_margin: float = 0.001  # meters
    
    # Performance settings
    enable_parallel: bool = True
    num_threads: int = 4
    enable_profiling: bool = False
    
    # Visualization settings (for debugging)
    enable_visualization: bool = False
    visualization_fps: int = 30
