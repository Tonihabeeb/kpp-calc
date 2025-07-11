"""
Real-time monitoring module for KPP simulation.
Handles live visualization of system state and performance metrics.
"""

import uuid
import time
import logging
import numpy as np
from numpy.typing import NDArray
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
from dataclasses import dataclass, field

@dataclass
class SystemMetrics:
    """Real-time system metrics data structure"""
    mechanical_efficiency: float = 0.0
    electrical_efficiency: float = 0.0
    total_power_output: float = 0.0
    chain_tension: float = 0.0
    floater_positions: List[float] = field(default_factory=list)
    system_losses: Dict[str, float] = field(default_factory=dict)
    grid_metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

class RealTimeMonitor:
    """Monitors and streams real-time system state for visualization"""
    
    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self.metrics_buffer = deque(maxlen=buffer_size)
        self.alert_callbacks: Dict[str, Callable] = {}
        self.alert_thresholds = {
            'chain_speed_max': 2.0,  # m/s
            'power_min': 100.0,      # W
            'efficiency_min': 0.5,   # 50%
            'chain_tension_max': 50000.0  # N
        }
        
        # Initialize current state
        self.current_state = {
            'timestamp': time.time(),
            'chain_speed': 0.0,
            'generator_power': 0.0,
            'compressor_power': 0.0,
            'net_power': 0.0,
            'chain_tension': 0.0,
            'floater_positions': [],
            'enhancements': {
                'h1_active': False,
                'h2_active': False,
                'h3_active': False
            },
            'alerts': [],
            'system_health': 1.0
        }
        
        # Setup logging
        self.logger = logging.getLogger('RealTimeMonitor')
        self.logger.setLevel(logging.INFO)
        
    def register_alert_callback(self, alert_type: str, callback: Callable):
        """Register callback for specific alert types"""
        self.alert_callbacks[alert_type] = callback
        
    def update_state(self, time: float, chain_speed: float, 
                    generator_power: float, compressor_power: float,
                    chain_tension: float, floater_positions: List[Dict],
                    h1: bool, h2: bool, h3: bool) -> str:
        """
        Update current state and return JSON string for streaming
        """
        # Calculate derived metrics
        net_power = generator_power - compressor_power
        efficiency = abs(generator_power / compressor_power) if compressor_power > 0 else 0.0
        
        # Update state
        self.current_state.update({
            'timestamp': time,
            'chain_speed': round(chain_speed, 3),
            'generator_power': round(generator_power, 2),
            'compressor_power': round(compressor_power, 2),
            'net_power': round(net_power, 2),
            'chain_tension': round(chain_tension, 2),
            'floater_positions': floater_positions,
            'enhancements': {
                'h1_active': h1,
                'h2_active': h2,
                'h3_active': h3
            }
        })
        
        # Check for alerts
        alerts = self.check_alerts(chain_speed, net_power, efficiency, chain_tension)
        self.current_state['alerts'] = alerts
        
        # Calculate system health score
        health_score = self.calculate_health_score(chain_speed, net_power, 
                                                 efficiency, chain_tension)
        self.current_state['system_health'] = health_score
        
        # Store metrics for trending
        metrics = SystemMetrics(
            mechanical_efficiency=efficiency,
            electrical_efficiency=generator_power / (compressor_power + 1e-6),
            total_power_output=net_power,
            chain_tension=chain_tension,
            floater_positions=[p['position'] for p in floater_positions],
            system_losses={
                'drag': abs(generator_power - net_power),
                'mechanical': abs(compressor_power * (1 - efficiency))
            },
            grid_metrics={
                'power_factor': 0.95,  # Assumed constant for now
                'frequency': 50.0      # Grid frequency
            },
            timestamp=time
        )
        self.metrics_buffer.append(metrics)
        
        # Log significant events
        if alerts:
            self.logger.warning(f"Alerts triggered: {alerts}")
        if net_power > 1000:  # Log when power exceeds 1kW
            self.logger.info(f"High power output: {net_power:.2f}W")
            
        return self.get_monitoring_data()
    
    def check_alerts(self, chain_speed: float, power: float, 
                    efficiency: float, tension: float) -> List[str]:
        """Check for alert conditions"""
        alerts = []
        
        if chain_speed > self.alert_thresholds['chain_speed_max']:
            alerts.append('chain_speed_high')
            if 'chain_speed_high' in self.alert_callbacks:
                self.alert_callbacks['chain_speed_high'](chain_speed)
                
        if power < self.alert_thresholds['power_min']:
            alerts.append('power_low')
            if 'power_low' in self.alert_callbacks:
                self.alert_callbacks['power_low'](power)
                
        if efficiency < self.alert_thresholds['efficiency_min']:
            alerts.append('efficiency_low')
            if 'efficiency_low' in self.alert_callbacks:
                self.alert_callbacks['efficiency_low'](efficiency)
                
        if tension > self.alert_thresholds['chain_tension_max']:
            alerts.append('tension_high')
            if 'tension_high' in self.alert_callbacks:
                self.alert_callbacks['tension_high'](tension)
                
        return alerts
    
    def calculate_health_score(self, chain_speed: float, power: float,
                             efficiency: float, tension: float) -> float:
        """Calculate overall system health score (0-1)"""
        speed_score = max(0, 1 - chain_speed / self.alert_thresholds['chain_speed_max'])
        power_score = min(1, power / self.alert_thresholds['power_min'])
        efficiency_score = min(1, efficiency / self.alert_thresholds['efficiency_min'])
        tension_score = max(0, 1 - tension / self.alert_thresholds['chain_tension_max'])
        
        scores = [speed_score, power_score, efficiency_score, tension_score]
        return float(np.mean(scores))
    
    def get_monitoring_data(self) -> str:
        """Get current monitoring data as JSON string"""
        import json
        return json.dumps(self.current_state)
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics for display"""
        return {
            'chain_speed_mps': self.current_state['chain_speed'],
            'power_output_kw': self.current_state['generator_power'] / 1000,
            'power_input_kw': self.current_state['compressor_power'] / 1000,
            'net_power_kw': self.current_state['net_power'] / 1000,
            'efficiency': (self.current_state['generator_power'] / 
                         self.current_state['compressor_power']
                         if self.current_state['compressor_power'] > 0 else 0.0),
            'system_health': self.current_state['system_health'],
            'active_alerts': self.current_state['alerts']
        }
    
    def get_enhancement_status(self) -> Dict:
        """Get current enhancement status"""
        return self.current_state['enhancements']
    
    def get_floater_positions(self) -> List[Dict]:
        """Get current floater positions for visualization"""
        return self.current_state['floater_positions']
    
    def get_trend_data(self, metric: str, window: int = 100) -> List[float]:
        """Get trend data for specified metric"""
        if not self.metrics_buffer:
            return []
            
        if metric == 'power':
            return [m.total_power_output for m in list(self.metrics_buffer)[-window:]]
        elif metric == 'efficiency':
            return [m.mechanical_efficiency for m in list(self.metrics_buffer)[-window:]]
        elif metric == 'tension':
            return [m.chain_tension for m in list(self.metrics_buffer)[-window:]]
        else:
            return []

