"""
Economic Optimizer - Phase 7 Week 5 Day 29-31

Comprehensive economic optimization system for grid services including:
- Revenue maximization across all services
- Multi-objective optimization (revenue vs. grid support)
- Service allocation optimization
- Risk management and portfolio optimization
- Real-time economic decision making

Key Features:
- Multi-service revenue optimization
- Dynamic service allocation based on economic value
- Risk-adjusted return optimization
- Real-time market condition adaptation
- Performance tracking and ROI analysis
"""

import math
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import statistics


class OptimizationObjective(Enum):
    """Optimization objective types"""
    REVENUE_MAXIMIZATION = "revenue_max"
    PROFIT_MAXIMIZATION = "profit_max"
    RISK_ADJUSTED_RETURN = "risk_adjusted"
    GRID_SUPPORT_PRIORITY = "grid_priority"
    BALANCED_OPTIMIZATION = "balanced"


class ServiceType(Enum):
    """Grid service types for optimization"""
    FREQUENCY_REGULATION = "frequency"
    VOLTAGE_SUPPORT = "voltage"
    ENERGY_ARBITRAGE = "arbitrage"
    DEMAND_RESPONSE = "demand_response"
    GRID_STABILIZATION = "stabilization"
    BACKUP_POWER = "backup"


@dataclass
class ServiceParameters:
    """Economic parameters for grid services"""
    revenue_rate: float = 0.0             # $/MWh revenue rate
    availability_payment: float = 0.0     # $/MW-hour availability payment
    performance_bonus: float = 0.0        # Performance bonus multiplier
    penalty_rate: float = 0.0             # Penalty rate for non-performance
    capacity_requirement: float = 0.0     # Required capacity allocation
    response_time: float = 0.0            # Required response time (seconds)
    duration_limit: float = 0.0           # Maximum service duration (hours)
    reliability_factor: float = 1.0       # Service reliability factor


@dataclass
class OptimizationConstraints:
    """Optimization constraints and limits"""
    max_power_output: float = 250.0       # Maximum power output (kW)
    min_soc: float = 0.1                  # Minimum state of charge
    max_soc: float = 0.9                  # Maximum state of charge
    max_cycles_per_day: float = 2.0       # Maximum battery cycles per day
    min_grid_support: float = 0.15        # Minimum capacity for grid support
    max_arbitrage_allocation: float = 0.6  # Maximum capacity for arbitrage
    risk_tolerance: float = 0.3            # Risk tolerance factor (0-1)


@dataclass
class EconomicState:
    """Current economic state and performance"""
    total_revenue: float = 0.0             # Total accumulated revenue
    frequency_revenue: float = 0.0         # Revenue from frequency services
    voltage_revenue: float = 0.0           # Revenue from voltage services
    arbitrage_revenue: float = 0.0         # Revenue from energy arbitrage
    demand_response_revenue: float = 0.0   # Revenue from demand response
    stabilization_revenue: float = 0.0     # Revenue from stabilization
    
    total_costs: float = 0.0               # Total operational costs
    battery_degradation_cost: float = 0.0  # Battery degradation costs
    maintenance_cost: float = 0.0          # Maintenance costs
    
    net_profit: float = 0.0                # Net profit (revenue - costs)
    roi: float = 0.0                       # Return on investment
    
    operating_hours: float = 0.0           # Total operating hours
    service_utilization: Optional[Dict[str, float]] = None  # Service utilization rates


class EconomicOptimizer:
    """    Comprehensive economic optimization system for grid services.
    
    Optimizes revenue across all grid services while maintaining grid support
    requirements and managing operational risks.
    """
    
    def __init__(self, constraints: Optional[OptimizationConstraints] = None):
        """Initialize economic optimizer"""
        self.constraints = constraints or OptimizationConstraints()
        self.objective = OptimizationObjective.BALANCED_OPTIMIZATION
          # Expose key constraints for testing
        self.max_power_kw = self.constraints.max_power_output
        self.risk_tolerance = self.constraints.risk_tolerance
        
        # Service portfolio tracking
        self.service_portfolio = []
        
        # Service economic parameters
        self.service_parameters = {
            ServiceType.FREQUENCY_REGULATION: ServiceParameters(
                revenue_rate=35.0,           # $/MWh
                availability_payment=8.0,    # $/MW-hour
                performance_bonus=1.1,       # 10% bonus for good performance
                penalty_rate=5.0,            # $/MWh penalty
                capacity_requirement=50.0,   # kW minimum
                response_time=2.0,           # seconds
                duration_limit=1.0,          # hours
                reliability_factor=0.95
            ),
            ServiceType.VOLTAGE_SUPPORT: ServiceParameters(
                revenue_rate=25.0,           # $/MVARh
                availability_payment=5.0,    # $/MVAR-hour
                performance_bonus=1.05,      # 5% bonus
                penalty_rate=3.0,            # $/MVARh penalty
                capacity_requirement=30.0,   # kVAR minimum
                response_time=5.0,           # seconds
                duration_limit=4.0,          # hours
                reliability_factor=0.98
            ),
            ServiceType.ENERGY_ARBITRAGE: ServiceParameters(
                revenue_rate=0.0,            # Variable based on price spread
                availability_payment=0.0,    # No availability payment
                performance_bonus=1.0,       # No bonus
                penalty_rate=0.0,            # No penalty
                capacity_requirement=0.0,    # No minimum
                response_time=300.0,         # 5 minutes
                duration_limit=12.0,         # hours
                reliability_factor=1.0
            ),
            ServiceType.DEMAND_RESPONSE: ServiceParameters(
                revenue_rate=45.0,           # $/MWh
                availability_payment=12.0,   # $/MW-hour
                performance_bonus=1.15,      # 15% bonus
                penalty_rate=8.0,            # $/MWh penalty
                capacity_requirement=25.0,   # kW minimum
                response_time=600.0,         # 10 minutes
                duration_limit=6.0,          # hours
                reliability_factor=0.90
            ),
            ServiceType.GRID_STABILIZATION: ServiceParameters(
                revenue_rate=50.0,           # $/MWh
                availability_payment=15.0,   # $/MW-hour
                performance_bonus=1.2,       # 20% bonus
                penalty_rate=10.0,           # $/MWh penalty
                capacity_requirement=75.0,   # kW minimum
                response_time=1.0,           # seconds
                duration_limit=2.0,          # hours
                reliability_factor=0.99
            )
        }
        
        # Economic state tracking
        self.economic_state = EconomicState(service_utilization={})
        
        # Optimization history
        self.optimization_history = []
        self.last_optimization_time = 0.0
        self.optimization_interval = 300.0  # 5-minute optimization cycle
          # Performance tracking
        self.performance_metrics = {
            'decisions': 0,
            'profitable_decisions': 0,
            'total_opportunity_value': 0.0,
            'captured_value': 0.0,
            'optimization_efficiency': 0.0,
            'total_revenue': 0.0
        }
        
        # Risk management
        self.risk_factors = {
            'price_volatility': 0.2,
            'performance_risk': 0.1,
            'availability_risk': 0.05,
            'degradation_risk': 0.15
        }
        
    def optimize(self, current_conditions: Dict[str, Any], 
                available_services: Dict[str, Any],
                forecasts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform economic optimization for current conditions
        
        Args:
            current_conditions: Current grid and economic conditions
            available_services: Available grid services and their status
            forecasts: Price and demand forecasts
            
        Returns:
            Optimization results and service allocation recommendations
        """
        current_time = time.time()
        
        # Update economic state
        self._update_economic_state(current_conditions, available_services)
        
        # Check if optimization is needed
        if current_time - self.last_optimization_time < self.optimization_interval:
            return self._get_cached_optimization()
        
        # Calculate service values
        service_values = self._calculate_service_values(current_conditions, forecasts)
        
        # Perform optimization based on objective
        optimization_result = self._perform_optimization(
            service_values, available_services, current_conditions
        )
        
        # Update performance tracking
        self._update_performance_metrics(optimization_result)
        
        # Cache result
        self.last_optimization_time = current_time
        self.optimization_history.append({
            'timestamp': current_time,
            'result': optimization_result,
            'conditions': current_conditions.copy()
        })
        
        # Limit history size
        if len(self.optimization_history) > 100:
            self.optimization_history = self.optimization_history[-100:]
        
        return optimization_result
    
    def _calculate_service_values(self, conditions: Dict[str, Any], 
                                forecasts: Dict[str, Any]) -> Dict[ServiceType, float]:
        """Calculate economic value for each service type"""
        
        service_values = {}
        current_price = conditions.get('electricity_price', 60.0)
        
        # Frequency regulation value
        frequency_deviation = abs(conditions.get('frequency', 50.0) - 50.0)
        frequency_urgency = min(2.0, frequency_deviation / 0.1)  # Urgency factor
        
        freq_params = self.service_parameters[ServiceType.FREQUENCY_REGULATION]
        frequency_value = (
            freq_params.revenue_rate * frequency_urgency * 
            freq_params.reliability_factor * freq_params.performance_bonus
        )
        service_values[ServiceType.FREQUENCY_REGULATION] = frequency_value
        
        # Voltage support value
        voltage_deviation = abs(conditions.get('voltage', 1.0) - 1.0)
        voltage_urgency = min(2.0, voltage_deviation / 0.05)  # Urgency factor
        
        volt_params = self.service_parameters[ServiceType.VOLTAGE_SUPPORT]
        voltage_value = (
            volt_params.revenue_rate * voltage_urgency * 
            volt_params.reliability_factor * volt_params.performance_bonus
        )
        service_values[ServiceType.VOLTAGE_SUPPORT] = voltage_value
        
        # Energy arbitrage value
        forecast_24h = forecasts.get('day_ahead', {})
        if forecast_24h:
            max_price = forecast_24h.get('max_price', current_price)
            min_price = forecast_24h.get('min_price', current_price)
            price_spread = max_price - min_price
            arbitrage_value = price_spread * 0.8  # 80% capture efficiency
        else:
            arbitrage_value = 0.0
        service_values[ServiceType.ENERGY_ARBITRAGE] = arbitrage_value
        
        # Demand response value
        load_level = conditions.get('load_demand', 150.0)
        peak_threshold = 200.0  # kW
        if load_level > peak_threshold:
            dr_urgency = (load_level - peak_threshold) / peak_threshold
            dr_params = self.service_parameters[ServiceType.DEMAND_RESPONSE]
            dr_value = (
                dr_params.revenue_rate * dr_urgency * 
                dr_params.reliability_factor * dr_params.performance_bonus
            )
        else:
            dr_value = 0.0
        service_values[ServiceType.DEMAND_RESPONSE] = dr_value
        
        # Grid stabilization value
        grid_emergency = (
            frequency_deviation > 0.2 or voltage_deviation > 0.1 or
            not conditions.get('grid_connected', True)
        )
        
        if grid_emergency:
            stab_params = self.service_parameters[ServiceType.GRID_STABILIZATION]
            stabilization_value = (
                stab_params.revenue_rate * 2.0 *  # High value during emergencies
                stab_params.reliability_factor * stab_params.performance_bonus
            )
        else:
            stabilization_value = 10.0  # Base availability value
        service_values[ServiceType.GRID_STABILIZATION] = stabilization_value
        
        return service_values
    
    def _perform_optimization(self, service_values: Dict[ServiceType, float],
                            available_services: Dict[str, Any],
                            conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Perform multi-objective optimization"""
          # Available capacity - use the minimum of configured max and currently available
        total_capacity = min(
            self.constraints.max_power_output,
            conditions.get('available_capacity', self.constraints.max_power_output)
        )
        
        # Service allocation based on optimization objective
        if self.objective == OptimizationObjective.REVENUE_MAXIMIZATION:
            allocation = self._optimize_revenue(service_values, total_capacity)
        elif self.objective == OptimizationObjective.RISK_ADJUSTED_RETURN:
            allocation = self._optimize_risk_adjusted(service_values, total_capacity)
        elif self.objective == OptimizationObjective.GRID_SUPPORT_PRIORITY:
            allocation = self._optimize_grid_support(service_values, total_capacity)
        else:  # BALANCED_OPTIMIZATION
            allocation = self._optimize_balanced(service_values, total_capacity, conditions)
          # Calculate expected performance
        expected_revenue = self._calculate_expected_revenue(allocation, service_values)
        expected_risk = self._calculate_expected_risk(allocation)
        
        # Generate service commands
        service_commands = self._generate_service_commands(allocation, conditions)
        
        return {
            'optimization_objective': self.objective.value,
            'service_allocation': allocation,
            'service_commands': service_commands,
            'expected_revenue_rate': expected_revenue,
            'total_revenue': expected_revenue * 24,  # Daily revenue estimate
            'expected_risk_level': expected_risk,
            'risk_score': expected_risk,  # Alias for compatibility
            'capacity_utilization': sum(allocation.values()) / total_capacity,
            'optimization_timestamp': time.time(),
            'total_opportunity_value': sum(service_values.values()),
            'captured_value_ratio': expected_revenue / max(sum(service_values.values()), 1.0)
        }
    
    def _optimize_revenue(self, service_values: Dict[ServiceType, float], 
                         total_capacity: float) -> Dict[ServiceType, float]:
        """Optimize for maximum revenue"""
        
        # Sort services by value per unit capacity
        sorted_services = sorted(
            service_values.items(),
            key=lambda x: x[1] / max(self.service_parameters[x[0]].capacity_requirement, 1.0),
            reverse=True
        )
        
        allocation = {}
        remaining_capacity = total_capacity
        
        for service_type, value in sorted_services:
            if value <= 0:
                allocation[service_type] = 0.0
                continue
            
            # Get service capacity requirement
            min_capacity = self.service_parameters[service_type].capacity_requirement
            max_capacity = min(remaining_capacity, total_capacity * 0.4)  # Max 40% per service
            
            if max_capacity >= min_capacity and remaining_capacity > 0:
                allocated_capacity = min(max_capacity, remaining_capacity)
                allocation[service_type] = allocated_capacity
                remaining_capacity -= allocated_capacity
            else:
                allocation[service_type] = 0.0
        
        return allocation
    
    def _optimize_risk_adjusted(self, service_values: Dict[ServiceType, float],
                              total_capacity: float) -> Dict[ServiceType, float]:
        """Optimize for risk-adjusted returns"""
        
        allocation = {}
        
        # Calculate risk-adjusted values
        risk_adjusted_values = {}
        for service_type, value in service_values.items():
            reliability = self.service_parameters[service_type].reliability_factor
            risk_discount = 1.0 - (1.0 - reliability) * self.constraints.risk_tolerance
            risk_adjusted_values[service_type] = value * risk_discount
        
        # Use revenue optimization with risk-adjusted values
        return self._optimize_revenue(risk_adjusted_values, total_capacity)
    
    def _optimize_grid_support(self, service_values: Dict[ServiceType, float],
                             total_capacity: float) -> Dict[ServiceType, float]:
        """Optimize with grid support priority"""
        
        allocation = {}
        remaining_capacity = total_capacity
        
        # Priority order for grid support
        priority_services = [
            ServiceType.GRID_STABILIZATION,
            ServiceType.FREQUENCY_REGULATION,
            ServiceType.VOLTAGE_SUPPORT,
            ServiceType.DEMAND_RESPONSE,
            ServiceType.ENERGY_ARBITRAGE
        ]
        
        # Reserve minimum capacity for grid support
        grid_support_reserve = total_capacity * self.constraints.min_grid_support
        
        for service_type in priority_services:
            if service_type not in service_values:
                allocation[service_type] = 0.0
                continue
            
            min_capacity = self.service_parameters[service_type].capacity_requirement
            
            if service_type in [ServiceType.GRID_STABILIZATION, ServiceType.FREQUENCY_REGULATION]:
                # High priority services get preferential allocation
                max_capacity = min(remaining_capacity, total_capacity * 0.3)
            else:
                max_capacity = min(remaining_capacity, total_capacity * 0.2)
            
            if max_capacity >= min_capacity and service_values[service_type] > 0:
                allocated_capacity = max(min_capacity, max_capacity)
                allocation[service_type] = allocated_capacity
                remaining_capacity -= allocated_capacity
            else:
                allocation[service_type] = 0.0
        
        return allocation
    
    def _optimize_balanced(self, service_values: Dict[ServiceType, float],
                          total_capacity: float, conditions: Dict[str, Any]) -> Dict[ServiceType, float]:
        """Balanced optimization considering revenue and grid support"""
        
        # Check for emergency conditions
        emergency_conditions = (
            abs(conditions.get('frequency', 50.0) - 50.0) > 0.1 or
            abs(conditions.get('voltage', 1.0) - 1.0) > 0.05 or
            not conditions.get('grid_connected', True)
        )
        
        if emergency_conditions:
            # Prioritize grid support during emergencies
            return self._optimize_grid_support(service_values, total_capacity)
        else:
            # Balance revenue and grid support during normal conditions
            allocation = {}
            remaining_capacity = total_capacity
            
            # Reserve capacity for grid support
            grid_reserve = total_capacity * 0.3
            arbitrage_limit = total_capacity * self.constraints.max_arbitrage_allocation
            
            # Allocate grid support services first
            grid_services = [
                ServiceType.FREQUENCY_REGULATION,
                ServiceType.VOLTAGE_SUPPORT,
                ServiceType.GRID_STABILIZATION
            ]
            
            for service_type in grid_services:
                if service_type in service_values and service_values[service_type] > 0:
                    min_capacity = self.service_parameters[service_type].capacity_requirement
                    max_capacity = min(remaining_capacity, grid_reserve / len(grid_services))
                    
                    if max_capacity >= min_capacity:
                        allocation[service_type] = max_capacity
                        remaining_capacity -= max_capacity
                    else:
                        allocation[service_type] = 0.0
                else:
                    allocation[service_type] = 0.0
            
            # Allocate remaining capacity to economic services
            economic_services = [ServiceType.DEMAND_RESPONSE, ServiceType.ENERGY_ARBITRAGE]
            
            for service_type in economic_services:
                if service_type in service_values and remaining_capacity > 0:
                    if service_type == ServiceType.ENERGY_ARBITRAGE:
                        max_capacity = min(remaining_capacity, arbitrage_limit)
                    else:
                        max_capacity = remaining_capacity
                    
                    allocation[service_type] = max_capacity
                    remaining_capacity -= max_capacity
                else:
                    allocation[service_type] = 0.0
            
            return allocation
    
    def _calculate_expected_revenue(self, allocation: Dict[ServiceType, float],
                                  service_values: Dict[ServiceType, float]) -> float:
        """Calculate expected revenue from allocation"""
        
        expected_revenue = 0.0
        
        for service_type, capacity in allocation.items():
            if capacity > 0 and service_type in service_values:
                value_per_kw = service_values[service_type]
                capacity_factor = capacity / self.constraints.max_power_output
                expected_revenue += value_per_kw * capacity_factor
        
        return expected_revenue
    
    def _calculate_expected_risk(self, allocation: Dict[ServiceType, float]) -> float:
        """Calculate expected risk level from allocation"""
        
        total_risk = 0.0
        total_capacity = sum(allocation.values())
        
        if total_capacity == 0:
            return 0.0
        
        for service_type, capacity in allocation.items():
            if capacity > 0:
                reliability = self.service_parameters[service_type].reliability_factor
                risk_factor = 1.0 - reliability
                capacity_weight = capacity / total_capacity
                total_risk += risk_factor * capacity_weight
        
        return total_risk
    
    def _generate_service_commands(self, allocation: Dict[ServiceType, float],
                                 conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specific service commands from allocation"""
        
        commands = {}
        
        for service_type, capacity in allocation.items():
            if capacity > 0:
                if service_type == ServiceType.FREQUENCY_REGULATION:
                    commands['frequency_regulation'] = {
                        'enable': True,
                        'capacity_kw': capacity,
                        'response_time': self.service_parameters[service_type].response_time,
                        'droop_setting': 0.04  # 4% droop
                    }
                
                elif service_type == ServiceType.VOLTAGE_SUPPORT:
                    commands['voltage_support'] = {
                        'enable': True,
                        'capacity_kvar': capacity,
                        'voltage_setpoint': 1.0,
                        'deadband': 0.02
                    }
                
                elif service_type == ServiceType.ENERGY_ARBITRAGE:
                    current_price = conditions.get('electricity_price', 60.0)
                    commands['energy_arbitrage'] = {
                        'enable': True,
                        'capacity_kw': capacity,
                        'charge_threshold': current_price * 0.8,
                        'discharge_threshold': current_price * 1.2
                    }
                
                elif service_type == ServiceType.DEMAND_RESPONSE:
                    commands['demand_response'] = {
                        'enable': True,
                        'capacity_kw': capacity,
                        'activation_threshold': 200.0,  # kW load threshold
                        'response_time': self.service_parameters[service_type].response_time
                    }
                
                elif service_type == ServiceType.GRID_STABILIZATION:
                    commands['grid_stabilization'] = {
                        'enable': True,
                        'capacity_kw': capacity,
                        'response_time': self.service_parameters[service_type].response_time,
                        'black_start_ready': True
                    }
        
        return commands
    
    def _update_economic_state(self, conditions: Dict[str, Any], 
                              services: Dict[str, Any]):
        """Update economic state tracking"""
        
        dt = 300.0  # 5-minute interval in seconds
        
        # Update operating hours
        self.economic_state.operating_hours += dt / 3600.0
        
        # Calculate revenues (simplified calculation)
        current_price = conditions.get('electricity_price', 60.0)
        
        # Update revenue by service type (example calculations)
        if services.get('frequency_active', False):
            freq_power = services.get('frequency_power', 0.0)
            freq_revenue = abs(freq_power) * self.service_parameters[ServiceType.FREQUENCY_REGULATION].revenue_rate * dt / 3600000.0
            self.economic_state.frequency_revenue += freq_revenue
        
        if services.get('arbitrage_active', False):
            arbitrage_power = services.get('arbitrage_power', 0.0)
            if arbitrage_power < 0:  # Discharging
                arbitrage_revenue = abs(arbitrage_power) * current_price * dt / 3600000.0
                self.economic_state.arbitrage_revenue += arbitrage_revenue
        
        # Update total revenue
        self.economic_state.total_revenue = (
            self.economic_state.frequency_revenue +
            self.economic_state.voltage_revenue +
            self.economic_state.arbitrage_revenue +
            self.economic_state.demand_response_revenue +
            self.economic_state.stabilization_revenue
        )
        
        # Calculate net profit
        self.economic_state.net_profit = self.economic_state.total_revenue - self.economic_state.total_costs
        
        # Calculate ROI (simplified)
        if self.economic_state.operating_hours > 0:
            investment_cost = 500000.0  # Assumed system cost
            self.economic_state.roi = (self.economic_state.net_profit / investment_cost) * 100
    
    def _update_performance_metrics(self, optimization_result: Dict[str, Any]):
        """Update optimization performance metrics"""
        
        self.performance_metrics['decisions'] += 1
        
        captured_value = optimization_result.get('expected_revenue_rate', 0.0)
        opportunity_value = optimization_result.get('total_opportunity_value', 0.0)
        
        self.performance_metrics['captured_value'] += captured_value
        self.performance_metrics['total_opportunity_value'] += opportunity_value
        
        if captured_value > 0:
            self.performance_metrics['profitable_decisions'] += 1
        
        # Calculate efficiency
        if self.performance_metrics['total_opportunity_value'] > 0:
            self.performance_metrics['optimization_efficiency'] = (                self.performance_metrics['captured_value'] / 
                self.performance_metrics['total_opportunity_value']
            )
    
    def _get_cached_optimization(self) -> Dict[str, Any]:
        """Get cached optimization result"""
        if self.optimization_history:
            return self.optimization_history[-1]['result']
        else:
            return {
                'optimization_objective': self.objective.value,
                'service_allocation': {},
                'service_commands': {},
                'expected_revenue_rate': 0.0,
                'total_revenue': 0.0,
                'expected_risk_level': 0.0,
                'risk_score': 0.0,
                'capacity_utilization': 0.0,
                'optimization_timestamp': time.time(),
                'total_opportunity_value': 0.0,
                'captured_value_ratio': 0.0
            }
    
    def get_economic_status(self) -> Dict[str, Any]:
        """Get current economic status and performance"""
        
        return {
            'economic_state': {
                'total_revenue': self.economic_state.total_revenue,
                'net_profit': self.economic_state.net_profit,
                'roi_percent': self.economic_state.roi,
                'operating_hours': self.economic_state.operating_hours
            },
            'service_revenues': {
                'frequency': self.economic_state.frequency_revenue,
                'voltage': self.economic_state.voltage_revenue,
                'arbitrage': self.economic_state.arbitrage_revenue,
                'demand_response': self.economic_state.demand_response_revenue,
                'stabilization': self.economic_state.stabilization_revenue
            },
            'performance_metrics': self.performance_metrics.copy(),
            'optimization_objective': self.objective.value,
            'last_optimization': self.last_optimization_time,
            'optimization_count': len(self.optimization_history)
        }
    
    def set_optimization_objective(self, objective: OptimizationObjective):
        """Set optimization objective"""
        self.objective = objective
    
    def update_service_parameters(self, service_type: ServiceType, 
                                 parameters: Dict[str, float]):
        """Update service economic parameters"""
        if service_type in self.service_parameters:
            for param_name, value in parameters.items():
                if hasattr(self.service_parameters[service_type], param_name):
                    setattr(self.service_parameters[service_type], param_name, value)
    
    def reset_performance_metrics(self):
        """Reset performance tracking metrics"""
        self.performance_metrics = {
            'decisions': 0,
            'profitable_decisions': 0,
            'total_opportunity_value': 0.0,
            'captured_value': 0.0,
            'optimization_efficiency': 0.0
        }
        self.optimization_history.clear()


def create_economic_optimizer(max_power_kw: float = 250.0, 
                            risk_tolerance: float = 0.3) -> EconomicOptimizer:
    """
    Factory function to create an economic optimizer
    
    Args:
        max_power_kw: Maximum power output in kW
        risk_tolerance: Risk tolerance factor (0.0-1.0)
        
    Returns:
        Configured EconomicOptimizer instance
    """
    constraints = OptimizationConstraints(
        max_power_output=max_power_kw,
        risk_tolerance=risk_tolerance
    )
    return EconomicOptimizer(constraints)
