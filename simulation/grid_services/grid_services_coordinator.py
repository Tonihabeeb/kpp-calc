import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from enum import IntEnum
from dataclasses import dataclass, field
from collections import deque

from simulation.grid_services.voltage.voltage_regulator import VoltageRegulator, VoltageRegulatorConfig
from simulation.grid_services.voltage.power_factor_controller import PowerFactorController, PowerFactorConfig
from simulation.grid_services.frequency.primary_frequency_controller import PrimaryFrequencyController, PrimaryFrequencyConfig
from simulation.grid_services.frequency.secondary_frequency_controller import SecondaryFrequencyController, SecondaryFrequencyConfig
from simulation.grid_services.storage.battery_storage_system import BatteryStorageSystem, BatteryStorageConfig
from simulation.grid_services.storage.grid_stabilization_controller import GridStabilizationController, GridStabilizationConfig
from simulation.grid_services.demand_response.load_forecaster import LoadForecaster, LoadForecastConfig
from simulation.grid_services.demand_response.load_curtailment_controller import LoadCurtailmentController, LoadCurtailmentConfig
from simulation.grid_services.economic.economic_optimizer import EconomicOptimizer, EconomicOptimizerConfig
from simulation.grid_services.economic.market_interface import MarketInterface, MarketInterfaceConfig, MarketType, OrderType
from simulation.grid_services.economic.price_forecaster import PriceForecaster, PriceForecasterConfig
from simulation.grid_services.economic.bidding_strategy import BiddingStrategy, BiddingStrategyConfig

# Grid conditions enum
class GridConditions(IntEnum):
    """Grid operating conditions."""
    NORMAL = 0
    STRESSED = 1
    EMERGENCY = 2
    RESTORATION = 3

@dataclass
class GridServicesConfig:
    """Configuration for grid services coordinator"""
    rated_power: float = 1000.0  # kVA
    nominal_frequency: float = 50.0  # Hz
    nominal_voltage: float = 1.0  # p.u.
    target_power_factor: float = 0.98
    frequency_priority: float = 1.0  # Priority weight for frequency control
    voltage_priority: float = 0.8  # Priority weight for voltage control
    power_factor_priority: float = 0.6  # Priority weight for power factor control
    storage_priority: float = 0.9  # Priority weight for storage services
    demand_response_priority: float = 0.7  # Priority weight for demand response
    economic_priority: float = 0.5  # Priority weight for economic optimization
    update_rate: float = 0.1  # seconds

@dataclass
class GridServicesState:
    """Grid services state data"""
    frequency: float = 50.0  # Hz
    voltage: float = 1.0  # p.u.
    active_power: float = 0.0  # kW
    reactive_power: float = 0.0  # kVAr
    power_factor: float = 1.0
    grid_condition: GridConditions = GridConditions.NORMAL
    timestamp: float = 0.0
    storage_state: Dict[str, Any] = field(default_factory=dict)
    demand_response_state: Dict[str, Any] = field(default_factory=dict)
    market_state: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=lambda: {
        'frequency_deviations_corrected': 0,
        'voltage_deviations_corrected': 0,
        'power_factor_corrections': 0,
        'total_energy_provided': 0.0,  # kWh
        'total_reactive_energy': 0.0,  # kVArh
        'average_power_factor': 1.0,
        'service_availability': 100.0,  # %
        'storage_cycles': 0,
        'demand_response_events': 0,
        'market_transactions': 0,
        'total_revenue': 0.0  # $
    })

class GridServicesCoordinator:
    """
    Grid services coordinator for managing and prioritizing multiple grid support services.
    Coordinates frequency control, voltage regulation, power factor correction,
    energy storage, demand response, and market participation.
    """
    
    def __init__(self, config: Optional[GridServicesConfig] = None):
        """Initialize the grid services coordinator"""
        self.config = config or GridServicesConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize state
        self.state = GridServicesState()
        self.is_active = False
        self.last_update_time = 0.0
        
        # Service registry
        self.registered_services = {}
        
        # Initialize controllers
        self._init_controllers()
        
        # Performance tracking
        self.response_history: deque = deque(maxlen=1000)
        
        self.logger.info("Grid services coordinator initialized")

    def register_service(self, service: Any) -> bool:
        """Register a grid service with the coordinator"""
        try:
            service_name = service.__class__.__name__
            self.registered_services[service_name] = service
            self.logger.info(f"Registered service: {service_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to register service: {e}")
            return False
    
    def _init_controllers(self) -> None:
        """Initialize all grid service controllers"""
        # Frequency controllers
        self.primary_frequency = PrimaryFrequencyController(
            PrimaryFrequencyConfig(
                nominal_frequency=self.config.nominal_frequency,
                rated_power=self.config.rated_power
            )
        )
        
        self.secondary_frequency = SecondaryFrequencyController(
            SecondaryFrequencyConfig(
                rated_power=self.config.rated_power
            )
        )
        
        # Voltage controllers
        self.voltage_regulator = VoltageRegulator(
            VoltageRegulatorConfig(
                nominal_voltage=self.config.nominal_voltage,
                rated_power=self.config.rated_power
            )
        )
        
        self.power_factor_controller = PowerFactorController(
            PowerFactorConfig(
                target_power_factor=self.config.target_power_factor,
                rated_power=self.config.rated_power,
                priority_factor=self.config.power_factor_priority
            )
        )
        
        # Storage controllers
        self.battery_storage = BatteryStorageSystem(
            BatteryStorageConfig(
                capacity=self.config.rated_power * 4  # 4 hours of storage
            )
        )
        
        self.grid_stabilization = GridStabilizationController(
            GridStabilizationConfig(
                max_power_output=self.config.rated_power
            )
        )
        
        # Demand response controllers
        self.load_forecaster = LoadForecaster(
            LoadForecastConfig()
        )
        
        self.load_curtailment = LoadCurtailmentController(
            LoadCurtailmentConfig()
        )
        
        # Economic controllers
        self.economic_optimizer = EconomicOptimizer(
            EconomicOptimizerConfig()
        )
        
        self.market_interface = MarketInterface(
            MarketInterfaceConfig()
        )
        
        self.price_forecaster = PriceForecaster(
            PriceForecasterConfig()
        )
        
        self.bidding_strategy = BiddingStrategy(
            BiddingStrategyConfig()
        )
    
    def enable(self) -> bool:
        """Enable all grid services"""
        try:
            self.is_active = True
            self.primary_frequency.enable()
            self.secondary_frequency.enable()
            self.voltage_regulator.enable()
            self.power_factor_controller.enable()
            
            # Connect to market
            self.market_interface.connect()
            
            self.logger.info("Grid services coordinator enabled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to enable grid services: {e}")
            return False
    
    def disable(self) -> bool:
        """Disable all grid services"""
        try:
            self.is_active = False
            self.primary_frequency.disable()
            self.secondary_frequency.disable()
            self.voltage_regulator.disable()
            self.power_factor_controller.disable()
            
            # Disconnect from market
            self.market_interface.disconnect()
            
            self.logger.info("Grid services coordinator disabled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to disable grid services: {e}")
            return False
    
    def update(self, grid_state: Dict[str, Any], time_step: float) -> Tuple[float, float]:
        """
        Update all grid services based on current grid state
        
        Args:
            grid_state: Current grid state including frequency, voltage, etc.
            time_step: Time step since last update in seconds
            
        Returns:
            Tuple of (active_power_adjustment, reactive_power_adjustment)
        """
        if not self.is_active:
            return 0.0, 0.0
            
        try:
            # Update state
            self._update_state(grid_state)
            
            # Determine grid condition
            self._assess_grid_condition()
            
            # Update market data
            market_data = self.market_interface.update(time_step)
            price_forecast = self.price_forecaster.update(market_data, time_step)
            
            # Update load forecast
            load_forecast = self.load_forecaster.update(grid_state, time_step)
            
            # Update economic optimization
            economic_setpoint, market_actions = self.economic_optimizer.update(
                market_data, grid_state, time_step)
            
            # Execute market actions
            if market_actions:
                if market_actions.get('market_order') == 'buy':
                    self.market_interface.submit_order(
                        MarketType.ENERGY,
                        OrderType.BUY,
                        abs(economic_setpoint),
                        market_data['energy_price']
                    )
                elif market_actions.get('market_order') == 'sell':
                    self.market_interface.submit_order(
                        MarketType.ENERGY,
                        OrderType.SELL,
                        abs(economic_setpoint),
                        market_data['energy_price']
                    )
            
            # Calculate power adjustments based on priorities
            active_power_adj = self._calculate_active_power_adjustment(
                time_step, economic_setpoint)
            reactive_power_adj = self._calculate_reactive_power_adjustment(
                time_step)
            
            # Update storage system
            storage_response = self.battery_storage.update({
                'power_setpoint': active_power_adj,
                'grid_frequency': self.state.frequency,
                'grid_voltage': self.state.voltage,
                'time_step': time_step
            })
            
            # Update demand response
            curtailment = self.load_curtailment.update(grid_state, time_step)
            
            # Combine responses
            total_active_power = (
                active_power_adj +
                storage_response.get('power_output', 0.0) -
                curtailment
            )
            
            # Update metrics
            self._update_metrics(total_active_power, reactive_power_adj)
            
            return total_active_power, reactive_power_adj
            
        except Exception as e:
            self.logger.error(f"Error in grid services update: {e}")
            return 0.0, 0.0
    
    def process_grid_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a grid event and coordinate service responses
        
        Args:
            event: Grid event data including frequency, voltage, market conditions
            
        Returns:
            Dict containing service responses and performance metrics
        """
        try:
            if not self.is_active:
                return {'status': 'inactive'}
                
            start_time = time.time()
            time_step = event.get('timestamp', time.time()) - self.last_update_time
            self.last_update_time = time.time()
            
            # Update grid state
            self._update_state(event)
            
            # Calculate required responses
            responses = {}
            
            # Handle frequency deviations
            if 'frequency_deviation' in event:
                freq_dev = float(event['frequency_deviation'])
                primary_response = self.primary_frequency.update(freq_dev, time_step)
                secondary_response = self.secondary_frequency.update(freq_dev, time_step)
                responses['frequency_control'] = {
                    'primary': primary_response,
                    'secondary': secondary_response
                }
            
            # Handle voltage deviations
            if 'voltage_deviation' in event:
                volt_dev = float(event['voltage_deviation'])
                voltage_response = self.voltage_regulator.update(volt_dev, time_step)
                pf_response = self.power_factor_controller.update(volt_dev, time_step)
                responses['voltage_control'] = {
                    'voltage': voltage_response,
                    'power_factor': pf_response
                }
            
            # Handle market price changes
            if 'market_price' in event:
                price = float(event['market_price'])
                storage_response = self.battery_storage.update(
                    {'electricity_price': price}, time_step)
                optimizer_response = self.economic_optimizer.update(
                    {'electricity_price': price}, time_step)
                responses['market_response'] = {
                    'storage': storage_response,
                    'economic': optimizer_response
                }
            
            # Handle demand changes
            if 'demand_spike' in event:
                demand_response = self.load_curtailment.update(
                    {'demand_spike': event['demand_spike']}, time_step)
                responses['demand_response'] = demand_response
            
            # Track response time
            response_time = time.time() - start_time
            self.response_history.append(response_time)
            
            # Update performance metrics
            self.state.performance_metrics.update({
                'last_response_time': response_time,
                'avg_response_time': sum(self.response_history) / len(self.response_history)
            })
            
            return {
                'status': 'success',
                'responses': responses,
                'metrics': {
                    'response_time': response_time,
                    'state': self.get_state()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing grid event: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _update_state(self, grid_state: Dict[str, Any]) -> None:
        """Update internal state from grid measurements"""
        self.state.frequency = grid_state.get('frequency', self.config.nominal_frequency)
        self.state.voltage = grid_state.get('voltage', self.config.nominal_voltage)
        self.state.active_power = grid_state.get('active_power', 0.0)
        self.state.reactive_power = grid_state.get('reactive_power', 0.0)
        self.state.power_factor = grid_state.get('power_factor', 1.0)
        self.state.timestamp = time.time()
        
        # Update component states
        self.state.storage_state = self.battery_storage.get_state()
        self.state.demand_response_state = self.load_curtailment.get_state()
        self.state.market_state = self.market_interface.get_state()
    
    def _assess_grid_condition(self) -> None:
        """Assess current grid condition based on measurements"""
        freq_dev = abs(self.state.frequency - self.config.nominal_frequency)
        volt_dev = abs(self.state.voltage - self.config.nominal_voltage)
        
        if freq_dev > 1.0 or volt_dev > 0.1:  # Severe deviation
            self.state.grid_condition = GridConditions.EMERGENCY
        elif freq_dev > 0.5 or volt_dev > 0.05:  # Significant deviation
            self.state.grid_condition = GridConditions.STRESSED
        elif self.state.grid_condition == GridConditions.EMERGENCY:
            self.state.grid_condition = GridConditions.RESTORATION
        else:
            self.state.grid_condition = GridConditions.NORMAL
    
    def _calculate_active_power_adjustment(self, time_step: float,
                                        economic_setpoint: float) -> float:
        """Calculate total active power adjustment"""
        # Primary frequency response
        primary_adj = self.primary_frequency.update(
            frequency=self.state.frequency,
            time_step=time_step
        )
        
        # Secondary frequency response (AGC)
        agc_signal = self._calculate_agc_signal()
        secondary_adj = self.secondary_frequency.update(
            agc_signal=agc_signal,
            time_step=time_step
        )
        
        # Grid stabilization response
        stabilization_adj = self.grid_stabilization.update(
            grid_state={
                'frequency': self.state.frequency,
                'voltage': self.state.voltage,
                'active_power': self.state.active_power,
                'time_step': time_step
            }
        )
        
        # Combine adjustments based on priorities and grid condition
        if self.state.grid_condition == GridConditions.EMERGENCY:
            # Prioritize grid stability
            return (primary_adj * self.config.frequency_priority +
                   secondary_adj * self.config.frequency_priority +
                   stabilization_adj * self.config.storage_priority)
        else:
            # Include economic optimization
            return (primary_adj * self.config.frequency_priority +
                   secondary_adj * self.config.frequency_priority +
                   stabilization_adj * self.config.storage_priority +
                   economic_setpoint * self.config.economic_priority)
    
    def _calculate_reactive_power_adjustment(self, time_step: float) -> float:
        """Calculate reactive power adjustment from voltage controllers"""
        # Voltage regulation
        voltage_adj = self.voltage_regulator.update(
            voltage=self.state.voltage,
            time_step=time_step
        )
        
        # Power factor correction
        pf_adj = self.power_factor_controller.update(
            power_factor=self.state.power_factor,
            time_step=time_step
        )
        
        # Combine adjustments based on priorities
        return (voltage_adj * self.config.voltage_priority +
                pf_adj * self.config.power_factor_priority)
    
    def _calculate_agc_signal(self) -> float:
        """Calculate AGC signal for secondary frequency control"""
        return -1.0 * (self.state.frequency - self.config.nominal_frequency)
    
    def _update_metrics(self, active_power_adj: float,
                       reactive_power_adj: float) -> None:
        """Update performance metrics"""
        # Calculate energy provided
        time_step = time.time() - self.state.timestamp
        energy_provided = abs(active_power_adj) * time_step / 3600.0  # kWh
        reactive_energy = abs(reactive_power_adj) * time_step / 3600.0  # kVArh
        
        # Update basic metrics
        self.state.performance_metrics.update({
            'total_energy_provided': float(
                self.state.performance_metrics['total_energy_provided'] +
                energy_provided),
            'total_reactive_energy': float(
                self.state.performance_metrics['total_reactive_energy'] +
                reactive_energy),
            'average_power_factor': float(
                abs(active_power_adj) /
                (abs(active_power_adj) + abs(reactive_power_adj))
                if (abs(active_power_adj) + abs(reactive_power_adj)) > 0
                else 1.0
            )
        })
        
        # Update storage metrics
        self.state.performance_metrics['storage_cycles'] = float(
            self.state.storage_state.get('cycle_count', 0))
        
        # Update demand response metrics
        self.state.performance_metrics['demand_response_events'] = float(
            self.state.demand_response_state.get('curtailment_count', 0))
        
        # Update market metrics
        self.state.performance_metrics['market_transactions'] = float(
            self.state.market_state.get('metrics', {}).get('orders_executed', 0))
        self.state.performance_metrics['total_revenue'] = float(
            self.state.market_state.get('metrics', {}).get('total_revenue', 0.0))
        
        # Calculate service availability
        self.state.performance_metrics['service_availability'] = 100.0
        
        # Track response
        self.response_history.append({
            'timestamp': time.time(),
            'active_power': active_power_adj,
            'reactive_power': reactive_power_adj,
            'grid_condition': self.state.grid_condition
        })
    
    def get_state(self) -> Dict[str, Any]:
        """Get current coordinator state"""
        return {
            'frequency': self.state.frequency,
            'voltage': self.state.voltage,
            'active_power': self.state.active_power,
            'reactive_power': self.state.reactive_power,
            'power_factor': self.state.power_factor,
            'grid_condition': self.state.grid_condition.name,
            'storage_state': self.state.storage_state,
            'demand_response_state': self.state.demand_response_state,
            'market_state': self.state.market_state,
            'performance_metrics': self.state.performance_metrics,
            'is_active': self.is_active
        }
    
    def reset(self) -> None:
        """Reset coordinator state"""
        self.state = GridServicesState()
        self.is_active = False
        self.last_update_time = 0.0
        self.response_history.clear()
        
        # Reset all controllers
        self.primary_frequency.reset()
        self.secondary_frequency.reset()
        self.voltage_regulator.reset()
        self.power_factor_controller.reset()
        self.battery_storage.reset()
        self.grid_stabilization.reset()
        self.load_forecaster.reset()
        self.load_curtailment.reset()
        self.economic_optimizer.reset()
        self.market_interface.reset()
        self.price_forecaster.reset()
        self.bidding_strategy.reset()

