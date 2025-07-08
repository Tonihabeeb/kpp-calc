"""
Economic Optimizer for KPP Simulator
Implements economic optimization and market integration
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from datetime import datetime, timedelta

from ...core.physics_engine import PhysicsEngine
from ...electrical.electrical_system import IntegratedElectricalSystem
from ...control_systems.control_system import IntegratedControlSystem


class OptimizationMode(Enum):
    """Economic optimization modes"""
    REVENUE_MAXIMIZATION = "revenue_maximization"
    COST_MINIMIZATION = "cost_minimization"
    PROFIT_OPTIMIZATION = "profit_optimization"
    RISK_ADJUSTED = "risk_adjusted"
    SUSTAINABLE = "sustainable"


class MarketType(Enum):
    """Market types"""
    DAY_AHEAD = "day_ahead"
    REAL_TIME = "real_time"
    FREQUENCY_RESPONSE = "frequency_response"
    CAPACITY = "capacity"
    ANCILLARY_SERVICES = "ancillary_services"


@dataclass
class MarketPrice:
    """Market price data"""
    timestamp: datetime
    price: float  # $/MWh
    market_type: MarketType
    location: str
    confidence: float


@dataclass
class OptimizationDecision:
    """Economic optimization decision"""
    timestamp: datetime
    decision_type: str
    power_output: float
    revenue: float
    cost: float
    profit: float
    market_type: MarketType
    confidence: float


@dataclass
class EconomicMetrics:
    """Economic performance metrics"""
    total_revenue: float
    total_cost: float
    total_profit: float
    profit_margin: float
    roi: float
    payback_period: float
    net_present_value: float
    internal_rate_of_return: float


class EconomicOptimizer:
    """
    Economic Optimizer for revenue and profit optimization
    
    Features:
    - Revenue maximization algorithms
    - Cost minimization strategies
    - Profit optimization
    - Market price forecasting
    - Risk management
    - Portfolio optimization
    """
    
    def __init__(self, 
                 physics_engine: PhysicsEngine,
                 electrical_system: IntegratedElectricalSystem,
                 control_system: IntegratedControlSystem):
        """
        Initialize the Economic Optimizer
        
        Args:
            physics_engine: Core physics engine
            electrical_system: Integrated electrical system
            control_system: Integrated control system
        """
        self.physics_engine = physics_engine
        self.electrical_system = electrical_system
        self.control_system = control_system
        
        # Optimization state
        self.is_active = False
        self.current_mode = OptimizationMode.PROFIT_OPTIMIZATION
        self.optimization_horizon = 24  # hours
        
        # Market data
        self.market_prices: List[MarketPrice] = []
        self.price_forecast: List[MarketPrice] = []
        self.market_participation: Dict[MarketType, bool] = {
            MarketType.DAY_AHEAD: True,
            MarketType.REAL_TIME: True,
            MarketType.FREQUENCY_RESPONSE: True,
            MarketType.CAPACITY: False,
            MarketType.ANCILLARY_SERVICES: True
        }
        
        # Economic parameters
        self.operational_costs = {
            'fuel_cost': 30.0,  # $/MWh
            'maintenance_cost': 5.0,  # $/MWh
            'startup_cost': 100.0,  # $/start
            'shutdown_cost': 50.0,  # $/shutdown
            'variable_cost': 2.0,  # $/MWh
            'fixed_cost': 1000.0  # $/day
        }
        
        self.revenue_streams = {
            MarketType.DAY_AHEAD: {'price': 50.0, 'volume': 1000.0},  # $/MWh, MWh
            MarketType.REAL_TIME: {'price': 60.0, 'volume': 500.0},
            MarketType.FREQUENCY_RESPONSE: {'price': 80.0, 'volume': 100.0},
            MarketType.CAPACITY: {'price': 20.0, 'volume': 1000.0},
            MarketType.ANCILLARY_SERVICES: {'price': 100.0, 'volume': 200.0}
        }
        
        # Optimization history
        self.optimization_decisions: List[OptimizationDecision] = []
        self.economic_metrics = EconomicMetrics(
            total_revenue=0.0,
            total_cost=0.0,
            total_profit=0.0,
            profit_margin=0.0,
            roi=0.0,
            payback_period=0.0,
            net_present_value=0.0,
            internal_rate_of_return=0.0
        )
        
        # Performance tracking
        self.performance_metrics = {
            'optimization_accuracy': 0.0,
            'forecast_accuracy': 0.0,
            'decision_quality': 0.0,
            'market_capture': 0.0,
            'risk_adjusted_return': 0.0
        }
        
        # Risk parameters
        self.risk_tolerance = 0.1  # 10% risk tolerance
        self.volatility_threshold = 0.2  # 20% price volatility threshold
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Economic Optimizer initialized")
    
    def start(self):
        """Start the economic optimizer"""
        self.is_active = True
        self.logger.info("Economic Optimizer started")
    
    def stop(self):
        """Stop the economic optimizer"""
        self.is_active = False
        self.logger.info("Economic Optimizer stopped")
    
    def update(self, dt: float):
        """
        Update the economic optimizer
        
        Args:
            dt: Time step in seconds
        """
        if not self.is_active:
            return
        
        # Update market data
        self._update_market_data()
        
        # Run optimization
        self._run_optimization()
        
        # Update economic metrics
        self._update_economic_metrics(dt)
        
        # Update performance metrics
        self._update_performance_metrics(dt)
    
    def _update_market_data(self):
        """Update market price data"""
        current_time = datetime.now()
        
        # Simulate market price updates
        for market_type in MarketType:
            if self.market_participation[market_type]:
                # Generate simulated price
                base_price = self.revenue_streams[market_type]['price']
                price_variation = np.random.normal(0, base_price * 0.1)  # 10% variation
                current_price = base_price + price_variation
                
                # Add time-of-day variation
                hour = current_time.hour
                if 6 <= hour <= 22:  # Peak hours
                    current_price *= 1.2
                else:  # Off-peak hours
                    current_price *= 0.8
                
                # Create market price entry
                market_price = MarketPrice(
                    timestamp=current_time,
                    price=max(0, current_price),
                    market_type=market_type,
                    location="grid_connection",
                    confidence=0.9
                )
                
                self.market_prices.append(market_price)
        
        # Limit market price history
        if len(self.market_prices) > 10000:
            self.market_prices = self.market_prices[-10000:]
    
    def _run_optimization(self):
        """Run economic optimization"""
        if not self.market_prices:
            return
        
        # Get current market conditions
        current_prices = self._get_current_market_prices()
        
        # Run optimization based on mode
        if self.current_mode == OptimizationMode.REVENUE_MAXIMIZATION:
            decision = self._optimize_revenue(current_prices)
        elif self.current_mode == OptimizationMode.COST_MINIMIZATION:
            decision = self._optimize_cost(current_prices)
        elif self.current_mode == OptimizationMode.PROFIT_OPTIMIZATION:
            decision = self._optimize_profit(current_prices)
        elif self.current_mode == OptimizationMode.RISK_ADJUSTED:
            decision = self._optimize_risk_adjusted(current_prices)
        else:
            decision = self._optimize_sustainable(current_prices)
        
        # Record decision
        if decision:
            self.optimization_decisions.append(decision)
            
            # Limit decision history
            if len(self.optimization_decisions) > 1000:
                self.optimization_decisions.pop(0)
    
    def _get_current_market_prices(self) -> Dict[MarketType, float]:
        """Get current market prices"""
        current_prices = {}
        current_time = datetime.now()
        
        for market_type in MarketType:
            if self.market_participation[market_type]:
                # Get most recent price for this market
                market_prices = [p for p in self.market_prices 
                               if p.market_type == market_type and 
                               (current_time - p.timestamp).total_seconds() < 3600]  # Last hour
                
                if market_prices:
                    current_prices[market_type] = market_prices[-1].price
                else:
                    current_prices[market_type] = self.revenue_streams[market_type]['price']
        
        return current_prices
    
    def _optimize_revenue(self, current_prices: Dict[MarketType, float]) -> Optional[OptimizationDecision]:
        """Optimize for maximum revenue"""
        if not current_prices:
            return None
        
        # Find highest price market
        best_market = max(current_prices.items(), key=lambda x: x[1])
        market_type, price = best_market
        
        # Calculate optimal power output
        max_power = 1000.0  # kW
        optimal_power = max_power
        
        # Calculate revenue
        revenue = (optimal_power / 1000) * price  # Convert to MWh
        
        # Calculate cost
        cost = self._calculate_operational_cost(optimal_power)
        
        # Calculate profit
        profit = revenue - cost
        
        decision = OptimizationDecision(
            timestamp=datetime.now(),
            decision_type="revenue_maximization",
            power_output=optimal_power,
            revenue=revenue,
            cost=cost,
            profit=profit,
            market_type=market_type,
            confidence=0.9
        )
        
        self.logger.info(f"Revenue optimization: {market_type.value} at ${price:.2f}/MWh, Revenue: ${revenue:.2f}")
        
        return decision
    
    def _optimize_cost(self, current_prices: Dict[MarketType, float]) -> Optional[OptimizationDecision]:
        """Optimize for minimum cost"""
        if not current_prices:
            return None
        
        # Find lowest cost operation
        min_power = 100.0  # kW (minimum viable operation)
        optimal_power = min_power
        
        # Calculate cost
        cost = self._calculate_operational_cost(optimal_power)
        
        # Calculate revenue (use average price)
        avg_price = np.mean(list(current_prices.values()))
        revenue = (optimal_power / 1000) * avg_price
        
        # Calculate profit
        profit = revenue - cost
        
        decision = OptimizationDecision(
            timestamp=datetime.now(),
            decision_type="cost_minimization",
            power_output=optimal_power,
            revenue=revenue,
            cost=cost,
            profit=profit,
            market_type=list(current_prices.keys())[0],
            confidence=0.8
        )
        
        self.logger.info(f"Cost optimization: {optimal_power:.1f} kW, Cost: ${cost:.2f}")
        
        return decision
    
    def _optimize_profit(self, current_prices: Dict[MarketType, float]) -> Optional[OptimizationDecision]:
        """Optimize for maximum profit"""
        if not current_prices:
            return None
        
        # Find optimal power output for maximum profit
        max_power = 1000.0  # kW
        power_steps = np.linspace(100, max_power, 50)
        
        best_profit = -float('inf')
        best_decision = None
        
        for power in power_steps:
            # Calculate revenue for each market
            total_revenue = 0
            best_market = None
            
            for market_type, price in current_prices.items():
                revenue = (power / 1000) * price
                if revenue > total_revenue:
                    total_revenue = revenue
                    best_market = market_type
            
            # Calculate cost
            cost = self._calculate_operational_cost(power)
            
            # Calculate profit
            profit = total_revenue - cost
            
            if profit > best_profit:
                best_profit = profit
                best_decision = OptimizationDecision(
                    timestamp=datetime.now(),
                    decision_type="profit_optimization",
                    power_output=power,
                    revenue=total_revenue,
                    cost=cost,
                    profit=profit,
                    market_type=best_market,
                    confidence=0.95
                )
        
        if best_decision:
            self.logger.info(f"Profit optimization: {best_decision.power_output:.1f} kW, Profit: ${best_decision.profit:.2f}")
        
        return best_decision
    
    def _optimize_risk_adjusted(self, current_prices: Dict[MarketType, float]) -> Optional[OptimizationDecision]:
        """Optimize for risk-adjusted returns"""
        if not current_prices:
            return None
        
        # Calculate price volatility
        prices = list(current_prices.values())
        volatility = np.std(prices) / np.mean(prices) if prices else 0
        
        # Adjust for risk
        if volatility > self.volatility_threshold:
            # High volatility - reduce exposure
            risk_factor = 1 - (volatility - self.volatility_threshold)
        else:
            # Low volatility - normal operation
            risk_factor = 1.0
        
        # Apply risk adjustment to profit optimization
        decision = self._optimize_profit(current_prices)
        if decision:
            decision.power_output *= risk_factor
            decision.revenue *= risk_factor
            decision.profit = decision.revenue - decision.cost
            decision.decision_type = "risk_adjusted"
            decision.confidence *= risk_factor
        
        return decision
    
    def _optimize_sustainable(self, current_prices: Dict[MarketType, float]) -> Optional[OptimizationDecision]:
        """Optimize for sustainable operation"""
        if not current_prices:
            return None
        
        # Consider environmental factors and long-term sustainability
        # This is a simplified implementation
        decision = self._optimize_profit(current_prices)
        if decision:
            # Apply sustainability factor (reduce output slightly)
            sustainability_factor = 0.9
            decision.power_output *= sustainability_factor
            decision.revenue *= sustainability_factor
            decision.profit = decision.revenue - decision.cost
            decision.decision_type = "sustainable"
        
        return decision
    
    def _calculate_operational_cost(self, power_output: float) -> float:
        """Calculate operational cost for given power output"""
        # Variable costs
        variable_cost = (power_output / 1000) * self.operational_costs['variable_cost']
        fuel_cost = (power_output / 1000) * self.operational_costs['fuel_cost']
        maintenance_cost = (power_output / 1000) * self.operational_costs['maintenance_cost']
        
        # Fixed costs (prorated per hour)
        fixed_cost = self.operational_costs['fixed_cost'] / 24  # Daily cost / 24 hours
        
        total_cost = variable_cost + fuel_cost + maintenance_cost + fixed_cost
        
        return total_cost
    
    def _update_economic_metrics(self, dt: float):
        """Update economic performance metrics"""
        if not self.optimization_decisions:
            return
        
        # Calculate totals from recent decisions
        recent_decisions = self.optimization_decisions[-100:]  # Last 100 decisions
        
        total_revenue = sum(d.revenue for d in recent_decisions)
        total_cost = sum(d.cost for d in recent_decisions)
        total_profit = sum(d.profit for d in recent_decisions)
        
        # Update metrics
        self.economic_metrics.total_revenue = total_revenue
        self.economic_metrics.total_cost = total_cost
        self.economic_metrics.total_profit = total_profit
        
        # Calculate profit margin
        if total_revenue > 0:
            self.economic_metrics.profit_margin = total_profit / total_revenue
        
        # Calculate ROI (simplified)
        total_investment = 1000000.0  # $1M investment
        if total_investment > 0:
            self.economic_metrics.roi = total_profit / total_investment
    
    def _update_performance_metrics(self, dt: float):
        """Update performance metrics"""
        if not self.optimization_decisions:
            return
        
        # Calculate optimization accuracy
        recent_decisions = self.optimization_decisions[-50:]
        if recent_decisions:
            accuracies = [d.confidence for d in recent_decisions]
            self.performance_metrics['optimization_accuracy'] = np.mean(accuracies)
        
        # Calculate forecast accuracy (simplified)
        if len(self.market_prices) > 10:
            actual_prices = [p.price for p in self.market_prices[-10:]]
            forecast_prices = [p.price for p in self.price_forecast[-10:]] if self.price_forecast else actual_prices
            
            if len(forecast_prices) == len(actual_prices):
                errors = [abs(a - f) / a for a, f in zip(actual_prices, forecast_prices) if a > 0]
                if errors:
                    self.performance_metrics['forecast_accuracy'] = 1 - np.mean(errors)
    
    def set_optimization_mode(self, mode: OptimizationMode):
        """Set optimization mode"""
        self.current_mode = mode
        self.logger.info(f"Optimization mode set to: {mode.value}")
    
    def set_market_participation(self, market_type: MarketType, participate: bool):
        """Set market participation"""
        self.market_participation[market_type] = participate
        self.logger.info(f"Market participation for {market_type.value}: {participate}")
    
    def set_operational_costs(self, costs: Dict[str, float]):
        """Set operational costs"""
        self.operational_costs.update(costs)
        self.logger.info("Operational costs updated")
    
    def set_revenue_streams(self, streams: Dict[MarketType, Dict[str, float]]):
        """Set revenue streams"""
        self.revenue_streams.update(streams)
        self.logger.info("Revenue streams updated")
    
    def set_risk_parameters(self, risk_tolerance: float, volatility_threshold: float):
        """Set risk parameters"""
        self.risk_tolerance = risk_tolerance
        self.volatility_threshold = volatility_threshold
        self.logger.info(f"Risk parameters updated: tolerance={risk_tolerance}, threshold={volatility_threshold}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current optimizer status"""
        return {
            'is_active': self.is_active,
            'optimization_mode': self.current_mode.value,
            'market_participation': {k.value: v for k, v in self.market_participation.items()},
            'current_prices': self._get_current_market_prices(),
            'optimization_horizon': self.optimization_horizon
        }
    
    def get_economic_metrics(self) -> EconomicMetrics:
        """Get economic performance metrics"""
        return self.economic_metrics
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()
    
    def get_optimization_decisions(self, duration: timedelta = timedelta(hours=24)) -> List[OptimizationDecision]:
        """Get optimization decisions for specified duration"""
        cutoff_time = datetime.now() - duration
        return [d for d in self.optimization_decisions if d.timestamp >= cutoff_time]
    
    def get_market_prices(self, duration: timedelta = timedelta(hours=24)) -> List[MarketPrice]:
        """Get market prices for specified duration"""
        cutoff_time = datetime.now() - duration
        return [p for p in self.market_prices if p.timestamp >= cutoff_time]
    
    def clear_history(self):
        """Clear optimization and market history"""
        self.optimization_decisions.clear()
        self.market_prices.clear()
        self.price_forecast.clear()
        self.logger.info("History cleared")
    
    def reset_economic_metrics(self):
        """Reset economic metrics"""
        self.economic_metrics = EconomicMetrics(
            total_revenue=0.0,
            total_cost=0.0,
            total_profit=0.0,
            profit_margin=0.0,
            roi=0.0,
            payback_period=0.0,
            net_present_value=0.0,
            internal_rate_of_return=0.0
        )
        
        self.logger.info("Economic metrics reset") 