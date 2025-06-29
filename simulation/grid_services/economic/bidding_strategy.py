"""
Bidding Strategy - Phase 7 Week 5

Provides intelligent bidding strategy optimization for various electricity markets
including dynamic pricing, risk management, and portfolio optimization.

This module uses machine learning and optimization techniques to maximize revenue
while managing market risks and operational constraints.
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np


class BiddingStrategy(Enum):
    """Available bidding strategies"""

    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    ADAPTIVE = "adaptive"
    MARGINAL_COST = "marginal_cost"
    MARKUP_BASED = "markup_based"


class RiskLevel(Enum):
    """Risk tolerance levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class BidRecommendation:
    """Bid recommendation from strategy"""

    service_type: str
    market_type: str
    capacity_mw: float
    price_mwh: float
    duration_hours: float
    confidence: float
    expected_revenue: float
    risk_score: float
    reasoning: str
    alternative_bids: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MarketConditions:
    """Current market conditions for strategy"""

    current_price: float
    price_volatility: float
    demand_forecast: float
    supply_margin: float
    congestion_factor: float
    weather_impact: float
    time_of_day_factor: float
    seasonal_factor: float


@dataclass
class OperationalConstraints:
    """Operational constraints for bidding"""

    max_capacity: float
    min_capacity: float
    ramp_rate: float
    minimum_runtime: float
    startup_cost: float
    variable_cost: float
    efficiency: float
    availability: float


class BiddingStrategyController:
    """
    Advanced bidding strategy controller

    Optimizes bidding decisions across multiple markets using various strategies,
    risk management, and machine learning techniques.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize bidding strategy controller

        Args:
            config: Bidding strategy configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Strategy parameters
        self.default_strategy = BiddingStrategy(
            config.get("default_strategy", "balanced")
        )
        self.risk_tolerance = RiskLevel(config.get("risk_tolerance", "medium"))
        self.profit_margin_target = config.get("profit_margin_target", 0.15)
        self.max_exposure_ratio = config.get("max_exposure_ratio", 0.7)

        # Market-specific parameters
        self.market_weights = config.get(
            "market_weights",
            {"energy_rt": 0.4, "energy_da": 0.3, "freq_reg": 0.2, "spinning_res": 0.1},
        )

        # Learning parameters
        self.learning_rate = config.get("learning_rate", 0.01)
        self.memory_window = config.get("memory_window_hours", 168)  # 1 week

        # Strategy state
        self.historical_bids = []
        self.performance_history = []
        self.market_patterns = {}
        self.current_portfolio = {}

        # Risk management
        self.position_limits = config.get(
            "position_limits",
            {
                "max_daily_exposure": 100.0,
                "max_hourly_exposure": 50.0,
                "concentration_limit": 0.3,
            },
        )

        # Performance tracking
        self.strategy_performance = {
            "total_revenue": 0.0,
            "win_rate": 0.0,
            "average_margin": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
        }

        self.logger.info(
            f"Bidding strategy initialized with {self.default_strategy.value} strategy"
        )

    def generate_bid_recommendations(
        self,
        market_conditions: MarketConditions,
        operational_constraints: OperationalConstraints,
        forecast_horizon: int = 24,
    ) -> List[BidRecommendation]:
        """
        Generate optimal bid recommendations

        Args:
            market_conditions: Current market state
            operational_constraints: System operational limits
            forecast_horizon: Hours to optimize over

        Returns:
            List of bid recommendations
        """
        try:
            recommendations = []

            # Get market opportunities
            opportunities = self._identify_market_opportunities(
                market_conditions, forecast_horizon
            )

            # Apply bidding strategy for each opportunity
            for opportunity in opportunities:
                # Calculate optimal bid parameters
                bid_params = self._calculate_optimal_bid(
                    opportunity, market_conditions, operational_constraints
                )

                if bid_params:
                    # Assess risk and confidence
                    risk_assessment = self._assess_bid_risk(
                        bid_params, market_conditions
                    )

                    # Create recommendation
                    recommendation = BidRecommendation(
                        service_type=opportunity["service_type"],
                        market_type=opportunity["market_type"],
                        capacity_mw=bid_params["capacity"],
                        price_mwh=bid_params["price"],
                        duration_hours=bid_params["duration"],
                        confidence=bid_params["confidence"],
                        expected_revenue=bid_params["expected_revenue"],
                        risk_score=risk_assessment["risk_score"],
                        reasoning=bid_params["reasoning"],
                        alternative_bids=bid_params.get("alternatives", []),
                    )

                    recommendations.append(recommendation)

            # Portfolio optimization
            optimized_recommendations = self._optimize_portfolio(recommendations)

            self.logger.info(
                f"Generated {len(optimized_recommendations)} bid recommendations"
            )
            return optimized_recommendations

        except Exception as e:
            self.logger.error(f"Error generating bid recommendations: {e}")
            return []

    def update_strategy_performance(self, bid_results: List[Dict[str, Any]]):
        """
        Update strategy performance based on bid results

        Args:
            bid_results: Results of previous bids
        """
        try:
            for result in bid_results:
                # Store historical performance
                self.performance_history.append(
                    {
                        "timestamp": datetime.now(),
                        "bid_id": result["bid_id"],
                        "strategy": result.get("strategy", self.default_strategy.value),
                        "success": result["accepted"],
                        "revenue": result.get("revenue", 0.0),
                        "expected_revenue": result.get("expected_revenue", 0.0),
                        "market_type": result["market_type"],
                    }
                )

            # Update performance metrics
            self._update_performance_metrics()

            # Adapt strategy if using adaptive mode
            if self.default_strategy == BiddingStrategy.ADAPTIVE:
                self._adapt_strategy()

            self.logger.info(
                f"Updated strategy performance with {len(bid_results)} results"
            )

        except Exception as e:
            self.logger.error(f"Error updating strategy performance: {e}")

    def get_strategy_recommendations(self, market_type: str) -> Dict[str, Any]:
        """
        Get strategy recommendations for a specific market

        Args:
            market_type: Type of market to get recommendations for

        Returns:
            Strategy recommendations
        """
        try:
            # Analyze market patterns
            patterns = self._analyze_market_patterns(market_type)

            # Get current performance
            current_performance = self._get_market_performance(market_type)

            # Generate recommendations
            recommendations = {
                "suggested_strategy": self._suggest_optimal_strategy(
                    market_type, patterns
                ),
                "risk_adjustment": self._calculate_risk_adjustment(market_type),
                "markup_range": self._calculate_markup_range(market_type),
                "volume_guidance": self._calculate_volume_guidance(market_type),
                "timing_recommendations": self._get_timing_recommendations(market_type),
                "performance_summary": current_performance,
            }

            return recommendations

        except Exception as e:
            self.logger.error(f"Error getting strategy recommendations: {e}")
            return {}

    def calculate_bid_price(
        self,
        service_type: str,
        base_cost: float,
        market_conditions: MarketConditions,
        strategy: Optional[BiddingStrategy] = None,
    ) -> float:
        """
        Calculate optimal bid price for a service

        Args:
            service_type: Type of service being bid
            base_cost: Base cost of providing service
            market_conditions: Current market state
            strategy: Bidding strategy to use

        Returns:
            Optimal bid price
        """
        try:
            strategy = strategy or self.default_strategy

            # Calculate base markup
            markup = self._calculate_base_markup(strategy, service_type)

            # Apply market condition adjustments
            market_adjustment = self._calculate_market_adjustment(
                market_conditions, service_type
            )

            # Apply risk premium
            risk_premium = self._calculate_risk_premium(service_type, market_conditions)

            # Calculate final price
            price = base_cost * (1 + markup + market_adjustment + risk_premium)

            # Apply bounds checking
            price = self._apply_price_bounds(price, service_type, market_conditions)

            self.logger.debug(f"Calculated bid price: ${price:.2f} for {service_type}")
            return price

        except Exception as e:
            self.logger.error(f"Error calculating bid price: {e}")
            return base_cost * 1.1  # Default 10% markup

    def assess_portfolio_risk(self) -> Dict[str, float]:
        """
        Assess current portfolio risk exposure

        Returns:
            Risk assessment metrics
        """
        try:
            # Calculate concentration risk
            concentration_risk = self._calculate_concentration_risk()

            # Calculate market risk
            market_risk = self._calculate_market_risk()

            # Calculate operational risk
            operational_risk = self._calculate_operational_risk()

            # Calculate liquidity risk
            liquidity_risk = self._calculate_liquidity_risk()

            # Overall risk score
            overall_risk = (
                np.sqrt(
                    concentration_risk**2
                    + market_risk**2
                    + operational_risk**2
                    + liquidity_risk**2
                )
                / 2.0
            )

            return {
                "overall_risk": overall_risk,
                "concentration_risk": concentration_risk,
                "market_risk": market_risk,
                "operational_risk": operational_risk,
                "liquidity_risk": liquidity_risk,
                "risk_budget_utilization": overall_risk / self._get_risk_budget(),
            }

        except Exception as e:
            self.logger.error(f"Error assessing portfolio risk: {e}")
            return {"overall_risk": 0.5}  # Default medium risk

    def get_status(self) -> Dict[str, Any]:
        """Get current bidding strategy status"""
        return {
            "current_strategy": self.default_strategy.value,
            "risk_tolerance": self.risk_tolerance.value,
            "performance_metrics": self.strategy_performance.copy(),
            "portfolio_risk": self.assess_portfolio_risk(),
            "active_positions": len(self.current_portfolio),
            "historical_bids": len(self.historical_bids),
        }

    def reset(self):
        """Reset bidding strategy state"""
        self.historical_bids.clear()
        self.performance_history.clear()
        self.market_patterns.clear()
        self.current_portfolio.clear()

        self.strategy_performance = {
            "total_revenue": 0.0,
            "win_rate": 0.0,
            "average_margin": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
        }

        self.logger.info("Bidding strategy reset")

    def _identify_market_opportunities(
        self, conditions: MarketConditions, horizon: int
    ) -> List[Dict[str, Any]]:
        """Identify profitable market opportunities"""
        opportunities = []

        # Energy markets
        if conditions.current_price > 40:  # Profitable threshold
            opportunities.append(
                {
                    "service_type": "energy",
                    "market_type": "energy_rt",
                    "opportunity_score": min(conditions.current_price / 50.0, 2.0),
                    "time_horizon": 1,
                }
            )

        # Frequency regulation
        if conditions.price_volatility > 0.1:  # High volatility = regulation value
            opportunities.append(
                {
                    "service_type": "frequency_regulation",
                    "market_type": "freq_reg",
                    "opportunity_score": conditions.price_volatility * 10,
                    "time_horizon": 4,
                }
            )

        # Spinning reserve
        if conditions.supply_margin < 0.15:  # Tight supply
            opportunities.append(
                {
                    "service_type": "spinning_reserve",
                    "market_type": "spinning_res",
                    "opportunity_score": (0.15 - conditions.supply_margin) * 20,
                    "time_horizon": 8,
                }
            )

        return opportunities

    def _calculate_optimal_bid(
        self,
        opportunity: Dict[str, Any],
        conditions: MarketConditions,
        constraints: OperationalConstraints,
    ) -> Optional[Dict[str, Any]]:
        """Calculate optimal bid parameters for an opportunity"""
        try:
            service_type = opportunity["service_type"]

            # Calculate capacity allocation
            max_available = constraints.max_capacity * constraints.availability
            allocated_capacity = min(
                max_available * 0.8,  # Reserve some capacity
                opportunity["opportunity_score"] * 10,  # Scale with opportunity
            )

            if allocated_capacity < constraints.min_capacity:
                return None

            # Calculate base price
            marginal_cost = constraints.variable_cost / constraints.efficiency
            markup = self._calculate_base_markup(self.default_strategy, service_type)
            price = marginal_cost * (1 + markup)

            # Apply market adjustments
            market_factor = 1.0 + (conditions.price_volatility - 0.1) * 2
            price *= market_factor

            # Calculate expected revenue
            clearing_probability = self._estimate_clearing_probability(
                price, conditions
            )
            expected_revenue = (
                allocated_capacity
                * price
                * opportunity["time_horizon"]
                * clearing_probability
            )

            # Calculate confidence
            confidence = min(
                clearing_probability * opportunity["opportunity_score"], 1.0
            )

            return {
                "capacity": allocated_capacity,
                "price": price,
                "duration": opportunity["time_horizon"],
                "expected_revenue": expected_revenue,
                "confidence": confidence,
                "reasoning": f"Targeting {service_type} with {confidence:.1%} confidence",
            }

        except Exception as e:
            self.logger.error(f"Error calculating optimal bid: {e}")
            return None

    def _assess_bid_risk(
        self, bid_params: Dict[str, Any], conditions: MarketConditions
    ) -> Dict[str, float]:
        """Assess risk of a specific bid"""
        # Price risk
        price_risk = conditions.price_volatility

        # Volume risk
        volume_risk = 1.0 - bid_params["confidence"]

        # Market risk
        market_risk = abs(conditions.demand_forecast - 1.0) * 0.5

        # Overall risk score
        risk_score = np.sqrt(
            price_risk**2 + volume_risk**2 + market_risk**2
        ) / math.sqrt(3)

        return {
            "risk_score": risk_score,
            "price_risk": price_risk,
            "volume_risk": volume_risk,
            "market_risk": market_risk,
        }

    def _optimize_portfolio(
        self, recommendations: List[BidRecommendation]
    ) -> List[BidRecommendation]:
        """Optimize portfolio of bid recommendations"""
        if not recommendations:
            return recommendations

        # Sort by risk-adjusted return
        scored_recs = []
        for rec in recommendations:
            risk_adjusted_return = rec.expected_revenue / max(rec.risk_score, 0.1)
            scored_recs.append((risk_adjusted_return, rec))

        scored_recs.sort(key=lambda x: x[0], reverse=True)

        # Select optimal portfolio within risk limits
        optimized = []
        total_capacity = 0.0
        total_risk = 0.0

        for score, rec in scored_recs:
            # Check capacity limits
            if (
                total_capacity + rec.capacity_mw
                > self.position_limits["max_daily_exposure"]
            ):
                continue

            # Check risk limits
            portfolio_risk = math.sqrt(total_risk**2 + rec.risk_score**2)
            if portfolio_risk > self._get_risk_budget():
                continue

            optimized.append(rec)
            total_capacity += rec.capacity_mw
            total_risk = portfolio_risk

        return optimized

    def _calculate_base_markup(
        self, strategy: BiddingStrategy, service_type: str
    ) -> float:
        """Calculate base markup for strategy and service type"""
        base_markups = {
            BiddingStrategy.CONSERVATIVE: 0.25,
            BiddingStrategy.BALANCED: 0.15,
            BiddingStrategy.AGGRESSIVE: 0.08,
            BiddingStrategy.MARGINAL_COST: 0.02,
        }

        service_multipliers = {
            "energy": 1.0,
            "frequency_regulation": 1.2,
            "spinning_reserve": 1.1,
            "voltage_support": 1.3,
        }

        base_markup = base_markups.get(strategy, 0.15)
        service_multiplier = service_multipliers.get(service_type, 1.0)

        return base_markup * service_multiplier

    def _calculate_market_adjustment(
        self, conditions: MarketConditions, service_type: str
    ) -> float:
        """Calculate market condition adjustment factor"""
        # Supply/demand balance
        supply_adjustment = (1.0 - conditions.supply_margin) * 0.2

        # Volatility adjustment
        volatility_adjustment = conditions.price_volatility * 0.1

        # Time-of-day adjustment
        tod_adjustment = (conditions.time_of_day_factor - 1.0) * 0.1

        return supply_adjustment + volatility_adjustment + tod_adjustment

    def _calculate_risk_premium(
        self, service_type: str, conditions: MarketConditions
    ) -> float:
        """Calculate risk premium for service and conditions"""
        base_risk_premium = {
            "energy": 0.02,
            "frequency_regulation": 0.05,
            "spinning_reserve": 0.03,
            "voltage_support": 0.08,
        }.get(service_type, 0.03)

        # Adjust for market volatility
        volatility_adjustment = conditions.price_volatility * 0.1

        # Adjust for risk tolerance
        risk_multiplier = {
            RiskLevel.LOW: 1.5,
            RiskLevel.MEDIUM: 1.0,
            RiskLevel.HIGH: 0.5,
        }.get(self.risk_tolerance, 1.0)

        return (base_risk_premium + volatility_adjustment) * risk_multiplier

    def _apply_price_bounds(
        self, price: float, service_type: str, conditions: MarketConditions
    ) -> float:
        """Apply price bounds and sanity checks"""
        # Market-specific bounds
        min_prices = {
            "energy": 10.0,
            "frequency_regulation": 15.0,
            "spinning_reserve": 8.0,
            "voltage_support": 20.0,
        }

        max_prices = {
            "energy": 500.0,
            "frequency_regulation": 200.0,
            "spinning_reserve": 150.0,
            "voltage_support": 300.0,
        }

        min_price = min_prices.get(service_type, 5.0)
        max_price = max_prices.get(service_type, 1000.0)

        # Apply current market bounds
        market_min = conditions.current_price * 0.5
        market_max = conditions.current_price * 3.0

        return np.clip(price, max(min_price, market_min), min(max_price, market_max))

    def _estimate_clearing_probability(
        self, price: float, conditions: MarketConditions
    ) -> float:
        """Estimate probability of bid clearing at given price"""
        # Simple model based on price vs market price
        price_ratio = price / max(conditions.current_price, 1.0)

        if price_ratio <= 0.8:
            return 0.95
        elif price_ratio <= 1.0:
            return 0.8
        elif price_ratio <= 1.2:
            return 0.6
        elif price_ratio <= 1.5:
            return 0.3
        else:
            return 0.1

    def _get_risk_budget(self) -> float:
        """Get current risk budget based on tolerance"""
        risk_budgets = {RiskLevel.LOW: 0.3, RiskLevel.MEDIUM: 0.5, RiskLevel.HIGH: 0.8}
        return risk_budgets.get(self.risk_tolerance, 0.5)

    def _calculate_concentration_risk(self) -> float:
        """Calculate portfolio concentration risk"""
        if not self.current_portfolio:
            return 0.0

        # Simplified concentration calculation
        total_exposure = sum(
            pos.get("exposure", 0) for pos in self.current_portfolio.values()
        )
        if total_exposure == 0:
            return 0.0

        # Calculate Herfindahl index
        hhi = sum(
            (pos.get("exposure", 0) / total_exposure) ** 2
            for pos in self.current_portfolio.values()
        )
        return min(hhi, 1.0)

    def _calculate_market_risk(self) -> float:
        """Calculate market risk exposure"""
        # Simplified market risk based on price volatility
        return 0.3  # Placeholder

    def _calculate_operational_risk(self) -> float:
        """Calculate operational risk exposure"""
        # Simplified operational risk
        return 0.2  # Placeholder

    def _calculate_liquidity_risk(self) -> float:
        """Calculate liquidity risk exposure"""
        # Simplified liquidity risk
        return 0.15  # Placeholder

    def _update_performance_metrics(self):
        """Update strategy performance metrics"""
        if not self.performance_history:
            return

        recent_performance = self.performance_history[-50:]  # Last 50 bids

        # Win rate
        wins = sum(1 for p in recent_performance if p["success"])
        self.strategy_performance["win_rate"] = wins / len(recent_performance)

        # Average margin
        successful_bids = [p for p in recent_performance if p["success"]]
        if successful_bids:
            margins = [
                (p["revenue"] - p["expected_revenue"]) / max(p["expected_revenue"], 1)
                for p in successful_bids
            ]
            self.strategy_performance["average_margin"] = float(np.mean(margins))

        # Total revenue
        self.strategy_performance["total_revenue"] = sum(
            p["revenue"] for p in self.performance_history
        )

    def _adapt_strategy(self):
        """Adapt strategy based on performance"""
        if len(self.performance_history) < 20:
            return

        recent_win_rate = self.strategy_performance["win_rate"]

        # Adjust strategy based on performance
        if recent_win_rate < 0.3:
            # Too aggressive, become more conservative
            self.profit_margin_target *= 1.1
        elif recent_win_rate > 0.8:
            # Too conservative, become more aggressive
            self.profit_margin_target *= 0.95

    def _analyze_market_patterns(self, market_type: str) -> Dict[str, Any]:
        """Analyze historical market patterns"""
        # Placeholder for pattern analysis
        return {"trend": "stable", "volatility": 0.15, "seasonality": "normal"}

    def _get_market_performance(self, market_type: str) -> Dict[str, float]:
        """Get performance metrics for specific market"""
        market_history = [
            p for p in self.performance_history if p["market_type"] == market_type
        ]

        if not market_history:
            return {}

        return {
            "win_rate": sum(1 for p in market_history if p["success"])
            / len(market_history),
            "total_revenue": sum(p["revenue"] for p in market_history),
            "bid_count": len(market_history),
        }

    def _suggest_optimal_strategy(
        self, market_type: str, patterns: Dict[str, Any]
    ) -> str:
        """Suggest optimal strategy for market type"""
        # Simplified strategy suggestion
        if patterns.get("volatility", 0) > 0.2:
            return BiddingStrategy.CONSERVATIVE.value
        elif patterns.get("trend") == "rising":
            return BiddingStrategy.AGGRESSIVE.value
        else:
            return BiddingStrategy.BALANCED.value

    def _calculate_risk_adjustment(self, market_type: str) -> float:
        """Calculate risk adjustment for market"""
        return 0.05  # Placeholder

    def _calculate_markup_range(self, market_type: str) -> Dict[str, float]:
        """Calculate recommended markup range"""
        return {"min": 0.05, "max": 0.25, "recommended": 0.15}

    def _calculate_volume_guidance(self, market_type: str) -> Dict[str, float]:
        """Calculate volume allocation guidance"""
        return {"min_capacity": 1.0, "max_capacity": 50.0, "optimal_capacity": 25.0}

    def _get_timing_recommendations(self, market_type: str) -> Dict[str, Any]:
        """Get timing recommendations for market"""
        return {
            "best_hours": [9, 10, 11, 17, 18, 19],
            "avoid_hours": [2, 3, 4, 5],
            "peak_opportunity": "18:00",
        }


def create_bidding_strategy(config: Dict[str, Any]) -> BiddingStrategyController:
    """Factory function to create a bidding strategy controller"""
    return BiddingStrategyController(config)
