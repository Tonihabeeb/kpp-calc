import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

class CurtailmentMode(Enum):
    """Load curtailment operating modes"""
    NORMAL = "normal"
    PEAK_SHAVING = "peak_shaving"
    EMERGENCY = "emergency"
    PRICE_RESPONSE = "price_response"

@dataclass
class LoadCurtailmentConfig:
    """Configuration for load curtailment controller"""
    max_curtailment: float = 0.3  # Maximum curtailment as fraction of load
    min_curtailment: float = 0.05  # Minimum curtailment to activate
    ramp_rate: float = 0.1  # Maximum change in curtailment per minute
    price_threshold: float = 100.0  # Price threshold for curtailment ($/MWh)
    peak_threshold: float = 0.9  # Peak threshold as fraction of capacity
    recovery_time: float = 3600.0  # Minimum time between curtailments (s)
    max_duration: float = 7200.0  # Maximum curtailment duration (s)

@dataclass
class CurtailmentState:
    """State for load curtailment controller"""
    mode: CurtailmentMode = CurtailmentMode.NORMAL
    current_curtailment: float = 0.0  # Current curtailment level
    curtailment_start: float = 0.0  # Start time of current curtailment
    last_curtailment_end: float = 0.0  # End time of last curtailment
    cumulative_curtailed: float = 0.0  # Total energy curtailed (kWh)
    available_loads: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=lambda: {
        'total_curtailed_energy': 0.0,
        'peak_reduction': 0.0,
        'cost_savings': 0.0,
        'curtailment_count': 0
    })

class LoadCurtailmentController:
    """
    Load curtailment controller for demand response applications.
    Manages load reduction during peak periods and high price events.
    """
    
    def __init__(self, config: Optional[LoadCurtailmentConfig] = None):
        """Initialize load curtailment controller"""
        self.config = config or LoadCurtailmentConfig()
        self.state = CurtailmentState()
        self.current_load = 0.0

    def set_current_load(self, load: float) -> None:
        """
        Set the current load level
        
        Args:
            load: Current load in kW
        """
        self.current_load = max(0.0, load)

    def request_load_reduction(self, reduction: float) -> float:
        """
        Request a specific load reduction
        
        Args:
            reduction: Requested load reduction in kW
            
        Returns:
            Actual load reduction that will be achieved
        """
        try:
            # Ensure reduction doesn't exceed maximum curtailment
            max_reduction = self.current_load * self.config.max_curtailment
            target_reduction = min(reduction, max_reduction)
            
            # Apply minimum curtailment threshold
            if target_reduction < self.current_load * self.config.min_curtailment:
                return 0.0
            
            # Update state
            self.state.current_curtailment = target_reduction
            if target_reduction > 0 and self.state.curtailment_start == 0:
                self.state.curtailment_start = time.time()
            
            # Update metrics
            self.state.metrics['curtailment_count'] += 1
            
            return target_reduction
            
        except Exception as e:
            self._end_curtailment()
            return 0.0
    
    def update(self, grid_state: Dict[str, Any], time_step: float) -> float:
        """
        Update curtailment control and calculate required load reduction
        
        Args:
            grid_state: Current grid state including load and price data
            time_step: Time step since last update in seconds
            
        Returns:
            Required load reduction in kW
        """
        try:
            # Update operating mode
            self._update_mode(grid_state)
            
            # Check if curtailment is allowed
            if not self._can_curtail(grid_state):
                self._end_curtailment()
                return 0.0
            
            # Calculate required curtailment
            curtailment = self._calculate_curtailment(grid_state)
            
            # Apply ramp rate limits
            curtailment = self._apply_ramp_limits(curtailment, time_step)
            
            # Update state and metrics
            self._update_state(curtailment, grid_state, time_step)
            
            return curtailment
            
        except Exception as e:
            self._end_curtailment()
            return 0.0
    
    def _update_mode(self, grid_state: Dict[str, Any]) -> None:
        """Update operating mode based on grid conditions"""
        price = grid_state.get('electricity_price', 0.0)
        load = grid_state.get('active_power', 0.0)
        capacity = grid_state.get('capacity', float('inf'))
        emergency = grid_state.get('emergency_condition', False)
        
        if emergency:
            self.state.mode = CurtailmentMode.EMERGENCY
        elif price > self.config.price_threshold:
            self.state.mode = CurtailmentMode.PRICE_RESPONSE
        elif load > capacity * self.config.peak_threshold:
            self.state.mode = CurtailmentMode.PEAK_SHAVING
        else:
            self.state.mode = CurtailmentMode.NORMAL
    
    def _can_curtail(self, grid_state: Dict[str, Any]) -> bool:
        """Check if curtailment is allowed"""
        current_time = time.time()
        
        # Check recovery time
        if (current_time - self.state.last_curtailment_end <
            self.config.recovery_time):
            return False
            
        # Check maximum duration
        if (self.state.curtailment_start > 0 and
            current_time - self.state.curtailment_start >
            self.config.max_duration):
            return False
            
        # Check if curtailment is needed
        return (self.state.mode != CurtailmentMode.NORMAL or
                self._calculate_curtailment(grid_state) >
                self.config.min_curtailment)
    
    def _calculate_curtailment(self, grid_state: Dict[str, Any]) -> float:
        """Calculate required curtailment level"""
        load = grid_state.get('active_power', 0.0)
        capacity = grid_state.get('capacity', float('inf'))
        price = grid_state.get('electricity_price', 0.0)
        
        if self.state.mode == CurtailmentMode.EMERGENCY:
            return load * self.config.max_curtailment
            
        elif self.state.mode == CurtailmentMode.PRICE_RESPONSE:
            # Linear response to price above threshold
            price_factor = min(1.0, (price - self.config.price_threshold) /
                             self.config.price_threshold)
            return load * self.config.max_curtailment * price_factor
            
        elif self.state.mode == CurtailmentMode.PEAK_SHAVING:
            # Curtail excess above peak threshold
            excess = load - (capacity * self.config.peak_threshold)
            return min(load * self.config.max_curtailment,
                      max(0.0, excess))
                      
        return 0.0
    
    def _apply_ramp_limits(self, target_curtailment: float,
                          time_step: float) -> float:
        """Apply ramp rate limits to curtailment changes"""
        max_change = self.config.ramp_rate * time_step / 60.0  # Convert to per second
        current = self.state.current_curtailment
        
        return current + max(-max_change,
                           min(max_change, target_curtailment - current))
    
    def _update_state(self, curtailment: float, grid_state: Dict[str, Any],
                     time_step: float) -> None:
        """Update controller state and metrics"""
        current_time = time.time()
        
        # Update curtailment state
        if curtailment > 0 and self.state.curtailment_start == 0:
            self.state.curtailment_start = current_time
        elif curtailment == 0 and self.state.curtailment_start > 0:
            self._end_curtailment()
        
        self.state.current_curtailment = curtailment
        
        # Update metrics
        energy_curtailed = curtailment * time_step / 3600.0  # kWh
        self.state.cumulative_curtailed += energy_curtailed
        
        price = grid_state.get('electricity_price', 0.0)
        cost_savings = energy_curtailed * price / 1000.0  # Convert to MWh
        
        self.state.metrics = {
            'total_curtailed_energy': float(self.state.cumulative_curtailed),
            'peak_reduction': float(curtailment),
            'cost_savings': float(self.state.metrics['cost_savings'] + cost_savings),
            'curtailment_count': float(self.state.metrics['curtailment_count'] +
                                     (1 if curtailment > 0 and
                                      self.state.curtailment_start == current_time
                                      else 0))
        }
    
    def _end_curtailment(self) -> None:
        """End current curtailment event"""
        if self.state.curtailment_start > 0:
            self.state.last_curtailment_end = time.time()
            self.state.curtailment_start = 0
        self.state.current_curtailment = 0.0
    
    def register_curtailable_load(self, load_info: Dict[str, Any]) -> None:
        """Register a curtailable load with the controller"""
        self.state.available_loads.append(load_info)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current controller state"""
        return {
            'mode': self.state.mode.value,
            'current_curtailment': self.state.current_curtailment,
            'curtailment_start': self.state.curtailment_start,
            'last_curtailment_end': self.state.last_curtailment_end,
            'cumulative_curtailed': self.state.cumulative_curtailed,
            'available_loads': self.state.available_loads,
            'metrics': self.state.metrics
        }
    
    def reset(self) -> None:
        """Reset controller state"""
        self.state = CurtailmentState()


def create_standard_load_curtailment_controller() -> LoadCurtailmentController:
    """
    Create a load curtailment controller with standard configuration.
    
    Returns:
        LoadCurtailmentController instance with standard settings
    """
    config = LoadCurtailmentConfig(
        max_curtailment=0.3,
        min_curtailment=0.05,
        ramp_rate=0.1,
        price_threshold=100.0,
        peak_threshold=0.9,
        recovery_time=3600.0,
        max_duration=7200.0
    )
    return LoadCurtailmentController(config)

