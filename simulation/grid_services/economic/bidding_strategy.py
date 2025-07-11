import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

class BiddingMode(Enum):
    """Bidding strategy modes"""
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    NEUTRAL = "neutral"
    DYNAMIC = "dynamic"

@dataclass
class BiddingStrategyConfig:
    """Configuration for bidding strategy"""
    min_profit_margin: float = 0.1  # Minimum profit margin
    max_position_size: float = 1000.0  # Maximum position size in kW
    price_increment: float = 0.5  # Price increment for bid adjustments
    update_interval: float = 300.0  # Strategy update interval
    risk_factor: float = 0.5  # Risk factor (0-1)
    volatility_threshold: float = 0.2  # Price volatility threshold
    trend_window: int = 12  # Hours for trend analysis

@dataclass
class BiddingState:
    """State for bidding strategy"""
    mode: BiddingMode = BiddingMode.NEUTRAL
    last_update: float = 0.0
    current_position: float = 0.0  # Net position in kW
    price_history: List[Dict[str, Any]] = field(default_factory=list)
    bid_history: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=lambda: {
        'successful_bids': 0,
        'failed_bids': 0,
        'average_profit': 0.0,
        'total_volume': 0.0
    })

class BiddingStrategy:
    """
    Bidding strategy for market participation.
    Implements dynamic price-based bidding with risk management.
    """
    
    def __init__(self, config: Optional[BiddingStrategyConfig] = None):
        """Initialize bidding strategy"""
        self.config = config or BiddingStrategyConfig()
        self.state = BiddingState()
    
    def update(self, market_data: Dict[str, Any], system_state: Dict[str, Any],
              time_step: float) -> Dict[str, Any]:
        """
        Update bidding strategy and generate bid/offer recommendations
        
        Args:
            market_data: Current market prices and forecasts
            system_state: Current system state including power and storage
            time_step: Time step since last update in seconds
            
        Returns:
            Dictionary containing bid/offer recommendations
        """
        try:
            # Update price history
            self._update_price_history(market_data)
            
            current_time = time.time()
            if (current_time - self.state.last_update >=
                self.config.update_interval):
                # Update strategy
                self._update_strategy(market_data, system_state)
                self.state.last_update = current_time
            
            # Generate recommendations
            return self._generate_recommendations(market_data, system_state)
            
        except Exception as e:
            return {}
    
    def _update_price_history(self, market_data: Dict[str, Any]) -> None:
        """Update price history with new market data"""
        self.state.price_history.append({
            'timestamp': time.time(),
            'energy_price': market_data.get('energy_price', 0.0),
            'reserve_price': market_data.get('reserve_price', 0.0),
            'forecast_prices': market_data.get('price_forecast', [])
        })
        
        # Keep only recent history
        max_history = self.config.trend_window * 4  # 15-minute intervals
        if len(self.state.price_history) > max_history:
            self.state.price_history = self.state.price_history[-max_history:]
    
    def _update_strategy(self, market_data: Dict[str, Any],
                        system_state: Dict[str, Any]) -> None:
        """Update bidding strategy based on market conditions"""
        # Calculate market metrics
        volatility = self._calculate_volatility()
        trend = self._calculate_trend()
        risk_score = self._calculate_risk_score(market_data, system_state)
        
        # Update bidding mode
        if risk_score > 0.8:
            self.state.mode = BiddingMode.CONSERVATIVE
        elif risk_score < 0.2:
            self.state.mode = BiddingMode.AGGRESSIVE
        elif volatility > self.config.volatility_threshold:
            self.state.mode = BiddingMode.DYNAMIC
        else:
            self.state.mode = BiddingMode.NEUTRAL
    
    def _calculate_volatility(self) -> float:
        """Calculate price volatility"""
        if len(self.state.price_history) < 2:
            return 0.0
            
        prices = [p['energy_price'] for p in self.state.price_history]
        mean_price = sum(prices) / len(prices)
        
        if mean_price == 0:
            return 0.0
            
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        return (variance ** 0.5) / mean_price
    
    def _calculate_trend(self) -> float:
        """Calculate price trend"""
        if len(self.state.price_history) < 2:
            return 0.0
            
        prices = [p['energy_price'] for p in self.state.price_history]
        first_price = prices[0]
        last_price = prices[-1]
        
        if first_price == 0:
            return 0.0
            
        return (last_price - first_price) / first_price
    
    def _calculate_risk_score(self, market_data: Dict[str, Any],
                            system_state: Dict[str, Any]) -> float:
        """Calculate current risk score"""
        # Position risk
        position_risk = abs(self.state.current_position /
                          self.config.max_position_size)
        
        # Price risk
        volatility = self._calculate_volatility()
        price_risk = min(1.0, volatility / self.config.volatility_threshold)
        
        # System risk
        capacity = system_state.get('available_capacity', 0.0)
        system_risk = 0.0 if capacity == 0 else (
            abs(self.state.current_position) / capacity)
        
        # Combine risks
        return (0.4 * position_risk +
                0.4 * price_risk +
                0.2 * system_risk)
    
    def _generate_recommendations(self, market_data: Dict[str, Any],
                                system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate bid/offer recommendations"""
        energy_price = market_data.get('energy_price', 0.0)
        capacity = system_state.get('available_capacity', 0.0)
        
        if capacity == 0:
            return {}
            
        # Calculate base prices
        mean_price = sum(p['energy_price']
                        for p in self.state.price_history) / len(
                        self.state.price_history) if self.state.price_history else energy_price
                        
        if self.state.mode == BiddingMode.AGGRESSIVE:
            bid_margin = self.config.min_profit_margin
            offer_margin = self.config.min_profit_margin
        elif self.state.mode == BiddingMode.CONSERVATIVE:
            bid_margin = self.config.min_profit_margin * 2
            offer_margin = self.config.min_profit_margin * 2
        else:
            bid_margin = self.config.min_profit_margin * 1.5
            offer_margin = self.config.min_profit_margin * 1.5
            
        # Calculate bid/offer prices
        bid_price = mean_price * (1 - bid_margin)
        offer_price = mean_price * (1 + offer_margin)
        
        # Adjust for trend
        trend = self._calculate_trend()
        if self.state.mode == BiddingMode.DYNAMIC:
            bid_price += trend * mean_price * self.config.risk_factor
            offer_price += trend * mean_price * self.config.risk_factor
            
        # Calculate quantities
        remaining_capacity = self.config.max_position_size - abs(
            self.state.current_position)
        base_quantity = min(remaining_capacity, capacity * 0.2)
        
        if self.state.mode == BiddingMode.AGGRESSIVE:
            quantity = base_quantity * 1.5
        elif self.state.mode == BiddingMode.CONSERVATIVE:
            quantity = base_quantity * 0.5
        else:
            quantity = base_quantity
            
        return {
            'bid': {
                'price': round(bid_price / self.config.price_increment) *
                        self.config.price_increment,
                'quantity': quantity,
                'confidence': 1.0 - self._calculate_risk_score(
                    market_data, system_state)
            },
            'offer': {
                'price': round(offer_price / self.config.price_increment) *
                         self.config.price_increment,
                'quantity': quantity,
                'confidence': 1.0 - self._calculate_risk_score(
                    market_data, system_state)
            }
        }
    
    def update_position(self, executed_quantity: float) -> None:
        """Update current position after trade execution"""
        self.state.current_position += executed_quantity
    
    def record_bid_result(self, bid_data: Dict[str, Any],
                         success: bool) -> None:
        """Record bid execution result"""
        self.state.bid_history.append({
            'timestamp': time.time(),
            'bid_data': bid_data,
            'success': success
        })
        
        # Update metrics
        if success:
            self.state.performance_metrics['successful_bids'] = float(
                self.state.performance_metrics['successful_bids'] + 1)
            self.state.performance_metrics['total_volume'] = float(
                self.state.performance_metrics['total_volume'] +
                bid_data.get('quantity', 0.0))
            
            # Update average profit
            price_diff = (bid_data.get('execution_price', 0.0) -
                         bid_data.get('price', 0.0))
            profit = price_diff * bid_data.get('quantity', 0.0)
            
            total_success = self.state.performance_metrics['successful_bids']
            if total_success > 0:
                self.state.performance_metrics['average_profit'] = float(
                    (self.state.performance_metrics['average_profit'] *
                     (total_success - 1) + profit) / total_success)
        else:
            self.state.performance_metrics['failed_bids'] = float(
                self.state.performance_metrics['failed_bids'] + 1)
        
        # Keep history manageable
        max_history = 1000
        if len(self.state.bid_history) > max_history:
            self.state.bid_history = self.state.bid_history[-max_history:]
    
    def get_state(self) -> Dict[str, Any]:
        """Get current strategy state"""
        return {
            'mode': self.state.mode.value,
            'current_position': self.state.current_position,
            'last_update': self.state.last_update,
            'performance_metrics': self.state.performance_metrics
        }
    
    def reset(self) -> None:
        """Reset strategy state"""
        self.state = BiddingState()


def create_bidding_strategy(config: Optional[BiddingStrategyConfig] = None) -> BiddingStrategy:
    """
    Factory function to create a bidding strategy instance.
    
    Args:
        config: Optional configuration for the bidding strategy
        
    Returns:
        BiddingStrategy instance
    """
    return BiddingStrategy(config)

