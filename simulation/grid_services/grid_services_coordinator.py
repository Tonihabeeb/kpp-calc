"""
Grid Services Coordinator

Coordinates all grid services including frequency response, voltage support,
demand response, and energy storage services. Manages service prioritization,
resource allocation, and revenue optimization.
"""

import time
import math
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import IntEnum

# Import frequency response services
from .frequency.primary_frequency_controller import PrimaryFrequencyController, create_standard_primary_frequency_controller
from .frequency.secondary_frequency_controller import SecondaryFrequencyController, create_standard_secondary_frequency_controller  
from .frequency.synthetic_inertia_controller import SyntheticInertiaController, create_standard_synthetic_inertia_controller

# Import voltage support services
from .voltage.voltage_regulator import VoltageRegulator, create_standard_voltage_regulator
from .voltage.power_factor_controller import PowerFactorController, create_standard_power_factor_controller
from .voltage.dynamic_voltage_support import DynamicVoltageSupport, create_standard_dynamic_voltage_support

# Import demand response services
from .demand_response.load_curtailment_controller import LoadCurtailmentController, create_standard_load_curtailment_controller
from .demand_response.peak_shaving_controller import PeakShavingController, create_standard_peak_shaving_controller
from .demand_response.load_forecaster import LoadForecaster, create_standard_load_forecaster

# Import energy storage services
from .storage.battery_storage_system import BatteryStorageSystem, create_battery_storage_system
from .storage.grid_stabilization_controller import GridStabilizationController, create_grid_stabilization_controller

# Import economic optimization services
from .economic.economic_optimizer import EconomicOptimizer, create_economic_optimizer
from .economic.market_interface import MarketInterface, create_market_interface
from .economic.price_forecaster import PriceForecaster, create_price_forecaster
from .economic.bidding_strategy import BiddingStrategyController, create_bidding_strategy


class ServicePriority(IntEnum):
    """Service priority levels (lower number = higher priority)"""
    EMERGENCY = 1
    FREQUENCY_REGULATION = 2
    VOLTAGE_SUPPORT = 3
    GRID_STABILIZATION = 4
    ENERGY_ARBITRAGE = 5
    DEMAND_RESPONSE = 6
    OPTIMIZATION = 7


@dataclass
class GridConditions:
    """Current grid conditions for service decision making"""
    frequency: float = 60.0          # Grid frequency (Hz)
    voltage: float = 480.0           # Grid voltage (V)
    active_power: float = 0.0        # Current active power output (MW)
    reactive_power: float = 0.0      # Current reactive power output (MVAR)
    grid_connected: bool = True      # Grid connection status
    agc_signal: float = 0.0          # AGC regulation signal (-1.0 to +1.0)
    timestamp: float = 0.0           # Measurement timestamp


@dataclass
class GridServicesConfig:
    """Configuration for Grid Services Coordinator"""
    enable_frequency_services: bool = True
    enable_voltage_services: bool = True
    enable_demand_response: bool = True
    enable_energy_storage: bool = True
    enable_economic_optimization: bool = True
    max_simultaneous_services: int = 5
    service_coordination_period: float = 1.0  # seconds
    
    # Resource allocation limits
    max_frequency_response: float = 0.15      # 15% for frequency services
    max_voltage_response: float = 0.10        # 10% for voltage services
    max_storage_response: float = 0.20        # 20% for storage services
    
    def validate(self):
        """Validate configuration parameters"""
        total_allocation = (self.max_frequency_response + 
                          self.max_voltage_response + 
                          self.max_storage_response)
        assert total_allocation <= 1.0, "Total resource allocation cannot exceed 100%"


class ServiceCommand:
    """Command from a grid service"""
    def __init__(self, service_type: str, power_command: float, priority: ServicePriority, 
                 duration: float = 0.0, confidence: float = 1.0):
        self.service_type = service_type
        self.power_command = power_command  # MW
        self.priority = priority
        self.duration = duration            # seconds (0 = indefinite)
        self.confidence = confidence        # 0.0 to 1.0
        self.timestamp = time.time()


class GridServicesCoordinator:
    """
    Grid Services Coordinator manages all grid services and coordinates their responses.
    
    Responsibilities:
    - Service prioritization and conflict resolution
    - Resource allocation optimization
    - Performance monitoring and optimization
    - Economic optimization across all services
    """
    
    def __init__(self, config: Optional[GridServicesConfig] = None):
        self.config = config or GridServicesConfig()
        self.config.validate()
        
        # Initialize frequency response services
        self.primary_frequency_controller = create_standard_primary_frequency_controller()
        self.secondary_frequency_controller = create_standard_secondary_frequency_controller()
        self.synthetic_inertia_controller = create_standard_synthetic_inertia_controller()
          # Initialize voltage support services
        self.voltage_regulator = create_standard_voltage_regulator()
        self.power_factor_controller = create_standard_power_factor_controller()
        self.dynamic_voltage_support = create_standard_dynamic_voltage_support()
        
        # Initialize demand response services
        self.load_curtailment_controller = create_standard_load_curtailment_controller()
        self.peak_shaving_controller = create_standard_peak_shaving_controller()
        self.load_forecaster = create_standard_load_forecaster()
          # Initialize energy storage services
        self.battery_storage_system = create_battery_storage_system()
        self.grid_stabilization_controller = create_grid_stabilization_controller()
          # Initialize economic optimization services
        self.economic_optimizer = create_economic_optimizer(max_power_kw=250.0)
        self.market_interface = create_market_interface({})
        self.price_forecaster = create_price_forecaster(base_price=60.0)
        self.bidding_strategy = create_bidding_strategy({})
        
        # State variables
        self.active_services = {}           # Currently active services
        self.service_commands = []          # Current service commands
        self.total_power_command = 0.0      # Coordinated power command (MW)
        self.last_coordination_time = time.time()
          # Performance tracking
        self.service_activations = {}       # Count of service activations
        self.service_durations = {}         # Total service durations
        self.coordination_decisions = []    # History of coordination decisions
        self.revenue_tracking = {}          # Revenue by service type
        self._last_bid_results = []         # Last bid results for strategy updates
        
        # Resource allocation
        self.available_capacity = 1.0       # Available capacity for services (p.u.)
        self.allocated_capacity = {}        # Capacity allocated by service
        
    def update(self, grid_conditions: GridConditions, dt: float, rated_power: float) -> Dict[str, Any]:
        """
        Update all grid services and coordinate responses.
        
        Args:
            grid_conditions: Current grid conditions
            dt: Time step (seconds)
            rated_power: System rated power (MW)
            
        Returns:
            Dictionary containing coordinated commands and status
        """
        current_time = time.time()
        
        # Clear previous commands
        self.service_commands.clear()
        
        # Update frequency response services
        if self.config.enable_frequency_services:
            self._update_frequency_services(grid_conditions, dt, rated_power)
          # Update voltage support services
        if self.config.enable_voltage_services:
            self._update_voltage_services(grid_conditions, dt, rated_power)
        
        # Update demand response services
        if self.config.enable_demand_response:
            self._update_demand_response_services(grid_conditions, dt, rated_power)
          # Update energy storage services
        if self.config.enable_energy_storage:
            self._update_energy_storage_services(grid_conditions, dt, rated_power)
        
        # Update economic optimization services
        if self.config.enable_economic_optimization:
            self._update_economic_services(grid_conditions, dt, rated_power)
        
        # Coordinate all service commands
        coordinated_response = self._coordinate_services(dt, rated_power)
        
        # Update performance tracking
        self._update_performance_tracking(dt)
        
        self.last_coordination_time = current_time
        
        return coordinated_response
    
    def _update_frequency_services(self, grid_conditions: GridConditions, dt: float, rated_power: float):
        """Update all frequency response services"""
        
        # Primary frequency control
        if abs(grid_conditions.frequency - 60.0) > 0.02:  # Outside dead band
            pfc_response = self.primary_frequency_controller.update(
                grid_conditions.frequency, dt, rated_power
            )
            
            if abs(pfc_response['response_pu']) > 0.001:
                command = ServiceCommand(
                    service_type='primary_frequency_control',
                    power_command=pfc_response['power_command_mw'],
                    priority=ServicePriority.FREQUENCY_REGULATION,
                    confidence=0.95
                )
                self.service_commands.append(command)
        
        # Secondary frequency control (AGC)
        if abs(grid_conditions.agc_signal) > 0.001:
            sfc_response = self.secondary_frequency_controller.update(
                grid_conditions.agc_signal, dt, rated_power
            )
            
            if abs(sfc_response['response_pu']) > 0.001:
                command = ServiceCommand(
                    service_type='secondary_frequency_control',
                    power_command=sfc_response['power_command_mw'],
                    priority=ServicePriority.FREQUENCY_REGULATION,
                    confidence=0.90
                )
                self.service_commands.append(command)
        
        # Synthetic inertia
        inertia_response = self.synthetic_inertia_controller.update(
            grid_conditions.frequency, dt, rated_power
        )
        
        if abs(inertia_response['response_pu']) > 0.001:
            command = ServiceCommand(
                service_type='synthetic_inertia',
                power_command=inertia_response['power_command_mw'],
                priority=ServicePriority.FREQUENCY_REGULATION,
                duration=10.0,  # Typical inertia response duration
                confidence=0.98            )
            self.service_commands.append(command)
    
    def _update_voltage_services(self, grid_conditions: GridConditions, dt: float, rated_power: float):
        """Update all voltage support services"""
        
        # Convert voltage from V to p.u. (assuming 480V nominal)
        voltage_pu = grid_conditions.voltage / 480.0
        
        # Dynamic voltage support (highest priority - check first)
        dvs_response = self.dynamic_voltage_support.update(
            voltage_pu, dt, rated_power
        )
        
        if dvs_response['support_active']:
            command = ServiceCommand(
                service_type='dynamic_voltage_support',
                power_command=dvs_response['reactive_power_mvar'],  # Use reactive power in MVAR
                priority=ServicePriority.EMERGENCY,
                confidence=0.98
            )
            self.service_commands.append(command)
        
        # Voltage regulator (if no dynamic support active)
        elif abs(voltage_pu - 1.0) > 0.01:  # Outside ±1% dead band
            vr_response = self.voltage_regulator.update(
                voltage_pu, dt, rated_power
            )
            
            if vr_response['regulation_active']:
                command = ServiceCommand(
                    service_type='voltage_regulation',
                    power_command=vr_response['reactive_power_mvar'],  # Use reactive power in MVAR
                    priority=ServicePriority.VOLTAGE_SUPPORT,
                    confidence=0.95
                )
                self.service_commands.append(command)
        
        # Power factor controller (lowest priority - only if voltage services not active)
        if not any(cmd.service_type in ['dynamic_voltage_support', 'voltage_regulation'] 
                  for cmd in self.service_commands):
            
            # Calculate current power factor
            active_power_pu = grid_conditions.active_power / rated_power
            reactive_power_pu = grid_conditions.reactive_power / rated_power
            
            # Check if voltage regulation is active (for coordination)
            voltage_regulation_active = any(cmd.service_type == 'voltage_regulation' 
                                          for cmd in self.service_commands)
            
            pfc_response = self.power_factor_controller.update(
                active_power_pu, reactive_power_pu, dt, rated_power, voltage_regulation_active
            )
            
            if pfc_response['control_active']:
                command = ServiceCommand(
                    service_type='power_factor_control',
                    power_command=pfc_response['reactive_power_mvar'],  # Use reactive power in MVAR
                    priority=ServicePriority.OPTIMIZATION,
                    confidence=0.85
                )
                self.service_commands.append(command)
    
    def _update_demand_response_services(self, grid_conditions: GridConditions, dt: float, rated_power: float):
        """Update all demand response services"""
          # Update load forecaster (always runs for planning)
        current_load = abs(grid_conditions.active_power)  # Current load in MW
        weather_data = {
            'temperature': 20.0,  # Default temperature (could be from weather service)
            'humidity': 50.0,
            'wind_speed': 5.0
        }
        
        self.load_forecaster.update(current_load, dt, weather_data)
        
        # Get load forecast for peak shaving decisions
        forecast = self.load_forecaster.get_forecast(hours_ahead=4)  # 4-hour horizon
        
        # Update peak shaving controller
        current_demand = abs(grid_conditions.active_power)
        current_generation = grid_conditions.active_power if grid_conditions.active_power > 0 else 0.0
        
        # Convert forecast to simple list of floats if needed
        forecast_values = []
        if forecast:
            forecast_values = [point.get('predicted_load', 0.0) for point in forecast]
        
        ps_response = self.peak_shaving_controller.update(current_demand, current_generation, dt, forecast_values)
          # Generate peak shaving command if active
        if ps_response['shaving_active']:
            total_response = ps_response['generation_boost_mw'] - ps_response['load_reduction_mw']
            if abs(total_response) > 0.001:  # Only if significant response
                command = ServiceCommand(
                    service_type='peak_shaving',
                    power_command=total_response,  # MW
                    priority=ServicePriority.DEMAND_RESPONSE,
                    duration=ps_response.get('duration', 0.0),
                    confidence=0.80
                )
                self.service_commands.append(command)
          # Update load curtailment controller
        # Check for emergency conditions that would trigger curtailment
        emergency_conditions = {
            'grid_frequency_low': grid_conditions.frequency < 59.5,
            'grid_frequency_high': grid_conditions.frequency > 60.5,
            'voltage_low': grid_conditions.voltage < 432.0,  # 90% of nominal
            'voltage_high': grid_conditions.voltage > 528.0,  # 110% of nominal
            'system_overload': abs(grid_conditions.active_power) > rated_power * 0.95
        }
        
        grid_condition_data = {
            'emergency_conditions': emergency_conditions,
            'electricity_price': 50.0,  # $/MWh
            'utility_signal': 0.0,  # Utility curtailment signal
            'timestamp': grid_conditions.timestamp or time.time()
        }
        
        lc_response = self.load_curtailment_controller.update(current_load, dt, grid_condition_data)
        
        # Generate curtailment command if active
        if lc_response['curtailment_active']:
            curtailment_power = lc_response['curtailment_amount']
            if curtailment_power > 0.001:  # Only if significant curtailment
                # Determine priority based on curtailment type
                priority = ServicePriority.EMERGENCY if lc_response.get('curtailment_type') == 'emergency' else ServicePriority.DEMAND_RESPONSE
                
                command = ServiceCommand(
                    service_type='load_curtailment',
                    power_command=-curtailment_power,  # Negative for load reduction
                    priority=priority,
                    duration=lc_response.get('duration', 0.0),                    confidence=0.90
                )
                self.service_commands.append(command)
    
    def _update_energy_storage_services(self, grid_conditions: GridConditions, dt: float, rated_power: float):
        """Update all energy storage services"""
        
        # Prepare grid conditions for storage services
        storage_grid_conditions = {
            'frequency': grid_conditions.frequency,
            'voltage': grid_conditions.voltage,
            'active_power': grid_conditions.active_power,
            'reactive_power': grid_conditions.reactive_power,
            'grid_connected': grid_conditions.grid_connected,
            'electricity_price': 60.0,  # Default price, should be from market data
            'load_demand': grid_conditions.active_power * 1000  # Convert to kW
        }
        
        # Battery storage system (arbitrage and grid support)
        bss_response = self.battery_storage_system.update(dt, storage_grid_conditions)
        
        if bss_response['active'] and abs(bss_response['power_output_kw']) > 1.0:
            command = ServiceCommand(
                service_type='battery_storage',
                power_command=bss_response['power_output_kw'] / 1000.0,  # Convert kW to MW
                priority=ServicePriority.ENERGY_ARBITRAGE,
                confidence=0.85
            )
            self.service_commands.append(command)
        
        # Grid stabilization controller 
        battery_status = {
            'active': bss_response['active'],
            'soc': bss_response['soc'],
            'health': bss_response['health'],
            'available_energy_kwh': bss_response['available_energy_kwh'],
            'available_capacity_kwh': bss_response['available_capacity_kwh']
        }
        
        gsc_response = self.grid_stabilization_controller.update(dt, storage_grid_conditions, battery_status)
        
        if gsc_response['active'] and 'control_commands' in gsc_response:
            active_power = gsc_response['control_commands'].get('active_power_kw', 0.0)
            if abs(active_power) > 1.0:
                command = ServiceCommand(
                    service_type='grid_stabilization',
                    power_command=active_power / 1000.0,  # Convert kW to MW
                    priority=ServicePriority.GRID_STABILIZATION,
                    confidence=0.95
                )
                self.service_commands.append(command)
    
    def _update_economic_services(self, grid_conditions: GridConditions, dt: float, rated_power: float):
        """Update all economic optimization services"""
          # Update price forecasting
        current_price = getattr(grid_conditions, 'electricity_price', 60.0)  # Default if not available
        price_update = self.price_forecaster.update(current_price, grid_conditions.timestamp)
        
        # Prepare economic conditions
        economic_conditions = {
            'current_price': current_price,
            'forecast_prices': price_update.get('forecast_prices', [current_price] * 24),
            'grid_frequency': grid_conditions.frequency,
            'grid_voltage': grid_conditions.voltage,
            'active_power': grid_conditions.active_power,
            'available_capacity': self.available_capacity * rated_power,
            'timestamp': grid_conditions.timestamp
        }
          # Update economic optimizer
        optimization_result = self.economic_optimizer.optimize(
            economic_conditions, 
            self._get_current_service_portfolio(),
            {'prices': price_update.get('forecast_prices', [current_price] * 24)}
        )
        
        # Check for economic optimization commands
        if optimization_result.get('active', False):
            power_allocation = optimization_result.get('power_allocation', {})
            
            # Create commands for each service allocation
            for service_type, allocation in power_allocation.items():
                if abs(allocation.get('power_mw', 0.0)) > 0.1:  # Minimum threshold
                    command = ServiceCommand(
                        service_type=f'economic_{service_type}',
                        power_command=allocation['power_mw'],
                        priority=ServicePriority.OPTIMIZATION,
                        confidence=allocation.get('confidence', 0.7),
                        duration=allocation.get('duration_hours', 1.0) * 3600  # Convert to seconds
                    )
                    self.service_commands.append(command)
        
        # Update market interface with current conditions
        self.market_interface.process_market_clearing({
            'market_type': 'energy_rt',
            'clearing_time': grid_conditions.timestamp,
            'clearing_price': current_price,
            'total_demand': 1000.0,  # Simplified
            'total_supply': 1100.0   # Simplified
        })
          # Update bidding strategy performance
        if hasattr(self, '_last_bid_results') and self._last_bid_results:
            self.bidding_strategy.update_strategy_performance(self._last_bid_results)
            self._last_bid_results.clear()  # Clear after processing
    
    def _get_current_service_portfolio(self) -> Dict[str, Any]:
        """Get current service portfolio for economic optimization"""
        portfolio = {}
        
        # Aggregate current service commands by type
        for command in self.service_commands:
            service_category = command.service_type.split('_')[0]  # Get base service type
            if service_category not in portfolio:
                portfolio[service_category] = {
                    'total_power': 0.0,
                    'count': 0,
                    'avg_confidence': 0.0
                }
            
            portfolio[service_category]['total_power'] += command.power_command
            portfolio[service_category]['count'] += 1
            portfolio[service_category]['avg_confidence'] += command.confidence
        
        # Calculate averages
        for service_data in portfolio.values():
            if service_data['count'] > 0:
                service_data['avg_confidence'] /= service_data['count']
        
        return portfolio

    def _coordinate_services(self, dt: float, rated_power: float) -> Dict[str, Any]:
        """
        Coordinate multiple service commands into unified response.
        
        Args:
            dt: Time step (seconds)
            rated_power: System rated power (MW)
            
        Returns:
            Coordinated response dictionary
        """
        if not self.service_commands:
            return self._create_coordination_response(0.0, "No active services")
        
        # Sort commands by priority
        sorted_commands = sorted(self.service_commands, key=lambda x: x.priority.value)
        
        # Coordinate commands based on priority and compatibility
        coordinated_power = 0.0
        active_service_types = []
        coordination_method = "priority_based"
        
        if len(sorted_commands) == 1:
            # Single service - simple case
            command = sorted_commands[0]
            coordinated_power = command.power_command
            active_service_types.append(command.service_type)
            coordination_method = "single_service"
            
        elif len(sorted_commands) == 2:
            # Two services - check compatibility
            cmd1, cmd2 = sorted_commands[0], sorted_commands[1]
            
            if self._are_services_compatible(cmd1, cmd2):
                # Compatible services can be combined
                if cmd1.priority == cmd2.priority:
                    # Same priority - average weighted by confidence
                    total_confidence = cmd1.confidence + cmd2.confidence
                    coordinated_power = (
                        (cmd1.power_command * cmd1.confidence + 
                         cmd2.power_command * cmd2.confidence) / total_confidence
                    )
                    coordination_method = "weighted_average"
                else:
                    # Different priority - higher priority dominates
                    coordinated_power = cmd1.power_command
                    coordination_method = "priority_dominant"
                
                active_service_types.extend([cmd1.service_type, cmd2.service_type])
            else:
                # Incompatible services - highest priority wins
                coordinated_power = cmd1.power_command
                active_service_types.append(cmd1.service_type)
                coordination_method = "priority_override"
        
        else:
            # Multiple services - complex coordination
            coordinated_power, active_service_types, coordination_method = (
                self._coordinate_multiple_services(sorted_commands)
            )
        
        # Apply resource limits
        max_power = rated_power * self.config.max_frequency_response
        coordinated_power = max(-max_power, min(max_power, coordinated_power))
        
        # Update active services tracking
        self.active_services = {stype: True for stype in active_service_types}
        self.total_power_command = coordinated_power
        
        # Record coordination decision
        decision_record = {
            'timestamp': time.time(),
            'input_commands': len(self.service_commands),
            'coordinated_power': coordinated_power,
            'active_services': active_service_types.copy(),
            'coordination_method': coordination_method
        }
        self.coordination_decisions.append(decision_record)
        
        # Keep only recent decisions (last 100)
        if len(self.coordination_decisions) > 100:
            self.coordination_decisions = self.coordination_decisions[-100:]
        
        status = f"{coordination_method}: {len(active_service_types)} services active"
        return self._create_coordination_response(coordinated_power, status)
    
    def _are_services_compatible(self, cmd1: ServiceCommand, cmd2: ServiceCommand) -> bool:
        """Check if two service commands are compatible for coordination"""
        
        # Services of the same type are always compatible
        if cmd1.service_type == cmd2.service_type:
            return True
        
        # Frequency services are generally compatible
        frequency_services = {'primary_frequency_control', 'secondary_frequency_control', 'synthetic_inertia'}
        if cmd1.service_type in frequency_services and cmd2.service_type in frequency_services:
            return True
        
        # Voltage services are generally compatible
        voltage_services = {'voltage_regulation', 'power_factor_correction', 'dynamic_voltage_support'}
        if cmd1.service_type in voltage_services and cmd2.service_type in voltage_services:
            return True
        
        # Check if commands are in same direction (both positive or both negative)
        same_direction = (cmd1.power_command * cmd2.power_command >= 0)
        
        # Services are compatible if they're in the same direction
        return same_direction
    
    def _coordinate_multiple_services(self, commands: List[ServiceCommand]) -> tuple:
        """
        Coordinate multiple service commands using advanced algorithms.
        
        Returns:
            Tuple of (coordinated_power, active_service_types, coordination_method)
        """
        # Group commands by priority level
        priority_groups = {}
        for cmd in commands:
            priority = cmd.priority.value
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(cmd)
        
        # Start with highest priority group
        highest_priority = min(priority_groups.keys())
        primary_group = priority_groups[highest_priority]
        
        # Calculate weighted average within priority group
        total_weight = sum(cmd.confidence for cmd in primary_group)
        coordinated_power = sum(
            cmd.power_command * cmd.confidence for cmd in primary_group
        ) / total_weight
        
        active_service_types = [cmd.service_type for cmd in primary_group]
        
        # Check if we can add compatible services from lower priority groups
        for priority_level in sorted(priority_groups.keys())[1:]:
            if len(active_service_types) >= self.config.max_simultaneous_services:
                break
            
            for cmd in priority_groups[priority_level]:
                # Check compatibility with current coordination
                avg_existing = coordinated_power
                if self._is_command_compatible_with_average(cmd, avg_existing):
                    # Add this service with reduced weight due to lower priority
                    weight_factor = 0.5  # Reduce influence of lower priority services
                    total_weight += cmd.confidence * weight_factor
                    coordinated_power = (
                        coordinated_power * (total_weight - cmd.confidence * weight_factor) +
                        cmd.power_command * cmd.confidence * weight_factor
                    ) / total_weight
                    active_service_types.append(cmd.service_type)
                    
                    if len(active_service_types) >= self.config.max_simultaneous_services:
                        break
        
        coordination_method = f"multi_service_{len(active_service_types)}"
        return coordinated_power, active_service_types, coordination_method
    
    def _is_command_compatible_with_average(self, cmd: ServiceCommand, avg_power: float) -> bool:
        """Check if a command is compatible with the current average"""
        # Commands are compatible if they don't oppose each other too strongly
        if avg_power == 0:
            return True
        
        # Allow up to 50% opposition
        opposition_ratio = -cmd.power_command / avg_power if avg_power != 0 else 0
        return opposition_ratio < 0.5
    
    def _create_coordination_response(self, power_command: float, status: str) -> Dict[str, Any]:
        """Create standardized coordination response"""
        return {
            'total_power_command_mw': power_command,
            'total_power_command': power_command,  # Alias for compatibility
            'active_services': list(self.active_services.keys()),
            'service_count': len(self.active_services),
            'status': status,
            'coordination_method': getattr(self, '_last_coordination_method', 'none'),
            'coordination_successful': True,
            'timestamp': self.last_coordination_time,
            
            # Individual service responses for monitoring
            'frequency_services': {
                'primary_active': self.primary_frequency_controller.is_responding(),
                'secondary_active': self.secondary_frequency_controller.is_regulating(),
                'inertia_active': self.synthetic_inertia_controller.is_responding()
            },
            'voltage_services': {
                'regulator_active': self.voltage_regulator.is_regulating(),
                'power_factor_active': self.power_factor_controller.is_controlling(),
                'dynamic_support_active': self.dynamic_voltage_support.is_supporting()
            }
        }
    
    def _update_performance_tracking(self, dt: float):
        """Update performance tracking metrics"""
        current_time = time.time()
        
        # Track service activations and durations
        for service_type in self.active_services:
            # Count activations
            if service_type not in self.service_activations:
                self.service_activations[service_type] = 0
            self.service_activations[service_type] += 1
            
            # Track duration
            if service_type not in self.service_durations:
                self.service_durations[service_type] = 0.0
            self.service_durations[service_type] += dt
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for all services"""
        metrics = {
            'coordinator': {
                'total_coordinations': len(self.coordination_decisions),
                'active_service_count': len(self.active_services),
                'current_power_command': self.total_power_command,
                'service_activations': self.service_activations.copy(),
                'service_durations': self.service_durations.copy()
            },
            
            'frequency_services': {
                'primary_frequency': self.primary_frequency_controller.get_performance_metrics(),
                'secondary_frequency': self.secondary_frequency_controller.get_performance_metrics(),
                'synthetic_inertia': self.synthetic_inertia_controller.get_performance_metrics()
            },
            
            'voltage_services': {
                'voltage_regulator': self.voltage_regulator.get_performance_metrics(),
                'power_factor_controller': self.power_factor_controller.get_performance_metrics(),
                'dynamic_voltage_support': self.dynamic_voltage_support.get_performance_metrics()
            }
        }
        
        return metrics
    
    def reset(self):
        """Reset all grid services and coordinator state"""
        # Reset individual controllers
        self.primary_frequency_controller.reset()
        self.secondary_frequency_controller.reset()
        self.synthetic_inertia_controller.reset()
        self.voltage_regulator.reset()
        self.power_factor_controller.reset()
        self.dynamic_voltage_support.reset()
        self.load_curtailment_controller.reset()
        self.peak_shaving_controller.reset()
        self.load_forecaster.reset()
        self.battery_storage_system.reset()
        self.grid_stabilization_controller.reset()
          # Reset economic services if they have reset methods
        if hasattr(self.market_interface, 'reset'):
            self.market_interface.reset()
        if hasattr(self.bidding_strategy, 'reset'):
            self.bidding_strategy.reset()
        
        # Reset last bid results for economic optimization
        self._last_bid_results.clear()
        
        # Reset coordinator state
        self.active_services.clear()
        self.service_commands.clear()
        self.total_power_command = 0.0
        self.service_activations.clear()
        self.service_durations.clear()
        self.coordination_decisions.clear()
        self.revenue_tracking.clear()
        self.allocated_capacity.clear()
        self.available_capacity = 1.0
        self.last_coordination_time = time.time()
        
    def get_service_status(self) -> Dict[str, bool]:
        """Get current status of all services"""
        return {
            'primary_frequency_control': self.primary_frequency_controller.is_responding(),
            'secondary_frequency_control': self.secondary_frequency_controller.is_regulating(),
            'synthetic_inertia': self.synthetic_inertia_controller.is_responding(),
            'voltage_regulator': self.voltage_regulator.is_regulating(),
            'power_factor_controller': self.power_factor_controller.is_controlling(),
            'dynamic_voltage_support': self.dynamic_voltage_support.is_supporting(),
            'load_curtailment': self.load_curtailment_controller.is_curtailing(),
            'peak_shaving': self.peak_shaving_controller.is_shaving(),            'load_forecaster': self.load_forecaster.is_forecasting(),
            'battery_storage': self.battery_storage_system.is_storing(),
            'grid_stabilization': self.grid_stabilization_controller.is_stabilizing(),
            'economic_optimizer': self.config.enable_economic_optimization,
            'market_interface': self.config.enable_economic_optimization and len(getattr(self.market_interface, 'active_bids', {})) > 0,
            'price_forecaster': self.config.enable_economic_optimization,
            'bidding_strategy': self.config.enable_economic_optimization,
            'grid_services_coordinator': len(self.active_services) > 0}

    def start_all_services(self):
        """Start all enabled grid services"""
        
        # Start energy storage services (only ones with start_service method)
        if self.config.enable_energy_storage:
            self.battery_storage_system.start_service()
            self.grid_stabilization_controller.start_service()
    
    def stop_all_services(self):
        """Stop all grid services"""
        
        # Stop energy storage services (only ones with stop_service method)
        self.battery_storage_system.stop_service()
        self.grid_stabilization_controller.stop_service()


def create_standard_grid_services_coordinator() -> GridServicesCoordinator:
    """Create a standard grid services coordinator with typical settings"""
    config = GridServicesConfig(
        enable_frequency_services=True,
        enable_voltage_services=True,
        enable_demand_response=True,         # Enable demand response services (Week 3)
        enable_energy_storage=True,         # ENABLED: Energy storage services (Week 4)
        enable_economic_optimization=True,  # ENABLED: Economic optimization services (Week 5)
        max_simultaneous_services=5,        # Increased for energy storage
        service_coordination_period=1.0,
        max_frequency_response=0.15,
        max_voltage_response=0.10,
        max_storage_response=0.20
    )
    coordinator = GridServicesCoordinator(config)
    coordinator.start_all_services()  # Start energy storage services
    return coordinator
