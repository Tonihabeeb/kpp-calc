"""
Mechanical Optimization System for KPP Simulator
Analyzes and optimizes mechanical efficiency through parameter tuning
and real-time adjustments.
"""

import numpy as np
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import math

@dataclass
class MechanicalOptimizationConfig:
    """Configuration for mechanical optimization"""
    min_chain_tension: float = 35000.0  # N
    max_chain_tension: float = 42000.0  # N
    optimal_floater_spacing: float = 2.0  # m
    spacing_tolerance: float = 0.1  # m
    min_floater_volume: float = 0.3  # m³
    max_floater_volume: float = 0.5  # m³
    optimal_air_fill: float = 0.4  # ratio
    air_fill_tolerance: float = 0.05
    learning_rate: float = 0.01
    optimization_interval: int = 100  # steps
    startup_ramp_rate: float = 0.2  # Exponential ramp rate during startup
    min_startup_efficiency: float = 0.75  # Minimum efficiency during startup

@dataclass
class OptimizationState:
    """State tracking for optimization process"""
    current_efficiency: float = 0.0
    best_efficiency: float = 0.0
    best_parameters: Dict[str, float] = field(default_factory=dict)
    iteration_count: int = 0
    improvement_history: List[float] = field(default_factory=list)
    parameter_history: List[Dict[str, float]] = field(default_factory=list)

class MechanicalOptimizer:
    """
    Mechanical optimization system that analyzes system performance and
    suggests parameter adjustments to improve efficiency.
    """
    
    def __init__(self, config: Optional[MechanicalOptimizationConfig] = None):
        """
        Initialize the mechanical optimizer
        
        Args:
            config: Optional configuration parameters
        """
        self.config = config or MechanicalOptimizationConfig()
        self.logger = logging.getLogger(__name__)
        
        # Validate and fix configuration
        self._validate_config()
        
        # Initialize state
        self.state = OptimizationState()
        
        # Initialize metrics storage
        self.metrics = {
            'power_output': [],
            'mechanical_losses': [],
            'chain_tension': [],
            'floater_positions': [],
            'air_fill_levels': []
        }
        
        # Parameter bounds
        self.parameter_bounds = {
            'chain_tension': (self.config.min_chain_tension, self.config.max_chain_tension),
            'floater_volume': (self.config.min_floater_volume, self.config.max_floater_volume),
            'air_fill_level': (
                max(0.0, self.config.optimal_air_fill - self.config.air_fill_tolerance),
                min(1.0, self.config.optimal_air_fill + self.config.air_fill_tolerance)
            )
        }
    
    def _validate_config(self) -> None:
        """Validate and fix configuration parameters"""
        try:
            # Fix chain tension bounds
            if self.config.min_chain_tension > self.config.max_chain_tension:
                self.logger.warning("Invalid chain tension bounds, swapping min/max")
                self.config.min_chain_tension, self.config.max_chain_tension = (
                    self.config.max_chain_tension, self.config.min_chain_tension
                )
            
            # Fix floater volume bounds
            if self.config.min_floater_volume > self.config.max_floater_volume:
                self.logger.warning("Invalid floater volume bounds, swapping min/max")
                self.config.min_floater_volume, self.config.max_floater_volume = (
                    self.config.max_floater_volume, self.config.min_floater_volume
                )
            
            # Validate air fill parameters
            if self.config.optimal_air_fill < 0.0 or self.config.optimal_air_fill > 1.0:
                self.logger.warning("Invalid optimal air fill, clamping to [0, 1]")
                self.config.optimal_air_fill = max(0.0, min(1.0, self.config.optimal_air_fill))
            
            if self.config.air_fill_tolerance < 0.0:
                self.logger.warning("Invalid air fill tolerance, using absolute value")
                self.config.air_fill_tolerance = abs(self.config.air_fill_tolerance)
            
            # Validate learning rate
            if self.config.learning_rate <= 0.0:
                self.logger.warning("Invalid learning rate, setting to default")
                self.config.learning_rate = 0.01
            
            # Validate startup parameters
            if self.config.startup_ramp_rate <= 0.0:
                self.logger.warning("Invalid startup ramp rate, setting to default")
                self.config.startup_ramp_rate = 0.2
            
            if self.config.min_startup_efficiency < 0.0 or self.config.min_startup_efficiency > 1.0:
                self.logger.warning("Invalid min startup efficiency, clamping to [0, 1]")
                self.config.min_startup_efficiency = max(0.0, min(1.0, self.config.min_startup_efficiency))
                
        except Exception as e:
            self.logger.error(f"Error validating config: {e}")
            # Use default config if validation fails
            self.config = MechanicalOptimizationConfig()

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Safely convert value to float"""
        try:
            result = float(value)
            if math.isfinite(result):
                return result
            return default
        except (TypeError, ValueError):
            return default

    def _get_state_value(self, state: Dict[str, Any], key: str, default: float) -> float:
        """Safely get state value"""
        value = state.get(key, default)
        return self._safe_float(value, default)

    def update(self, system_state: Dict[str, Any], time_step: float) -> Dict[str, Any]:
        """
        Update optimizer state and generate parameter adjustments
        
        Args:
            system_state: Current system state
            time_step: Time step duration in seconds
            
        Returns:
            Dictionary of parameter adjustments
        """
        try:
            # Validate time step
            time_step = max(0.0, self._safe_float(time_step, 0.01))
            
            # Check if in startup phase
            is_startup = self.state.iteration_count < 100  # First 100 iterations considered startup
            
            # Get current state with safe value extraction
            current_power = self._get_state_value(system_state, 'power_output', 0.0)
            current_losses = self._get_state_value(system_state, 'mechanical_losses', 0.0)
            current_tension = self._get_state_value(
                system_state, 'chain_tension', self.config.min_chain_tension
            )
            
            # Calculate current efficiency
            total_power = current_power + current_losses
            current_efficiency = current_power / total_power if total_power > 0 else 0.0
            
            # Apply exponential ramp-up during startup
            if is_startup:
                # Calculate target efficiency based on iteration
                progress = min(1.0, self.state.iteration_count / 100.0)
                base_target = self.config.min_startup_efficiency
                max_target = 0.95
                
                # Use sigmoid function for smoother transition
                target_efficiency = base_target + (max_target - base_target) * (
                    1 / (1 + math.exp(-10 * (progress - 0.5)))
                )
                
                if current_efficiency < target_efficiency:
                    # Get startup optimizations
                    adjustments = self._optimize_startup_parameters(system_state, time_step)
                    
                    # Add aggressive efficiency improvements
                    if current_efficiency < 0.8 * target_efficiency:
                        # Analyze recent performance if available
                        if len(self.metrics['power_output']) >= 5:
                            recent_power = np.array(self.metrics['power_output'][-5:])
                            recent_losses = np.array(self.metrics['mechanical_losses'][-5:])
                            
                            # Check if efficiency is improving
                            recent_efficiencies = recent_power / (recent_power + recent_losses)
                            if not np.all(np.diff(recent_efficiencies) > 0):
                                # Efficiency not consistently improving, try alternative parameters
                                adjustments.update(self._optimize_alternative_parameters(system_state))
                    
                    adjustments['efficiency'] = current_efficiency
                    adjustments['target_efficiency'] = target_efficiency
                    return adjustments
            
            # Update state
            self.state.current_efficiency = current_efficiency
            if current_efficiency > self.state.best_efficiency:
                self.state.best_efficiency = current_efficiency
                self.state.best_parameters = {
                    'chain_tension': current_tension,
                    'floater_volume': self._get_state_value(system_state, 'floater_volume', 0.4),
                    'air_fill_level': self._get_state_value(system_state, 'air_fill_level', 0.4)
                }
            
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
            self.logger.error(f"Error in mechanical optimizer update: {e}")
            return {'efficiency': 0.0}
    
    def _optimize_parameters(self, current_state: Dict[str, Any], time_step: float) -> Dict[str, Any]:
        """
        Generate optimized parameter adjustments
        
        Args:
            current_state: Current system state
            time_step: Time step duration in seconds
            
        Returns:
            Dictionary of parameter adjustments
        """
        adjustments = {}
        
        # Analyze recent performance trends
        if len(self.metrics['power_output']) >= 10:
            recent_power = np.array(self.metrics['power_output'][-10:])
            recent_losses = np.array(self.metrics['mechanical_losses'][-10:])
            recent_tension = np.array(self.metrics['chain_tension'][-10:])
            
            # Scale adjustments based on time step
            adjustment_scale = min(1.0, time_step / 0.01)  # Scale for time steps different from 10ms
            
            # Optimize chain tension
            if np.mean(recent_losses) > 0.15 * np.mean(recent_power):
                # Too much loss, adjust tension
                optimal_tension = self._optimize_chain_tension(
                    recent_tension,
                    recent_power,
                    recent_losses
                )
                adjustments['chain_tension'] = optimal_tension * adjustment_scale
            
            # Optimize floater parameters
            current_volume = current_state.get('floater_volume', 0.4)
            current_air_fill = current_state.get('air_fill_level', 0.4)
            
            if self.state.current_efficiency < 0.85:  # Below target efficiency
                optimal_volume = self._optimize_floater_volume(
                    current_volume,
                    recent_power,
                    recent_losses
                )
                optimal_air_fill = self._optimize_air_fill(
                    current_air_fill,
                    recent_power,
                    recent_losses
                )
                
                adjustments['floater_volume'] = optimal_volume * adjustment_scale
                adjustments['air_fill_level'] = optimal_air_fill * adjustment_scale
        
        return adjustments
    
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
        
        # Start with conservative chain tension
        current_tension = current_state.get('chain_tension', self.config.min_chain_tension)
        target_tension = self.config.min_chain_tension + (
            (self.config.max_chain_tension - self.config.min_chain_tension) * 0.6
        )
        adjustments['chain_tension'] = target_tension * adjustment_scale
        
        # Optimize floater volume for startup
        current_volume = current_state.get('floater_volume', 0.4)
        target_volume = self.config.min_floater_volume + (
            (self.config.max_floater_volume - self.config.min_floater_volume) * 0.7
        )
        adjustments['floater_volume'] = target_volume * adjustment_scale
        
        # Set optimal air fill for startup
        adjustments['air_fill_level'] = self.config.optimal_air_fill * adjustment_scale
        
        return adjustments
    
    def _optimize_chain_tension(self, tensions: np.ndarray, power: np.ndarray,
                              losses: np.ndarray) -> float:
        """Optimize chain tension based on recent performance"""
        # Calculate efficiency for each tension value
        efficiencies = power / (power + losses)
        
        # Find tension with best efficiency
        best_idx = np.argmax(efficiencies)
        best_tension = tensions[best_idx]
        
        # Apply bounds and learning rate
        current_tension = tensions[-1]
        delta = (best_tension - current_tension) * self.config.learning_rate
        
        return np.clip(
            current_tension + delta,
            self.parameter_bounds['chain_tension'][0],
            self.parameter_bounds['chain_tension'][1]
        )
    
    def _optimize_floater_volume(self, current_volume: float, power: np.ndarray,
                               losses: np.ndarray) -> float:
        """Optimize floater volume based on performance metrics"""
        # Simple gradient descent
        efficiency = power[-1] / (power[-1] + losses[-1])
        
        if efficiency < 0.85:
            # Try increasing volume if efficiency is low
            delta = 0.01 * self.config.learning_rate
        else:
            # Try decreasing volume if efficiency is good
            delta = -0.01 * self.config.learning_rate
        
        return np.clip(
            current_volume + delta,
            self.parameter_bounds['floater_volume'][0],
            self.parameter_bounds['floater_volume'][1]
        )
    
    def _optimize_air_fill(self, current_air_fill: float, power: np.ndarray,
                          losses: np.ndarray) -> float:
        """Optimize air fill level based on performance metrics"""
        # Calculate optimal air fill based on power and losses
        efficiency = power[-1] / (power[-1] + losses[-1])
        
        if efficiency < 0.85:
            # Adjust towards optimal air fill
            target = self.config.optimal_air_fill
            delta = (target - current_air_fill) * self.config.learning_rate
        else:
            # Fine-tune around current value
            delta = 0.0
        
        return np.clip(
            current_air_fill + delta,
            self.parameter_bounds['air_fill_level'][0],
            self.parameter_bounds['air_fill_level'][1]
        )
    
    def _optimize_alternative_parameters(self, system_state: Dict[str, Any]) -> Dict[str, float]:
        """
        Try alternative parameter combinations when normal optimization is not effective
        
        Args:
            system_state: Current system state
            
        Returns:
            Dictionary of alternative parameter adjustments
        """
        adjustments = {}
        
        # Try different chain tension ranges
        current_tension = system_state.get('chain_tension', self.config.min_chain_tension)
        if current_tension < (self.config.min_chain_tension + self.config.max_chain_tension) / 2:
            # Current tension is in lower range, try higher range
            adjustments['chain_tension'] = self.config.min_chain_tension + (
                (self.config.max_chain_tension - self.config.min_chain_tension) * 0.7
            )
        else:
            # Current tension is in higher range, try lower range
            adjustments['chain_tension'] = self.config.min_chain_tension + (
                (self.config.max_chain_tension - self.config.min_chain_tension) * 0.3
            )
        
        # Try different floater configurations
        current_volume = system_state.get('floater_volume', 0.4)
        if current_volume < (self.config.min_floater_volume + self.config.max_floater_volume) / 2:
            # Current volume is in lower range, try higher range
            adjustments['floater_volume'] = self.config.min_floater_volume + (
                (self.config.max_floater_volume - self.config.min_floater_volume) * 0.8
            )
            # Use lower air fill with larger volume
            adjustments['air_fill_level'] = self.config.optimal_air_fill * 0.8
        else:
            # Current volume is in higher range, try lower range
            adjustments['floater_volume'] = self.config.min_floater_volume + (
                (self.config.max_floater_volume - self.config.min_floater_volume) * 0.4
            )
            # Use higher air fill with smaller volume
            adjustments['air_fill_level'] = self.config.optimal_air_fill * 1.2
        
        return adjustments
    
    def _store_metrics(self, system_state: Dict[str, Any]) -> None:
        """
        Store current metrics for trend analysis
        
        Args:
            system_state: Current system state
        """
        try:
            metrics = {
                'power_output': self._get_state_value(system_state, 'power_output', 0.0),
                'mechanical_losses': self._get_state_value(system_state, 'mechanical_losses', 0.0),
                'chain_tension': self._get_state_value(system_state, 'chain_tension', self.config.min_chain_tension),
                'floater_positions': system_state.get('floater_positions', []),
                'air_fill_levels': self._get_state_value(system_state, 'air_fill_level', self.config.optimal_air_fill)
            }
            
            # Validate floater positions
            if not isinstance(metrics['floater_positions'], list):
                metrics['floater_positions'] = []
            
            # Store valid metrics
            for key, value in metrics.items():
                if key == 'floater_positions':
                    # Store only valid numeric positions
                    valid_positions = []
                    for pos in value:
                        try:
                            pos_float = float(pos)
                            if math.isfinite(pos_float):
                                valid_positions.append(pos_float)
                        except (TypeError, ValueError):
                            continue
                    self.metrics[key].append(valid_positions)
                else:
                    # Store numeric values
                    self.metrics[key].append(value)
                
                # Keep only recent history
                if len(self.metrics[key]) > 1000:
                    self.metrics[key].pop(0)
            
            # Update improvement history
            self.state.improvement_history.append(self.state.current_efficiency)
            if len(self.state.improvement_history) > 100:
                self.state.improvement_history.pop(0)
            
            # Update parameter history
            current_params = {
                'chain_tension': metrics['chain_tension'],
                'floater_volume': self._get_state_value(system_state, 'floater_volume', 0.4),
                'air_fill_level': metrics['air_fill_levels']
            }
            self.state.parameter_history.append(current_params)
            if len(self.state.parameter_history) > 100:
                self.state.parameter_history.pop(0)
                
        except Exception as e:
            self.logger.error(f"Error storing metrics: {e}")

    def get_optimization_summary(self) -> Dict[str, Any]:
        """
        Get summary of optimization results
        
        Returns:
            Dictionary containing optimization summary
        """
        try:
            # Calculate recent performance metrics
            recent_power = np.array(self.metrics['power_output'][-10:])
            recent_losses = np.array(self.metrics['mechanical_losses'][-10:])
            recent_efficiency = np.mean(
                recent_power / np.where(recent_power + recent_losses > 0, recent_power + recent_losses, 1)
            )
            
            # Calculate efficiency trend
            efficiency_trend = 0.0
            if len(self.state.improvement_history) >= 2:
                recent_efficiencies = np.array(self.state.improvement_history[-10:])
                efficiency_trend = np.mean(np.diff(recent_efficiencies))
            
            # Get parameter trends
            parameter_trends = {}
            if len(self.state.parameter_history) >= 2:
                for param in ['chain_tension', 'floater_volume', 'air_fill_level']:
                    values = [p[param] for p in self.state.parameter_history[-10:]]
                    parameter_trends[param] = np.mean(np.diff(values))
            
            return {
                'current_efficiency': self.state.current_efficiency,
                'best_efficiency': self.state.best_efficiency,
                'recent_efficiency': float(recent_efficiency),
                'efficiency_trend': float(efficiency_trend),
                'best_parameters': self.state.best_parameters,
                'parameter_trends': parameter_trends,
                'recent_power_output': float(np.mean(recent_power)),
                'recent_losses': float(np.mean(recent_losses)),
                'iteration_count': self.state.iteration_count
            }
            
        except Exception as e:
            self.logger.error(f"Error generating optimization summary: {e}")
            return {
                'current_efficiency': 0.0,
                'best_efficiency': 0.0,
                'recent_efficiency': 0.0,
                'efficiency_trend': 0.0,
                'best_parameters': {},
                'parameter_trends': {},
                'recent_power_output': 0.0,
                'recent_losses': 0.0,
                'iteration_count': self.state.iteration_count
            } 