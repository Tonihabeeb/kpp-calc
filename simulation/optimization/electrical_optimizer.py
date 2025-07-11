"""
Electrical Optimization System for KPP Simulator
Optimizes electrical efficiency, power factor, and grid integration parameters.
"""

import numpy as np
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math

class OptimizationMode(str, Enum):
    """Optimization mode enumeration"""
    EFFICIENCY = "efficiency"
    POWER_FACTOR = "power_factor"
    GRID_STABILITY = "grid_stability"
    BALANCED = "balanced"

@dataclass
class ElectricalOptimizationConfig:
    """Configuration for electrical optimization"""
    target_power_factor: float = 0.98
    min_power_factor: float = 0.85
    max_power_factor: float = 1.0
    target_efficiency: float = 0.95
    voltage_tolerance: float = 0.05  # ±5%
    frequency_tolerance: float = 0.02  # ±2%
    optimization_interval: int = 100  # steps
    learning_rate: float = 0.01
    mode: OptimizationMode = OptimizationMode.BALANCED
    startup_ramp_rate: float = 0.25  # Exponential ramp rate during startup
    min_startup_efficiency: float = 0.80  # Minimum efficiency during startup

@dataclass
class OptimizationState:
    """State tracking for optimization process"""
    current_efficiency: float = 0.0
    current_power_factor: float = 1.0
    best_efficiency: float = 0.0
    best_power_factor: float = 1.0
    best_parameters: Dict[str, float] = field(default_factory=dict)
    iteration_count: int = 0
    improvement_history: List[Dict[str, float]] = field(default_factory=list)

class ElectricalOptimizer:
    """
    Electrical optimization system that analyzes and optimizes electrical
    performance including efficiency, power factor, and grid integration.
    """
    
    def __init__(self, config: Optional[ElectricalOptimizationConfig] = None):
        """Initialize electrical optimizer"""
        self.config = config or ElectricalOptimizationConfig()
        self.logger = logging.getLogger(__name__)
        self.state = OptimizationState()
        
        # Parameter bounds
        self.parameter_bounds = {
            'voltage_setpoint': (380.0, 420.0),  # V
            'current_limit': (80.0, 120.0),      # A
            'power_factor': (self.config.min_power_factor, self.config.max_power_factor),
            'reactive_power': (-0.3, 0.3)        # Per unit of rated power
        }
        
        # Initialize metrics tracking
        self.reset_metrics()
    
    def reset_metrics(self) -> None:
        """Reset optimization metrics"""
        self.metrics = {
            'power_output': [],
            'electrical_losses': [],
            'power_factor': [],
            'voltage': [],
            'current': [],
            'frequency': [],
            'reactive_power': []
        }
    
    def update(self, system_state: Dict[str, Any], time_step: float) -> Dict[str, Any]:
        """
        Update optimization state and generate parameter adjustments
        
        Args:
            system_state: Current system state including all relevant parameters
            time_step: Time step duration in seconds
            
        Returns:
            Dictionary of suggested parameter adjustments
        """
        try:
            # Extract current metrics
            current_power = system_state.get('power_output', 0.0)
            current_losses = system_state.get('electrical_losses', 0.0)
            current_pf = system_state.get('power_factor', 1.0)
            current_voltage = system_state.get('voltage', 400.0)
            current_frequency = system_state.get('frequency', 50.0)
            is_startup = system_state.get('is_startup', False)
            
            # Calculate current efficiency
            total_power = current_power + current_losses
            current_efficiency = current_power / total_power if total_power > 0 else 0.0
            
            # Apply exponential ramp-up during startup
            if is_startup:
                target_efficiency = self.config.min_startup_efficiency + (0.95 - self.config.min_startup_efficiency) * (
                    1 - math.exp(-self.config.startup_ramp_rate * self.state.iteration_count)
                )
                if current_efficiency < target_efficiency:
                    # Aggressive optimization during startup
                    adjustments = self._optimize_startup_parameters(system_state, time_step)
                    adjustments['efficiency'] = current_efficiency
                    return adjustments
            
            # Update state
            self.state.current_efficiency = current_efficiency
            self.state.current_power_factor = current_pf
            
            # Update best values if improved
            if current_efficiency > self.state.best_efficiency:
                self.state.best_efficiency = current_efficiency
                self.state.best_parameters.update({
                    'voltage_setpoint': current_voltage,
                    'power_factor': current_pf
                })
            
            if abs(current_pf - self.config.target_power_factor) < \
               abs(self.state.best_power_factor - self.config.target_power_factor):
                self.state.best_power_factor = current_pf
            
            # Store metrics
            self._store_metrics(system_state)
            
            # Generate optimization suggestions if needed
            if self.state.iteration_count % self.config.optimization_interval == 0:
                adjustments = self._optimize_parameters(system_state, time_step)
                adjustments['efficiency'] = current_efficiency
                return adjustments
            
            self.state.iteration_count += 1
            return {'efficiency': current_efficiency}
            
        except Exception as e:
            self.logger.error(f"Error in electrical optimization update: {e}")
            return {'efficiency': 0.0}
    
    def _store_metrics(self, state: Dict[str, Any]) -> None:
        """Store current metrics for trend analysis"""
        for metric, values in self.metrics.items():
            values.append(state.get(metric, 0.0))
            
            # Keep only recent history
            if len(values) > 1000:
                values.pop(0)
    
    def _optimize_parameters(self, current_state: Dict[str, Any], time_step: float) -> Dict[str, Any]:
        """
        Generate optimized parameter adjustments based on mode
        
        Args:
            current_state: Current system state
            time_step: Time step duration in seconds
            
        Returns:
            Dictionary of parameter adjustments
        """
        adjustments = {}
        
        if len(self.metrics['power_output']) < 10:
            return adjustments  # Need more history for optimization
        
        # Scale adjustments based on time step
        adjustment_scale = min(1.0, time_step / 0.01)  # Scale for time steps different from 10ms
        
        # Analyze recent performance
        recent_efficiency = self._calculate_recent_efficiency()
        recent_pf = np.mean(self.metrics['power_factor'][-10:])
        recent_voltage = np.mean(self.metrics['voltage'][-10:])
        
        if self.config.mode == OptimizationMode.EFFICIENCY:
            adjustments.update(self._optimize_for_efficiency(recent_efficiency))
        elif self.config.mode == OptimizationMode.POWER_FACTOR:
            adjustments.update(self._optimize_for_power_factor(recent_pf))
        elif self.config.mode == OptimizationMode.GRID_STABILITY:
            adjustments.update(self._optimize_for_grid_stability(current_state))
        else:  # BALANCED mode
            # Combine optimizations with weights
            eff_adj = self._optimize_for_efficiency(recent_efficiency)
            pf_adj = self._optimize_for_power_factor(recent_pf)
            grid_adj = self._optimize_for_grid_stability(current_state)
            
            adjustments = self._combine_adjustments([eff_adj, pf_adj, grid_adj])
        
        # Apply time step scaling to all adjustments
        for param in adjustments:
            adjustments[param] *= adjustment_scale
        
        return self._apply_bounds(adjustments)
    
    def _calculate_recent_efficiency(self) -> float:
        """Calculate average efficiency from recent metrics"""
        recent_power = np.array(self.metrics['power_output'][-10:])
        recent_losses = np.array(self.metrics['electrical_losses'][-10:])
        total_power = recent_power + recent_losses
        return np.mean(recent_power / np.where(total_power > 0, total_power, 1))
    
    def _optimize_for_efficiency(self, current_efficiency: float) -> Dict[str, float]:
        """Generate adjustments to optimize efficiency"""
        adjustments = {}
        
        if current_efficiency < self.config.target_efficiency:
            # Analyze voltage impact on efficiency
            voltage_correlation = self._calculate_correlation(
                self.metrics['voltage'],
                [p / (p + l) for p, l in zip(self.metrics['power_output'],
                                           self.metrics['electrical_losses'])]
            )
            
            # Adjust voltage setpoint based on correlation
            if abs(voltage_correlation) > 0.05:  # Lower threshold for more frequent adjustments
                direction = 1 if voltage_correlation > 0 else -1
                adjustments['voltage_setpoint'] = direction * self.config.learning_rate * 20.0  # Increased adjustment magnitude
            
            # Analyze current impact on efficiency
            current_correlation = self._calculate_correlation(
                self.metrics['current'],
                [p / (p + l) for p, l in zip(self.metrics['power_output'],
                                           self.metrics['electrical_losses'])]
            )
            
            # Adjust current limit based on correlation
            if abs(current_correlation) > 0.05:  # Lower threshold
                direction = 1 if current_correlation > 0 else -1
                adjustments['current_limit'] = direction * self.config.learning_rate * 5.0  # Increased adjustment
            
            # Analyze power factor impact
            pf_correlation = self._calculate_correlation(
                self.metrics['power_factor'],
                [p / (p + l) for p, l in zip(self.metrics['power_output'],
                                           self.metrics['electrical_losses'])]
            )
            
            # Adjust power factor based on correlation
            if abs(pf_correlation) > 0.05:  # Lower threshold
                direction = 1 if pf_correlation > 0 else -1
                adjustments['power_factor'] = direction * self.config.learning_rate * 0.05  # Increased adjustment
            
            # Analyze reactive power impact
            reactive_correlation = self._calculate_correlation(
                self.metrics['reactive_power'],
                [p / (p + l) for p, l in zip(self.metrics['power_output'],
                                           self.metrics['electrical_losses'])]
            )
            
            # Adjust reactive power based on correlation
            if abs(reactive_correlation) > 0.05:  # Lower threshold
                direction = 1 if reactive_correlation > 0 else -1
                adjustments['reactive_power'] = direction * self.config.learning_rate * 0.1  # Increased adjustment
            
            # If efficiency is far from target, make larger adjustments
            if self.config.target_efficiency - current_efficiency > 0.1:
                for param in adjustments:
                    adjustments[param] *= 2.0  # Double adjustments when far from target
        
        return adjustments
    
    def _optimize_for_power_factor(self, current_pf: float) -> Dict[str, float]:
        """Generate adjustments to optimize power factor"""
        adjustments = {}
        
        if abs(float(current_pf) - self.config.target_power_factor) > 0.02:
            # Calculate adjustment direction
            direction = 1 if float(current_pf) < self.config.target_power_factor else -1
            
            # Adjust reactive power to improve power factor
            adjustments['reactive_power'] = direction * self.config.learning_rate * 0.1
        
        return adjustments
    
    def _optimize_for_grid_stability(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Generate adjustments to optimize grid stability"""
        adjustments = {}
        
        # Get current values
        voltage = state.get('voltage', 400.0)
        frequency = state.get('frequency', 50.0)
        
        # Calculate deviations
        voltage_deviation = abs(voltage - 400.0) / 400.0
        frequency_deviation = abs(frequency - 50.0) / 50.0
        
        # More aggressive voltage correction
        if voltage_deviation > self.config.voltage_tolerance * 0.5:  # Lower threshold
            direction = 1 if voltage < 400.0 else -1
            adjustments['voltage_setpoint'] = direction * self.config.learning_rate * 30.0  # Increased adjustment
        
        # More aggressive frequency support
        if frequency_deviation > self.config.frequency_tolerance * 0.5:  # Lower threshold
            # Adjust power output to support frequency
            direction = 1 if frequency < 50.0 else -1
            adjustments['power_output'] = direction * self.config.learning_rate * 1000.0  # Increased adjustment
            
            # Adjust reactive power for voltage support
            adjustments['reactive_power'] = direction * self.config.learning_rate * 0.2
        
        # If deviations are large, make even larger adjustments
        if voltage_deviation > self.config.voltage_tolerance or \
           frequency_deviation > self.config.frequency_tolerance:
            for param in adjustments:
                adjustments[param] *= 2.0
        
        return adjustments
    
    def _combine_adjustments(self, adjustment_list: List[Dict[str, float]]) -> Dict[str, float]:
        """Combine multiple adjustment dictionaries with weights"""
        combined = {}
        weights = {
            OptimizationMode.EFFICIENCY: 0.4,
            OptimizationMode.POWER_FACTOR: 0.3,
            OptimizationMode.GRID_STABILITY: 0.3
        }
        
        # Combine all adjustments with weights
        for param in self.parameter_bounds.keys():
            weighted_sum = 0.0
            weight_sum = 0.0
            
            for adjustments, weight in zip(adjustment_list, weights.values()):
                if param in adjustments:
                    weighted_sum += adjustments[param] * weight
                    weight_sum += weight
            
            if weight_sum > 0:
                combined[param] = weighted_sum / weight_sum
        
        return combined
    
    def _apply_bounds(self, adjustments: Dict[str, float]) -> Dict[str, float]:
        """Apply bounds to parameter adjustments"""
        bounded = {}
        
        for param, value in adjustments.items():
            if param in self.parameter_bounds:
                min_val, max_val = self.parameter_bounds[param]
                bounded[param] = max(min_val, min(max_val, value))
            else:
                bounded[param] = value
        
        return bounded
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate correlation coefficient between two series"""
        if len(x) < 2 or len(y) < 2:
            return 0.0
        try:
            correlation = float(np.corrcoef(x, y)[0, 1])
            return float(correlation) if not np.isnan(correlation) else 0.0
        except Exception:
            return 0.0
    
    def _optimize_startup_parameters(self, current_state: Dict[str, Any], time_step: float) -> Dict[str, Any]:
        """
        Optimize parameters specifically for startup phase
        
        Args:
            current_state: Current system state
            time_step: Time step duration in seconds
            
        Returns:
            Dictionary of parameter adjustments
        """
        adjustments = {}
        
        # Scale adjustments based on time step
        adjustment_scale = min(1.0, time_step / 0.01)  # Scale for time steps different from 10ms
        
        # Set conservative voltage setpoint
        current_voltage = current_state.get('voltage', 400.0)
        target_voltage = 400.0  # Start at nominal voltage
        adjustments['voltage_setpoint'] = target_voltage * adjustment_scale
        
        # Set optimal power factor for startup
        current_pf = current_state.get('power_factor', 1.0)
        target_pf = self.config.target_power_factor
        adjustments['power_factor'] = target_pf * adjustment_scale
        
        # Set conservative current limit
        adjustments['current_limit'] = 90.0 * adjustment_scale  # Start at 90A
        
        # Set minimal reactive power
        adjustments['reactive_power'] = 0.0  # Start with unity power factor
        
        return adjustments
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get summary of optimization results"""
        return {
            'current_efficiency': self.state.current_efficiency,
            'current_power_factor': self.state.current_power_factor,
            'best_efficiency': self.state.best_efficiency,
            'best_power_factor': self.state.best_power_factor,
            'best_parameters': self.state.best_parameters,
            'recent_metrics': {
                'power_output': np.mean(self.metrics['power_output'][-10:])
                    if self.metrics['power_output'] else 0.0,
                'losses': np.mean(self.metrics['electrical_losses'][-10:])
                    if self.metrics['electrical_losses'] else 0.0,
                'power_factor': np.mean(self.metrics['power_factor'][-10:])
                    if self.metrics['power_factor'] else 1.0
            }
        } 