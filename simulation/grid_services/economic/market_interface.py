"""
Market Interface - Phase 7 Week 5

Provides market participation functionality including bid submission,
market clearing, settlement processing, and communication with grid operators.

This module handles real-time and day-ahead market operations for
various grid services including energy, ancillary services, and capacity markets.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np


class MarketType(Enum):
    """Types of electricity markets"""

    ENERGY_REAL_TIME = "energy_rt"
    ENERGY_DAY_AHEAD = "energy_da"
    FREQUENCY_REGULATION = "freq_reg"
    SPINNING_RESERVE = "spinning_res"
    NON_SPINNING_RESERVE = "non_spinning_res"
    VOLTAGE_SUPPORT = "voltage_support"
    CAPACITY = "capacity"


class BidStatus(Enum):
    """Status of market bids"""

    PENDING = "pending"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PARTIALLY_FILLED = "partial"
    CLEARED = "cleared"


@dataclass
class MarketBid:
    """Represents a market bid"""

    bid_id: str
    market_type: MarketType
    service_type: str
    capacity_mw: float
    price_mwh: float
    duration_hours: float
    start_time: datetime
    end_time: datetime
    status: BidStatus = BidStatus.PENDING
    cleared_capacity: float = 0.0
    cleared_price: float = 0.0
    revenue: float = 0.0
    submitted_at: Optional[datetime] = None
    cleared_at: Optional[datetime] = None


@dataclass
class MarketClearing:
    """Market clearing results"""

    market_type: MarketType
    clearing_time: datetime
    clearing_price: float
    total_demand: float
    total_supply: float
    marginal_unit: Optional[str] = None


@dataclass
class SettlementData:
    """Settlement and payment data"""

    settlement_id: str
    market_type: MarketType
    period_start: datetime
    period_end: datetime
    energy_delivered: float
    capacity_provided: float
    regulation_performance: float
    energy_revenue: float
    capacity_revenue: float
    performance_payment: float
    total_revenue: float
    penalties: float = 0.0
    net_payment: float = 0.0


class MarketInterface:
    """
    Market Interface for grid services participation

    Handles bid submission, market clearing processing, and settlement
    for various electricity markets and ancillary services.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize market interface

        Args:
            config: Market interface configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Market parameters
        self.market_operator = config.get("market_operator", "generic")
        self.participant_id = config.get("participant_id", "kpp_001")
        self.submission_deadline = config.get("submission_deadline_minutes", 60)
        self.max_bid_size = config.get("max_bid_size_mw", 100.0)
        self.min_bid_size = config.get("min_bid_size_mw", 1.0)

        # Bid tracking
        self.active_bids: Dict[str, MarketBid] = {}
        self.bid_history: List[MarketBid] = []
        self.settlement_history: List[SettlementData] = []

        # Market data
        self.market_clearings: Dict[MarketType, List[MarketClearing]] = {market_type: [] for market_type in MarketType}

        # Performance tracking
        self.performance_metrics = {
            "total_revenue": 0.0,
            "bid_acceptance_rate": 0.0,
            "average_clearing_price": 0.0,
            "capacity_factor": 0.0,
            "regulation_score": 0.0,
        }

        self.logger.info(f"Market interface initialized for operator {self.market_operator}")

    def submit_bid(self, bid_data: Dict[str, Any]) -> str:
        """
        Submit a bid to the market

        Args:
            bid_data: Bid parameters including service type, capacity, price, duration

        Returns:
            Bid ID if successful
        """
        try:
            # Validate bid data
            self._validate_bid_data(bid_data)

            # Create bid
            bid = MarketBid(
                bid_id=f"bid_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.active_bids)}",
                market_type=MarketType(bid_data["market_type"]),
                service_type=bid_data["service_type"],
                capacity_mw=bid_data["capacity_mw"],
                price_mwh=bid_data["price_mwh"],
                duration_hours=bid_data["duration_hours"],
                start_time=bid_data["start_time"],
                end_time=bid_data["end_time"],
                submitted_at=datetime.now(),
            )

            # Submit to market (simulation)
            success = self._submit_to_market(bid)

            if success:
                bid.status = BidStatus.SUBMITTED
                self.active_bids[bid.bid_id] = bid
                self.logger.info(f"Bid {bid.bid_id} submitted successfully")
                return bid.bid_id
            else:
                bid.status = BidStatus.REJECTED
                self.bid_history.append(bid)
                self.logger.warning(f"Bid {bid.bid_id} rejected by market")
                return ""

        except Exception as e:
            self.logger.error(f"Error submitting bid: {e}")
            return ""

    def process_market_clearing(self, clearing_data: Dict[str, Any]) -> bool:
        """
        Process market clearing results

        Args:
            clearing_data: Market clearing information

        Returns:
            True if processed successfully
        """
        try:
            # Create clearing record
            clearing = MarketClearing(
                market_type=MarketType(clearing_data["market_type"]),
                clearing_time=clearing_data["clearing_time"],
                clearing_price=clearing_data["clearing_price"],
                total_demand=clearing_data["total_demand"],
                total_supply=clearing_data["total_supply"],
                marginal_unit=clearing_data.get("marginal_unit"),
            )

            # Store clearing data
            self.market_clearings[clearing.market_type].append(clearing)

            # Update affected bids
            self._update_bid_status(clearing)

            self.logger.info(f"Market clearing processed for {clearing.market_type.value}")
            return True

        except Exception as e:
            self.logger.error(f"Error processing market clearing: {e}")
            return False

    def calculate_settlement(self, period_start: datetime, period_end: datetime) -> Optional[SettlementData]:
        """
        Calculate settlement for a specific period

        Args:
            period_start: Settlement period start
            period_end: Settlement period end

        Returns:
            Settlement data if available
        """
        try:
            # Find relevant cleared bids
            relevant_bids = [
                bid
                for bid in self.bid_history
                if (bid.status == BidStatus.CLEARED and bid.start_time <= period_end and bid.end_time >= period_start)
            ]

            if not relevant_bids:
                return None

            # Calculate revenues
            energy_revenue = sum(
                bid.cleared_capacity * bid.cleared_price * self._calculate_overlap_hours(bid, period_start, period_end)
                for bid in relevant_bids
                if bid.market_type in [MarketType.ENERGY_REAL_TIME, MarketType.ENERGY_DAY_AHEAD]
            )

            capacity_revenue = sum(
                bid.cleared_capacity * bid.cleared_price * self._calculate_overlap_hours(bid, period_start, period_end)
                for bid in relevant_bids
                if bid.market_type in [MarketType.FREQUENCY_REGULATION, MarketType.SPINNING_RESERVE]
            )

            # Simulate performance metrics
            energy_delivered = sum(bid.cleared_capacity for bid in relevant_bids) * 0.95  # 95% delivery
            capacity_provided = sum(bid.cleared_capacity for bid in relevant_bids)
            regulation_performance = np.random.uniform(0.9, 1.0)  # Performance score
            performance_payment = capacity_revenue * (regulation_performance - 0.9) * 0.1

            total_revenue = energy_revenue + capacity_revenue + performance_payment

            # Create settlement
            settlement = SettlementData(
                settlement_id=f"settlement_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                market_type=relevant_bids[0].market_type,  # Primary market
                period_start=period_start,
                period_end=period_end,
                energy_delivered=energy_delivered,
                capacity_provided=capacity_provided,
                regulation_performance=regulation_performance,
                energy_revenue=energy_revenue,
                capacity_revenue=capacity_revenue,
                performance_payment=performance_payment,
                total_revenue=total_revenue,
                net_payment=total_revenue,
            )

            self.settlement_history.append(settlement)
            self._update_performance_metrics()

            self.logger.info(f"Settlement calculated: ${total_revenue:.2f} revenue")
            return settlement

        except Exception as e:
            self.logger.error(f"Error calculating settlement: {e}")
            return None

    def get_market_prices(self, market_type: MarketType, lookback_hours: int = 24) -> List[float]:
        """
        Get recent market prices for a specific market

        Args:
            market_type: Type of market
            lookback_hours: Hours of historical data to return

        Returns:
            List of recent prices
        """
        clearings = self.market_clearings.get(market_type, [])
        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)

        recent_clearings = [c for c in clearings if c.clearing_time >= cutoff_time]

        return [c.clearing_price for c in recent_clearings]

    def get_bid_status(self, bid_id: str) -> Optional[BidStatus]:
        """Get status of a specific bid"""
        if bid_id in self.active_bids:
            return self.active_bids[bid_id].status

        for bid in self.bid_history:
            if bid.bid_id == bid_id:
                return bid.status

        return None

    def get_active_commitments(self) -> List[MarketBid]:
        """Get currently active market commitments"""
        now = datetime.now()
        return [
            bid
            for bid in self.active_bids.values()
            if (bid.status == BidStatus.CLEARED and bid.start_time <= now <= bid.end_time)
        ]

    def get_revenue_summary(self, days: int = 30) -> Dict[str, float]:
        """
        Get revenue summary for specified period

        Args:
            days: Number of days to include

        Returns:
            Revenue breakdown by category
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_settlements = [s for s in self.settlement_history if s.period_start >= cutoff_date]

        return {
            "total_revenue": sum(s.total_revenue for s in recent_settlements),
            "energy_revenue": sum(s.energy_revenue for s in recent_settlements),
            "capacity_revenue": sum(s.capacity_revenue for s in recent_settlements),
            "performance_payments": sum(s.performance_payment for s in recent_settlements),
            "penalties": sum(s.penalties for s in recent_settlements),
            "net_payment": sum(s.net_payment for s in recent_settlements),
            "average_daily_revenue": sum(s.total_revenue for s in recent_settlements) / max(days, 1),
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current market interface status"""
        return {
            "active_bids": len(self.active_bids),
            "total_bids_submitted": len(self.bid_history) + len(self.active_bids),
            "current_commitments": len(self.get_active_commitments()),
            "performance_metrics": self.performance_metrics.copy(),
            "last_settlement": (self.settlement_history[-1].settlement_id if self.settlement_history else None),
        }

    def reset(self):
        """Reset market interface state"""
        self.active_bids.clear()
        self.bid_history.clear()
        self.settlement_history.clear()
        for market_clearings in self.market_clearings.values():
            market_clearings.clear()

        self.performance_metrics = {
            "total_revenue": 0.0,
            "bid_acceptance_rate": 0.0,
            "average_clearing_price": 0.0,
            "capacity_factor": 0.0,
            "regulation_score": 0.0,
        }

        self.logger.info("Market interface reset")

    def _validate_bid_data(self, bid_data: Dict[str, Any]):
        """Validate bid data before submission"""
        required_fields = [
            "market_type",
            "service_type",
            "capacity_mw",
            "price_mwh",
            "duration_hours",
            "start_time",
            "end_time",
        ]

        for field in required_fields:
            if field not in bid_data:
                raise ValueError(f"Missing required field: {field}")

        if bid_data["capacity_mw"] < self.min_bid_size:
            raise ValueError(f"Capacity below minimum: {bid_data['capacity_mw']} < {self.min_bid_size}")

        if bid_data["capacity_mw"] > self.max_bid_size:
            raise ValueError(f"Capacity above maximum: {bid_data['capacity_mw']} > {self.max_bid_size}")

        if bid_data["price_mwh"] <= 0:
            raise ValueError(f"Invalid price: {bid_data['price_mwh']}")

    def _submit_to_market(self, bid: MarketBid) -> bool:
        """Simulate market submission (would be real API call in production)"""
        # Simulate submission success rate based on market conditions
        base_success_rate = 0.85

        # Adjust based on bid competitiveness (simplified)
        if bid.price_mwh < 50:  # Very competitive
            success_rate = min(0.95, base_success_rate + 0.1)
        elif bid.price_mwh > 100:  # Less competitive
            success_rate = max(0.6, base_success_rate - 0.25)
        else:
            success_rate = base_success_rate

        return np.random.random() < success_rate

    def _update_bid_status(self, clearing: MarketClearing):
        """Update bid status based on market clearing"""
        for bid in list(self.active_bids.values()):
            if bid.market_type == clearing.market_type and bid.status == BidStatus.SUBMITTED:

                # Simulate clearing logic
                if bid.price_mwh <= clearing.clearing_price:
                    bid.status = BidStatus.CLEARED
                    bid.cleared_capacity = bid.capacity_mw
                    bid.cleared_price = clearing.clearing_price
                    bid.revenue = bid.cleared_capacity * bid.cleared_price * bid.duration_hours
                    bid.cleared_at = clearing.clearing_time
                else:
                    bid.status = BidStatus.REJECTED

                # Move to history
                self.bid_history.append(bid)
                del self.active_bids[bid.bid_id]

    def _calculate_overlap_hours(self, bid: MarketBid, period_start: datetime, period_end: datetime) -> float:
        """Calculate overlap between bid period and settlement period"""
        overlap_start = max(bid.start_time, period_start)
        overlap_end = min(bid.end_time, period_end)

        if overlap_start >= overlap_end:
            return 0.0

        return (overlap_end - overlap_start).total_seconds() / 3600.0

    def _update_performance_metrics(self):
        """Update performance tracking metrics"""
        if not self.bid_history:
            return

        # Calculate acceptance rate
        accepted_bids = [b for b in self.bid_history if b.status == BidStatus.CLEARED]
        self.performance_metrics["bid_acceptance_rate"] = len(accepted_bids) / len(self.bid_history)

        # Calculate average clearing price
        if accepted_bids:
            self.performance_metrics["average_clearing_price"] = float(
                np.mean([b.cleared_price for b in accepted_bids])
            )

        # Calculate total revenue
        self.performance_metrics["total_revenue"] = sum(s.total_revenue for s in self.settlement_history)

        # Calculate capacity factor (simplified)
        if accepted_bids:
            total_committed = sum(b.cleared_capacity * b.duration_hours for b in accepted_bids)
            total_possible = sum(b.capacity_mw * b.duration_hours for b in self.bid_history)
            self.performance_metrics["capacity_factor"] = total_committed / max(total_possible, 1)

        # Calculate regulation score (simplified)
        if self.settlement_history:
            self.performance_metrics["regulation_score"] = float(
                np.mean([s.regulation_performance for s in self.settlement_history])
            )


def create_market_interface(config: Dict[str, Any]) -> MarketInterface:
    """Factory function to create a market interface"""
    return MarketInterface(config)
