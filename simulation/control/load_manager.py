import numpy as np
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import deque
from enum import Enum

"""
Load Management System for KPP Electrical System
Implements dynamic electrical load adjustment for optimal efficiency and grid stability.
"""

class LoadState(str, Enum):
    """Load manager state enumeration"""
    IDLE = "idle"
    FORECASTING = "forecasting"
    RESPONDING = "responding"
    OPTIMIZING = "optimizing"
    FAULT = "fault"

class LoadType(str, Enum):
    """Load type enumeration"""
    BASE = "base"
    PEAK = "peak"
    VARIABLE = "variable"
    CRITICAL = "critical"

class DemandResponseMode(str, Enum):
    """Demand response mode enumeration"""
    NORMAL = "normal"
    CURTAILMENT = "curtailment"
    PEAK_SHAVING = "peak_shaving"
    EMERGENCY = "emergency"

@dataclass
class LoadProfile:
    """Load profile data structure"""
    timestamp: float
    load_type: LoadType
    power_demand: float  # W
    priority: int  # 1-10, higher is more critical
    duration: float  # seconds
    flexibility: float  # 0-1, how flexible the load is

@dataclass
class LoadConfig:
    """Load manager configuration"""
    max_load: float = 50000.0  # W (50 kW)
    min_load: float = 1000.0  # W (1 kW)
    forecast_horizon: float = 3600.0  # seconds (1 hour)
    response_time_target: float = 5.0  # seconds
    optimization_enabled: bool = True
    demand_response_enabled: bool = True

class LoadManager:
    """
    Advanced load management system for KPP electrical system.
    Handles load forecasting, demand response, and optimization.
    """
    
    def __init__(self, config: Optional[LoadConfig] = None):
        """
        Initialize the load manager.
        
        Args:
            config: Load manager configuration
        """
        self.config = config or LoadConfig()
        self.logger = logging.getLogger(__name__)
        
        # System state
        self.load_state = LoadState.IDLE
        self.current_load = 0.0  # W
        self.target_load = 0.0  # W
        self.demand_response_mode = DemandResponseMode.NORMAL
        
        # Performance tracking
        self.performance_metrics = {
            'total_energy_managed': 0.0,  # kWh
            'peak_shaving_savings': 0.0,  # kWh
            'load_forecast_accuracy': 0.0,  # %
            'demand_response_events': 0,
            'optimization_savings': 0.0,  # kWh
            'operating_hours': 0.0,  # hours
            'load_errors': 0
        }
        
        # Load profiles
        self.load_profiles: List[LoadProfile] = []
        self.active_loads: Dict[str, LoadProfile] = {}
        self.load_history: deque = deque(maxlen=1000)
        
        # Forecasting
        self.forecast_horizon = self.config.forecast_horizon
        self.forecast_data: List[Dict[str, Any]] = []
        self.forecast_accuracy = 0.0
        
        # Demand response
        self.demand_response_active = False
        self.curtailment_target = 0.0
        self.peak_shaving_target = 0.0
        self.response_history: List[Dict[str, Any]] = []
        
        # Optimization
        self.optimization_active = False
        self.optimization_target = 0.0
        self.optimization_history: List[Dict[str, Any]] = []
        
        self.logger.info("Load manager initialized")
    
    def start_load_management(self) -> bool:
        """
        Start load management.
        
        Returns:
            True if load management started successfully
        """
        try:
            if self.load_state != LoadState.IDLE:
                self.logger.warning("Cannot start load management in state: %s", self.load_state)
                return False
            
            # Initialize load state
            self.load_state = LoadState.FORECASTING
            
            # Start load forecasting
            self._start_load_forecasting()
            
            self.logger.info("Load management started")
            return True
            
        except Exception as e:
            self.logger.error("Error starting load management: %s", e)
            self._handle_fault("load_start_error", str(e))
            return False
    
    def stop_load_management(self) -> bool:
        """
        Stop load management.
        
        Returns:
            True if load management stopped successfully
        """
        try:
            if self.load_state == LoadState.IDLE:
                self.logger.warning("Load management already stopped")
                return False
            
            # Stop optimization if active
            if self.optimization_active:
                self._stop_optimization()
            
            # Stop demand response if active
            if self.demand_response_active:
                self._stop_demand_response()
            
            # Reset load state
            self.load_state = LoadState.IDLE
            self.current_load = 0.0
            self.target_load = 0.0
            
            self.logger.info("Load management stopped")
            return True
            
        except Exception as e:
            self.logger.error("Error stopping load management: %s", e)
            self._handle_fault("load_stop_error", str(e))
            return False
    
    def update_load_state(self, current_load: float, available_power: float) -> bool:
        """
        Update load state based on current conditions.
        
        Args:
            current_load: Current load demand (W)
            available_power: Available power (W)
            
        Returns:
            True if update successful
        """
        try:
            if self.load_state == LoadState.IDLE:
                return False
            
            # Update current state
            self.current_load = current_load
            
            # Update load history
            self._update_load_history(current_load, available_power)
            
            # Execute load forecasting
            if self.load_state == LoadState.FORECASTING:
                self._execute_load_forecasting()
            
            # Execute demand response if needed
            if self.demand_response_active:
                self._execute_demand_response(available_power)
            
            # Execute optimization if active
            if self.optimization_active:
                self._execute_load_optimization()
            
            # Update performance metrics
            self._update_performance_metrics()
            
            return True
            
        except Exception as e:
            self.logger.error("Error updating load state: %s", e)
            self._handle_fault("state_update_error", str(e))
            return False
    
    def add_load_profile(self, load_type: LoadType, power_demand: float, 
                        priority: int, duration: float, flexibility: float) -> str:
        """
        Add a new load profile.
        
        Args:
            load_type: Type of load
            power_demand: Power demand (W)
            priority: Load priority (1-10)
            duration: Load duration (seconds)
            flexibility: Load flexibility (0-1)
            
        Returns:
            Load profile ID
        """
        try:
            # Validate parameters
            if power_demand < 0 or power_demand > self.config.max_load:
                self.logger.error("Invalid power demand: %.1f W", power_demand)
                return ""
            
            if priority < 1 or priority > 10:
                self.logger.error("Invalid priority: %d", priority)
                return ""
            
            if duration <= 0:
                self.logger.error("Invalid duration: %.1f s", duration)
                return ""
            
            if flexibility < 0 or flexibility > 1:
                self.logger.error("Invalid flexibility: %.2f", flexibility)
                return ""
            
            # Create load profile
            profile = LoadProfile(
                timestamp=time.time(),
                load_type=load_type,
                power_demand=power_demand,
                priority=priority,
                duration=duration,
                flexibility=flexibility
            )
            
            # Generate unique ID
            profile_id = f"load_{int(time.time() * 1000)}"
            
            # Add to active loads
            self.active_loads[profile_id] = profile
            self.load_profiles.append(profile)
            
            self.logger.info("Load profile added: %s (%.1f W, priority %d)", 
                           profile_id, power_demand, priority)
            
            return profile_id
            
        except Exception as e:
            self.logger.error("Error adding load profile: %s", e)
            return ""
    
    def remove_load_profile(self, profile_id: str) -> bool:
        """
        Remove a load profile.
        
        Args:
            profile_id: Load profile ID
            
        Returns:
            True if profile removed successfully
        """
        try:
            if profile_id not in self.active_loads:
                self.logger.warning("Load profile not found: %s", profile_id)
                return False
            
            # Remove from active loads
            profile = self.active_loads.pop(profile_id)
            
            # Remove from profiles list
            if profile in self.load_profiles:
                self.load_profiles.remove(profile)
            
            self.logger.info("Load profile removed: %s", profile_id)
            return True
            
        except Exception as e:
            self.logger.error("Error removing load profile: %s", e)
            return False
    
    def start_demand_response(self, mode: DemandResponseMode, target: float) -> bool:
        """
        Start demand response.
        
        Args:
            mode: Demand response mode
            target: Target load reduction (W)
            
        Returns:
            True if demand response started successfully
        """
        try:
            if not self.config.demand_response_enabled:
                self.logger.warning("Demand response not enabled")
                return False
            
            if self.demand_response_active:
                self.logger.warning("Demand response already active")
                return False
            
            # Validate target
            if target < 0 or target > self.current_load:
                self.logger.error("Invalid demand response target: %.1f W", target)
                return False
            
            # Set demand response parameters
            self.demand_response_mode = mode
            self.demand_response_active = True
            
            if mode == DemandResponseMode.CURTAILMENT:
                self.curtailment_target = target
            elif mode == DemandResponseMode.PEAK_SHAVING:
                self.peak_shaving_target = target
            
            # Update load state
            self.load_state = LoadState.RESPONDING
            
            # Record demand response start
            self._record_demand_response_event("start", mode, target)
            
            self.logger.info("Demand response started: %s mode, target %.1f W", 
                           mode.value, target)
            return True
            
        except Exception as e:
            self.logger.error("Error starting demand response: %s", e)
            return False
    
    def _stop_demand_response(self) -> None:
        """Stop demand response."""
        try:
            self.demand_response_active = False
            self.curtailment_target = 0.0
            self.peak_shaving_target = 0.0
            
            if self.load_state == LoadState.RESPONDING:
                self.load_state = LoadState.FORECASTING
            
            # Record demand response stop
            self._record_demand_response_event("stop", self.demand_response_mode, 0.0)
            
            self.logger.info("Demand response stopped")
            
        except Exception as e:
            self.logger.error("Error stopping demand response: %s", e)
    
    def _start_load_forecasting(self) -> None:
        """Start load forecasting."""
        try:
            # Initialize forecasting parameters
            self.forecast_data.clear()
            self.forecast_accuracy = 0.0
            
            # Create initial forecast
            self._create_load_forecast()
            
            self.logger.info("Load forecasting started")
            
        except Exception as e:
            self.logger.error("Error starting load forecasting: %s", e)
    
    def _execute_load_forecasting(self) -> None:
        """Execute load forecasting algorithm."""
        try:
            # Simplified forecasting algorithm
            # In practice, this would use advanced time series analysis
            
            # Analyze load patterns
            load_patterns = self._analyze_load_patterns()
            
            # Generate forecast
            forecast = self._generate_load_forecast(load_patterns)
            
            # Update forecast data
            forecast_record = {
                'timestamp': time.time(),
                'forecast': forecast,
                'patterns': load_patterns,
                'accuracy': self.forecast_accuracy
            }
            
            self.forecast_data.append(forecast_record)
            
            # Update forecast accuracy
            self._update_forecast_accuracy()
            
        except Exception as e:
            self.logger.error("Error executing load forecasting: %s", e)
    
    def _analyze_load_patterns(self) -> Dict[str, Any]:
        """
        Analyze load patterns from history.
        
        Returns:
            Load pattern analysis
        """
        try:
            if len(self.load_history) < 10:
                return {'pattern': 'insufficient_data', 'trend': 0.0}
            
            # Extract load values
            loads = [record['load'] for record in self.load_history]
            
            # Calculate basic statistics
            avg_load = sum(loads) / len(loads)
            max_load = max(loads)
            min_load = min(loads)
            
            # Calculate trend (simplified)
            if len(loads) >= 2:
                trend = (loads[-1] - loads[0]) / len(loads)
            else:
                trend = 0.0
            
            # Identify pattern type
            if max_load - min_load < avg_load * 0.1:
                pattern = 'stable'
            elif trend > avg_load * 0.01:
                pattern = 'increasing'
            elif trend < -avg_load * 0.01:
                pattern = 'decreasing'
            else:
                pattern = 'variable'
            
            return {
                'pattern': pattern,
                'trend': trend,
                'avg_load': avg_load,
                'max_load': max_load,
                'min_load': min_load,
                'volatility': (max_load - min_load) / avg_load
            }
            
        except Exception as e:
            self.logger.error("Error analyzing load patterns: %s", e)
            return {'pattern': 'error', 'trend': 0.0}
    
    def _generate_load_forecast(self, patterns: Dict[str, Any]) -> List[float]:
        """
        Generate load forecast based on patterns.
        
        Args:
            patterns: Load pattern analysis
            
        Returns:
            List of forecasted loads
        """
        try:
            forecast = []
            current_load = self.current_load
            
            # Generate forecast for next hour (3600 seconds)
            forecast_steps = int(self.forecast_horizon / 60)  # 1-minute intervals
            
            for i in range(forecast_steps):
                # Apply trend
                trend_factor = 1.0 + patterns.get('trend', 0.0) * i / forecast_steps
                
                # Add some variability
                variability = np.random.normal(0, patterns.get('volatility', 0.1) * 0.1)
                
                # Calculate forecasted load
                forecasted_load = current_load * trend_factor * (1 + variability)
                
                # Apply constraints
                forecasted_load = max(self.config.min_load, 
                                    min(self.config.max_load, forecasted_load))
                
                forecast.append(forecasted_load)
            
            return forecast
            
        except Exception as e:
            self.logger.error("Error generating load forecast: %s", e)
            return [self.current_load] * 60  # Return current load for all steps
    
    def _execute_demand_response(self, available_power: float) -> None:
        """
        Execute demand response.
        
        Args:
            available_power: Available power (W)
        """
        try:
            if not self.demand_response_active:
                return
            
            # Calculate load reduction needed
            if self.demand_response_mode == DemandResponseMode.CURTAILMENT:
                target_reduction = self.curtailment_target
            elif self.demand_response_mode == DemandResponseMode.PEAK_SHAVING:
                target_reduction = self.peak_shaving_target
            else:
                return
            
            # Identify loads to curtail
            curtailable_loads = self._identify_curtailable_loads()
            
            # Execute load curtailment
            actual_reduction = self._execute_load_curtailment(curtailable_loads, target_reduction)
            
            # Update performance metrics
            if actual_reduction > 0:
                self.performance_metrics['peak_shaving_savings'] += actual_reduction * 0.001  # kWh
                self.performance_metrics['demand_response_events'] += 1
            
            # Record response
            self._record_demand_response_event("execute", self.demand_response_mode, actual_reduction)
            
        except Exception as e:
            self.logger.error("Error executing demand response: %s", e)
    
    def _identify_curtailable_loads(self) -> List[Tuple[str, LoadProfile]]:
        """
        Identify loads that can be curtailed.
        
        Returns:
            List of curtailable load tuples (id, profile)
        """
        try:
            curtailable = []
            
            for load_id, profile in self.active_loads.items():
                # Check if load is flexible enough
                if profile.flexibility > 0.5:  # More than 50% flexible
                    # Check if load is not critical
                    if profile.priority < 8:  # Priority less than 8
                        curtailable.append((load_id, profile))
            
            # Sort by priority (lower priority first) and flexibility (higher flexibility first)
            curtailable.sort(key=lambda x: (x[1].priority, -x[1].flexibility))
            
            return curtailable
            
        except Exception as e:
            self.logger.error("Error identifying curtailable loads: %s", e)
            return []
    
    def _execute_load_curtailment(self, curtailable_loads: List[Tuple[str, LoadProfile]], 
                                 target_reduction: float) -> float:
        """
        Execute load curtailment.
        
        Args:
            curtailable_loads: List of curtailable loads
            target_reduction: Target load reduction (W)
            
        Returns:
            Actual load reduction achieved (W)
        """
        try:
            actual_reduction = 0.0
            
            for load_id, profile in curtailable_loads:
                if actual_reduction >= target_reduction:
                    break
                
                # Calculate reduction for this load
                reduction = min(profile.power_demand * profile.flexibility, 
                              target_reduction - actual_reduction)
                
                # Apply reduction
                profile.power_demand -= reduction
                actual_reduction += reduction
                
                # Update load profile
                self.active_loads[load_id] = profile
                
                self.logger.info("Load curtailed: %s (%.1f W reduction)", load_id, reduction)
            
            return actual_reduction
            
        except Exception as e:
            self.logger.error("Error executing load curtailment: %s", e)
            return 0.0
    
    def start_optimization(self) -> bool:
        """
        Start load optimization.
        
        Returns:
            True if optimization started successfully
        """
        try:
            if not self.config.optimization_enabled:
                self.logger.warning("Optimization not enabled")
                return False
            
            if self.optimization_active:
                self.logger.warning("Optimization already active")
                return False
            
            self.optimization_active = True
            self.load_state = LoadState.OPTIMIZING
            
            # Set optimization target
            self.optimization_target = self._calculate_optimization_target()
            
            self.logger.info("Load optimization started")
            return True
            
        except Exception as e:
            self.logger.error("Error starting optimization: %s", e)
            return False
    
    def _stop_optimization(self) -> None:
        """Stop load optimization."""
        try:
            self.optimization_active = False
            
            if self.load_state == LoadState.OPTIMIZING:
                self.load_state = LoadState.FORECASTING
            
            self.logger.info("Load optimization stopped")
            
        except Exception as e:
            self.logger.error("Error stopping optimization: %s", e)
    
    def _execute_load_optimization(self) -> None:
        """Execute load optimization algorithm."""
        try:
            # Simplified optimization algorithm
            # In practice, this would use advanced optimization techniques
            
            # Analyze current load distribution
            load_distribution = self._analyze_load_distribution()
            
            # Optimize load scheduling
            optimization_result = self._optimize_load_scheduling(load_distribution)
            
            # Apply optimization results
            if optimization_result['improvement'] > 0:
                self._apply_optimization_results(optimization_result)
                self.performance_metrics['optimization_savings'] += optimization_result['improvement']
            
            # Record optimization
            optimization_record = {
                'timestamp': time.time(),
                'distribution': load_distribution,
                'result': optimization_result,
                'target': self.optimization_target
            }
            
            self.optimization_history.append(optimization_record)
            
        except Exception as e:
            self.logger.error("Error executing load optimization: %s", e)
    
    def _analyze_load_distribution(self) -> Dict[str, Any]:
        """
        Analyze current load distribution.
        
        Returns:
            Load distribution analysis
        """
        try:
            if not self.active_loads:
                return {'total_load': 0.0, 'distribution': {}}
            
            total_load = sum(profile.power_demand for profile in self.active_loads.values())
            
            # Analyze by load type
            type_distribution = {}
            for profile in self.active_loads.values():
                load_type = profile.load_type.value
                if load_type not in type_distribution:
                    type_distribution[load_type] = 0.0
                type_distribution[load_type] += profile.power_demand
            
            # Analyze by priority
            priority_distribution = {}
            for profile in self.active_loads.values():
                priority = profile.priority
                if priority not in priority_distribution:
                    priority_distribution[priority] = 0.0
                priority_distribution[priority] += profile.power_demand
            
            return {
                'total_load': total_load,
                'type_distribution': type_distribution,
                'priority_distribution': priority_distribution,
                'load_count': len(self.active_loads)
            }
            
        except Exception as e:
            self.logger.error("Error analyzing load distribution: %s", e)
            return {'total_load': 0.0, 'distribution': {}}
    
    def _optimize_load_scheduling(self, distribution: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize load scheduling.
        
        Args:
            distribution: Load distribution analysis
            
        Returns:
            Optimization result
        """
        try:
            # Simplified optimization
            # In practice, this would use advanced scheduling algorithms
            
            total_load = distribution.get('total_load', 0.0)
            improvement = 0.0
            
            # Optimize for efficiency
            if total_load > self.config.max_load * 0.8:  # High load
                # Suggest load shifting
                improvement = total_load * 0.05  # 5% improvement
            elif total_load < self.config.min_load:  # Low load
                # Suggest load consolidation
                improvement = (self.config.min_load - total_load) * 0.1  # 10% improvement
            
            return {
                'improvement': improvement,
                'suggestions': ['load_shifting', 'consolidation'],
                'feasible': improvement > 0
            }
            
        except Exception as e:
            self.logger.error("Error optimizing load scheduling: %s", e)
            return {'improvement': 0.0, 'suggestions': [], 'feasible': False}
    
    def _apply_optimization_results(self, results: Dict[str, Any]) -> None:
        """
        Apply optimization results.
        
        Args:
            results: Optimization results
        """
        try:
            # Simplified application of optimization results
            # In practice, this would implement the suggested changes
            
            if results.get('feasible', False):
                self.logger.info("Optimization applied: %.1f W improvement", 
                               results.get('improvement', 0.0))
            
        except Exception as e:
            self.logger.error("Error applying optimization results: %s", e)
    
    def _calculate_optimization_target(self) -> float:
        """
        Calculate optimization target.
        
        Returns:
            Optimization target value
        """
        try:
            # Calculate target based on current load and efficiency
            current_efficiency = self._calculate_load_efficiency()
            target = current_efficiency * 1.1  # Aim for 10% improvement
            return min(1.0, target)
            
        except Exception as e:
            self.logger.error("Error calculating optimization target: %s", e)
            return 0.8
    
    def _calculate_load_efficiency(self) -> float:
        """
        Calculate load efficiency.
        
        Returns:
            Load efficiency (0-1)
        """
        try:
            if not self.active_loads:
                return 0.0
            
            # Calculate efficiency based on load distribution and utilization
            total_load = sum(profile.power_demand for profile in self.active_loads.values())
            avg_priority = sum(profile.priority for profile in self.active_loads.values()) / len(self.active_loads)
            avg_flexibility = sum(profile.flexibility for profile in self.active_loads.values()) / len(self.active_loads)
            
            # Efficiency factors
            utilization_factor = total_load / self.config.max_load
            priority_factor = 1.0 - (avg_priority - 5) / 5  # Higher priority is better
            flexibility_factor = avg_flexibility
            
            # Combined efficiency
            efficiency = (utilization_factor * 0.4 + 
                         priority_factor * 0.3 + 
                         flexibility_factor * 0.3)
            
            return max(0.0, min(1.0, efficiency))
            
        except Exception as e:
            self.logger.error("Error calculating load efficiency: %s", e)
            return 0.5
    
    def _update_load_history(self, current_load: float, available_power: float) -> None:
        """
        Update load history.
        
        Args:
            current_load: Current load (W)
            available_power: Available power (W)
        """
        try:
            history_record = {
                'timestamp': time.time(),
                'load': current_load,
                'available_power': available_power,
                'utilization': current_load / max(1, available_power)
            }
            
            self.load_history.append(history_record)
            
        except Exception as e:
            self.logger.error("Error updating load history: %s", e)
    
    def _update_forecast_accuracy(self) -> None:
        """Update forecast accuracy."""
        try:
            if len(self.forecast_data) < 2:
                return
            
            # Compare recent forecast with actual load
            recent_forecast = self.forecast_data[-1]['forecast']
            actual_loads = [record['load'] for record in list(self.load_history)[-len(recent_forecast):]]
            
            if len(actual_loads) == len(recent_forecast):
                # Calculate accuracy
                errors = [abs(f - a) for f, a in zip(recent_forecast, actual_loads)]
                avg_error = sum(errors) / len(errors)
                avg_load = sum(actual_loads) / len(actual_loads)
                
                if avg_load > 0:
                    accuracy = max(0, 100 - (avg_error / avg_load * 100))
                    self.forecast_accuracy = accuracy
                    self.performance_metrics['load_forecast_accuracy'] = accuracy
            
        except Exception as e:
            self.logger.error("Error updating forecast accuracy: %s", e)
    
    def _update_performance_metrics(self) -> None:
        """Update performance metrics."""
        try:
            # Update energy managed
            self.performance_metrics['total_energy_managed'] += self.current_load * 0.001  # kWh
            
            # Update operating hours
            self.performance_metrics['operating_hours'] += 0.001  # hours
            
        except Exception as e:
            self.logger.error("Error updating performance metrics: %s", e)
    
    def _record_demand_response_event(self, event_type: str, mode: DemandResponseMode, 
                                    value: float) -> None:
        """
        Record demand response event.
        
        Args:
            event_type: Type of event
            mode: Demand response mode
            value: Event value
        """
        try:
            event_record = {
                'timestamp': time.time(),
                'event_type': event_type,
                'mode': mode.value,
                'value': value,
                'current_load': self.current_load
            }
            
            self.response_history.append(event_record)
            
        except Exception as e:
            self.logger.error("Error recording demand response event: %s", e)
    
    def _handle_fault(self, fault_type: str, fault_message: str) -> None:
        """
        Handle load manager faults.
        
        Args:
            fault_type: Type of fault
            fault_message: Fault message
        """
        try:
            self.logger.error("Load fault: %s - %s", fault_type, fault_message)
            
            # Update system state
            self.load_state = LoadState.FAULT
            
            # Update performance metrics
            self.performance_metrics['load_errors'] += 1
            
        except Exception as e:
            self.logger.error("Error handling fault: %s", e)
    
    def get_load_state(self) -> LoadState:
        """
        Get current load state.
        
        Returns:
            Current load state
        """
        return self.load_state
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return self.performance_metrics.copy()
    
    def get_active_loads(self) -> Dict[str, LoadProfile]:
        """
        Get active loads.
        
        Returns:
            Dictionary of active load profiles
        """
        return self.active_loads.copy()
    
    def get_load_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get load history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of load history records
        """
        history_list = list(self.load_history)
        if limit is None:
            return history_list
        else:
            return history_list[-limit:]
    
    def get_forecast_data(self) -> List[Dict[str, Any]]:
        """
        Get forecast data.
        
        Returns:
            List of forecast records
        """
        return self.forecast_data.copy()
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """
        Get optimization history.
        
        Returns:
            List of optimization records
        """
        return self.optimization_history.copy()
    
    def is_optimizing(self) -> bool:
        """
        Check if optimization is active.
        
        Returns:
            True if optimizing
        """
        return self.optimization_active
    
    def is_demand_response_active(self) -> bool:
        """
        Check if demand response is active.
        
        Returns:
            True if demand response is active
        """
        return self.demand_response_active
    
    def reset(self) -> None:
        """Reset load manager to initial state."""
        self.load_state = LoadState.IDLE
        self.current_load = 0.0
        self.target_load = 0.0
        self.demand_response_mode = DemandResponseMode.NORMAL
        self.active_loads.clear()
        self.load_profiles.clear()
        self.load_history.clear()
        self.forecast_data.clear()
        self.response_history.clear()
        self.optimization_history.clear()
        self.optimization_active = False
        self.demand_response_active = False
        self.performance_metrics = {
            'total_energy_managed': 0.0,
            'peak_shaving_savings': 0.0,
            'load_forecast_accuracy': 0.0,
            'demand_response_events': 0,
            'optimization_savings': 0.0,
            'operating_hours': 0.0,
            'load_errors': 0
        }
        self.logger.info("Load manager reset")

