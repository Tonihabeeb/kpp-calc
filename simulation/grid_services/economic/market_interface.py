import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

class MarketType(Enum):
    """Types of electricity markets"""
    ENERGY = "energy"
    RESERVE = "reserve"
    CAPACITY = "capacity"
    ANCILLARY = "ancillary"

class OrderType(Enum):
    """Types of market orders"""
    BUY = "buy"
    SELL = "sell"
    BID = "bid"
    OFFER = "offer"

@dataclass
class MarketInterfaceConfig:
    """Configuration for market interface"""
    min_order_size: float = 100.0  # Minimum order size in kW
    max_order_size: float = 1000.0  # Maximum order size in kW
    price_tick_size: float = 0.01  # Minimum price increment
    order_timeout: float = 300.0  # Order timeout in seconds
    max_retry_attempts: int = 3  # Maximum order retry attempts
    update_interval: float = 60.0  # Market data update interval

@dataclass
class MarketState:
    """State for market interface"""
    connected: bool = False
    last_update: float = 0.0
    active_orders: List[Dict[str, Any]] = field(default_factory=list)
    order_history: List[Dict[str, Any]] = field(default_factory=list)
    market_data: Dict[str, Any] = field(default_factory=lambda: {
        'energy_price': 0.0,
        'reserve_price': 0.0,
        'capacity_price': 0.0,
        'price_forecast': [],
        'market_status': 'closed'
    })
    metrics: Dict[str, float] = field(default_factory=lambda: {
        'orders_executed': 0,
        'orders_failed': 0,
        'total_volume': 0.0,
        'average_price': 0.0
    })

class MarketInterface:
    """
    Market interface for interacting with electricity markets.
    Handles order submission, market data updates, and transaction tracking.
    """
    
    def __init__(self, config: Optional[MarketInterfaceConfig] = None):
        """Initialize market interface"""
        self.config = config or MarketInterfaceConfig()
        self.state = MarketState()
    
    def connect(self) -> bool:
        """Connect to market system"""
        try:
            # Simulate market connection
            self.state.connected = True
            self.state.last_update = time.time()
            return True
        except Exception as e:
            self.state.connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from market system"""
        try:
            # Cancel any active orders
            self.cancel_all_orders()
            self.state.connected = False
            return True
        except Exception as e:
            return False
    
    def update(self, time_step: float) -> Dict[str, Any]:
        """
        Update market data and process orders
        
        Args:
            time_step: Time step since last update in seconds
            
        Returns:
            Current market data
        """
        try:
            if not self.state.connected:
                return self.state.market_data
                
            current_time = time.time()
            if (current_time - self.state.last_update >=
                self.config.update_interval):
                self._update_market_data()
                self._process_active_orders()
                self.state.last_update = current_time
            
            return self.state.market_data
            
        except Exception as e:
            return self.state.market_data
    
    def submit_order(self, market_type: MarketType, order_type: OrderType,
                    quantity: float, price: float,
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Submit a new market order
        
        Args:
            market_type: Type of market (energy, reserve, etc.)
            order_type: Type of order (buy, sell, etc.)
            quantity: Order quantity in kW
            price: Order price in $/MWh
            metadata: Additional order metadata
            
        Returns:
            True if order was submitted successfully
        """
        try:
            if not self.state.connected:
                return False
                
            # Validate order parameters
            if not self._validate_order(quantity, price):
                return False
                
            # Create order
            order = {
                'id': str(int(time.time() * 1000)),
                'market_type': market_type.value,
                'order_type': order_type.value,
                'quantity': quantity,
                'price': price,
                'status': 'pending',
                'submit_time': time.time(),
                'metadata': metadata or {},
                'retry_count': 0
            }
            
            # Add to active orders
            self.state.active_orders.append(order)
            
            return True
            
        except Exception as e:
            return False
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a specific order"""
        try:
            for order in self.state.active_orders:
                if order['id'] == order_id:
                    order['status'] = 'cancelled'
                    self._move_to_history(order)
                    return True
            return False
        except Exception as e:
            return False
    
    def cancel_all_orders(self) -> bool:
        """Cancel all active orders"""
        try:
            for order in self.state.active_orders:
                order['status'] = 'cancelled'
                self._move_to_history(order)
            self.state.active_orders = []
            return True
        except Exception as e:
            return False
    
    def _validate_order(self, quantity: float, price: float) -> bool:
        """Validate order parameters"""
        if not (self.config.min_order_size <= quantity <=
                self.config.max_order_size):
            return False
            
        if price < 0:
            return False
            
        # Round price to tick size
        tick_size = self.config.price_tick_size
        if abs(price - round(price / tick_size) * tick_size) > 1e-10:
            return False
            
        return True
    
    def _update_market_data(self) -> None:
        """Update market data"""
        try:
            # Simulate market data update
            current_time = time.time()
            hour = int(current_time / 3600) % 24
            
            # Simple price model for simulation
            base_energy_price = 50.0  # $/MWh
            base_reserve_price = 25.0  # $/MW/h
            base_capacity_price = 75.0  # $/MW/day
            
            # Add time-of-day variation
            time_factor = 1.0 + 0.2 * abs(hour - 12) / 12.0
            
            self.state.market_data.update({
                'energy_price': base_energy_price * time_factor,
                'reserve_price': base_reserve_price * time_factor,
                'capacity_price': base_capacity_price,
                'market_status': 'open',
                'price_forecast': [
                    base_energy_price * (1.0 + 0.2 * abs((hour + i) % 24 - 12) / 12.0)
                    for i in range(24)
                ]
            })
            
        except Exception as e:
            pass
    
    def _process_active_orders(self) -> None:
        """Process active orders"""
        try:
            current_time = time.time()
            completed_orders = []
            
            for order in self.state.active_orders:
                # Check for timeout
                if (current_time - order['submit_time'] >
                    self.config.order_timeout):
                    if order['retry_count'] < self.config.max_retry_attempts:
                        # Retry order
                        order['retry_count'] += 1
                        order['submit_time'] = current_time
                    else:
                        # Mark as failed
                        order['status'] = 'failed'
                        self.state.metrics['orders_failed'] += 1
                        completed_orders.append(order)
                    continue
                
                # Simulate order execution
                market_price = self.state.market_data.get(
                    f"{order['market_type']}_price", 0.0)
                
                if ((order['order_type'] == 'buy' and
                     order['price'] >= market_price) or
                    (order['order_type'] == 'sell' and
                     order['price'] <= market_price)):
                    # Execute order
                    order['status'] = 'executed'
                    order['execution_time'] = current_time
                    order['execution_price'] = market_price
                    
                    # Update metrics
                    self.state.metrics['orders_executed'] += 1
                    self.state.metrics['total_volume'] += order['quantity']
                    self.state.metrics['average_price'] = (
                        (self.state.metrics['average_price'] *
                         (self.state.metrics['orders_executed'] - 1) +
                         market_price) /
                        self.state.metrics['orders_executed']
                    )
                    
                    completed_orders.append(order)
            
            # Move completed orders to history
            for order in completed_orders:
                self._move_to_history(order)
                self.state.active_orders.remove(order)
                
        except Exception as e:
            pass
    
    def _move_to_history(self, order: Dict[str, Any]) -> None:
        """Move order to history"""
        try:
            self.state.order_history.append(order.copy())
            
            # Keep only recent history
            max_history = 1000
            if len(self.state.order_history) > max_history:
                self.state.order_history = self.state.order_history[-max_history:]
                
        except Exception as e:
            pass
    
    def get_state(self) -> Dict[str, Any]:
        """Get current market interface state"""
        return {
            'connected': self.state.connected,
            'market_data': self.state.market_data.copy(),
            'active_orders': len(self.state.active_orders),
            'metrics': self.state.metrics.copy()
        }
    
    def reset(self) -> None:
        """Reset market interface state"""
        self.state = MarketState()

def create_market_interface(config: Optional[Dict[str, Any]] = None) -> MarketInterface:
    """
    Factory function to create a market interface with optional configuration
    
    Args:
        config: Optional dictionary with configuration parameters
        
    Returns:
        Configured MarketInterface instance
    """
    if config is None:
        return MarketInterface()
        
    interface_config = MarketInterfaceConfig(
        min_order_size=config.get('min_order_size', 100.0),
        max_order_size=config.get('max_order_size', 1000.0),
        price_tick_size=config.get('price_tick_size', 0.01),
        order_timeout=config.get('order_timeout', 300.0),
        max_retry_attempts=config.get('max_retry_attempts', 3),
        update_interval=config.get('update_interval', 60.0)
    )
    
    return MarketInterface(config=interface_config)

