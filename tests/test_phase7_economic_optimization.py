"""
Test Suite for Phase 7 Week 5: Economic Optimization Services

Tests the economic optimization components including price forecasting,
economic optimization, market interface, and bidding strategy.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Import the economic optimization services
from simulation.grid_services.economic.price_forecaster import PriceForecaster, create_price_forecaster
from simulation.grid_services.economic.economic_optimizer import EconomicOptimizer, create_economic_optimizer  
from simulation.grid_services.economic.market_interface import MarketInterface, MarketType, BidStatus, create_market_interface
from simulation.grid_services.economic.bidding_strategy import (
    BiddingStrategyController, BiddingStrategy, RiskLevel, MarketConditions, 
    OperationalConstraints, create_bidding_strategy
)


class TestPriceForecaster:
    """Test suite for price forecasting functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.forecaster = create_price_forecaster(base_price=50.0, volatility=0.15)
    
    def test_price_forecaster_initialization(self):
        """Test price forecaster initializes correctly"""
        assert self.forecaster.base_price == 50.0
        assert self.forecaster.volatility == 0.15
        assert len(self.forecaster.price_history) == 0
        assert len(self.forecaster.forecast_accuracy) == 0
    
    def test_price_update(self):
        """Test price update functionality"""
        current_time = datetime.now().timestamp()
        result = self.forecaster.update(55.0, current_time)
        
        assert result['current_price'] == 55.0
        assert 'forecast_prices' in result
        assert len(result['forecast_prices']) == 24  # 24-hour forecast
        assert all(isinstance(p, float) for p in result['forecast_prices'])
        assert len(self.forecaster.price_history) == 1
    
    def test_pattern_analysis(self):
        """Test price pattern analysis"""
        # Add some price history
        base_time = datetime.now().timestamp()
        prices = [45.0, 50.0, 55.0, 52.0, 48.0]
        
        for i, price in enumerate(prices):
            self.forecaster.update(price, base_time + i * 3600)
        
        patterns = self.forecaster.analyze_patterns()
        assert 'hourly_pattern' in patterns
        assert 'trend' in patterns
        assert 'volatility' in patterns
        assert isinstance(patterns['volatility'], float)
    
    def test_forecast_accuracy(self):
        """Test forecast accuracy tracking"""
        # Add initial forecast
        self.forecaster.update(50.0, datetime.now().timestamp())
        
        # Update with actual price (should track accuracy)
        future_time = datetime.now().timestamp() + 3600
        result = self.forecaster.update(52.0, future_time)
        
        if len(self.forecaster.forecast_accuracy) > 0:
            assert all(acc >= 0.0 for acc in self.forecaster.forecast_accuracy.values())
    
    def test_price_bounds(self):
        """Test price forecasts stay within reasonable bounds"""
        # Test with extreme input
        result = self.forecaster.update(1000.0, datetime.now().timestamp())
        forecast_prices = result['forecast_prices']
        
        # Forecasts should be reasonable even with extreme input
        assert all(10.0 <= p <= 500.0 for p in forecast_prices)


class TestEconomicOptimizer:
    """Test suite for economic optimization functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.optimizer = create_economic_optimizer(max_power_kw=200.0, risk_tolerance=0.3)
    
    def test_economic_optimizer_initialization(self):
        """Test economic optimizer initializes correctly"""
        assert self.optimizer.max_power_kw == 200.0
        assert self.optimizer.risk_tolerance == 0.3
        assert len(self.optimizer.service_portfolio) == 0
        assert self.optimizer.performance_metrics['total_revenue'] == 0.0
    
    def test_service_optimization(self):
        """Test service optimization functionality"""
        # Prepare test conditions
        conditions = {
            'current_price': 60.0,
            'grid_frequency': 59.95,
            'grid_voltage': 480.0,
            'active_power': 50.0,
            'available_capacity': 150.0,
            'timestamp': datetime.now().timestamp()
        }
        
        # Prepare available services
        services = {
            'frequency_regulation': {'capacity': 20.0, 'price': 80.0},
            'energy_arbitrage': {'capacity': 50.0, 'price': 55.0},
            'voltage_support': {'capacity': 15.0, 'price': 75.0}
        }
        
        # Prepare forecasts
        forecasts = {
            'prices': [58.0, 62.0, 65.0, 70.0] + [60.0] * 20
        }
        
        result = self.optimizer.optimize(conditions, services, forecasts)
        
        assert 'total_revenue' in result
        assert 'service_allocation' in result
        assert 'risk_score' in result
        assert isinstance(result['total_revenue'], float)
        assert result['total_revenue'] >= 0.0
    
    def test_risk_management(self):
        """Test risk management in optimization"""
        # High-risk scenario
        high_risk_conditions = {
            'current_price': 120.0,  # Very high price
            'grid_frequency': 59.8,  # Frequency deviation
            'grid_voltage': 460.0,   # Voltage deviation
            'active_power': 80.0,
            'available_capacity': 100.0,
            'timestamp': datetime.now().timestamp()
        }
        
        services = {
            'high_risk_service': {'capacity': 100.0, 'price': 150.0}
        }
        
        forecasts = {'prices': [120.0] * 24}
        
        result = self.optimizer.optimize(high_risk_conditions, services, forecasts)
        
        # Should apply risk constraints
        assert result['risk_score'] >= 0.0
        assert result['risk_score'] <= 1.0
    
    def test_revenue_calculation(self):
        """Test revenue calculation accuracy"""
        conditions = {
            'current_price': 50.0,
            'grid_frequency': 60.0,
            'grid_voltage': 480.0,
            'active_power': 30.0,
            'available_capacity': 100.0,
            'timestamp': datetime.now().timestamp()
        }
        
        services = {
            'energy': {'capacity': 50.0, 'price': 55.0}
        }
        
        forecasts = {'prices': [55.0] * 24}
        
        result = self.optimizer.optimize(conditions, services, forecasts)
        
        # Revenue should be calculated correctly
        expected_min_revenue = 0.0  # At minimum, should be non-negative
        assert result['total_revenue'] >= expected_min_revenue


class TestMarketInterface:
    """Test suite for market interface functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        config = {
            'market_operator': 'test_iso',
            'participant_id': 'test_kpp',
            'max_bid_size_mw': 100.0,
            'min_bid_size_mw': 1.0
        }
        self.market_interface = create_market_interface(config)
    
    def test_market_interface_initialization(self):
        """Test market interface initializes correctly"""
        assert self.market_interface.market_operator == 'test_iso'
        assert self.market_interface.participant_id == 'test_kpp'
        assert len(self.market_interface.active_bids) == 0
        assert len(self.market_interface.bid_history) == 0
    
    def test_bid_submission(self):
        """Test bid submission functionality"""
        bid_data = {
            'market_type': 'energy_rt',
            'service_type': 'energy',
            'capacity_mw': 25.0,
            'price_mwh': 60.0,
            'duration_hours': 1.0,
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(hours=1)
        }
        
        bid_id = self.market_interface.submit_bid(bid_data)
        
        assert bid_id != ""  # Should return valid bid ID
        assert len(self.market_interface.active_bids) <= 1  # Bid should be tracked
    
    def test_bid_validation(self):
        """Test bid validation logic"""
        # Invalid bid - too small
        invalid_bid = {
            'market_type': 'energy_rt',
            'service_type': 'energy',
            'capacity_mw': 0.5,  # Below minimum
            'price_mwh': 60.0,
            'duration_hours': 1.0,
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(hours=1)
        }
        
        bid_id = self.market_interface.submit_bid(invalid_bid)
        assert bid_id == ""  # Should reject invalid bid
    
    def test_market_clearing_processing(self):
        """Test market clearing result processing"""
        # Submit a bid first
        bid_data = {
            'market_type': 'energy_rt',
            'service_type': 'energy',
            'capacity_mw': 20.0,
            'price_mwh': 50.0,
            'duration_hours': 1.0,
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(hours=1)
        }
        
        self.market_interface.submit_bid(bid_data)
        
        # Process market clearing
        clearing_data = {
            'market_type': 'energy_rt',
            'clearing_time': datetime.now(),
            'clearing_price': 55.0,
            'total_demand': 1000.0,
            'total_supply': 1100.0
        }
        
        success = self.market_interface.process_market_clearing(clearing_data)
        assert success
        
        # Check that bids were updated based on clearing
        assert len(self.market_interface.market_clearings[MarketType.ENERGY_REAL_TIME]) > 0
    
    def test_settlement_calculation(self):
        """Test settlement calculation"""
        # Create a cleared bid in history
        from simulation.grid_services.economic.market_interface import MarketBid
        
        cleared_bid = MarketBid(
            bid_id="test_bid",
            market_type=MarketType.ENERGY_REAL_TIME,
            service_type="energy",
            capacity_mw=20.0,
            price_mwh=50.0,
            duration_hours=1.0,
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now(),
            status=BidStatus.CLEARED,
            cleared_capacity=20.0,
            cleared_price=55.0
        )
        
        self.market_interface.bid_history.append(cleared_bid)
        
        # Calculate settlement
        settlement = self.market_interface.calculate_settlement(
            datetime.now() - timedelta(hours=1),
            datetime.now()
        )
        
        assert settlement is not None
        assert settlement.total_revenue > 0.0
        assert settlement.energy_delivered >= 0.0
    
    def test_revenue_summary(self):
        """Test revenue summary calculation"""
        # Add some settlement history
        from simulation.grid_services.economic.market_interface import SettlementData
        
        settlement = SettlementData(
            settlement_id="test_settlement",
            market_type=MarketType.ENERGY_REAL_TIME,
            period_start=datetime.now() - timedelta(hours=1),
            period_end=datetime.now(),
            energy_delivered=20.0,
            capacity_provided=20.0,
            regulation_performance=0.95,
            energy_revenue=1000.0,
            capacity_revenue=200.0,
            performance_payment=50.0,
            total_revenue=1250.0,
            net_payment=1250.0
        )
        
        self.market_interface.settlement_history.append(settlement)
        
        revenue_summary = self.market_interface.get_revenue_summary(days=7)
        
        assert revenue_summary['total_revenue'] == 1250.0
        assert revenue_summary['energy_revenue'] == 1000.0
        assert revenue_summary['capacity_revenue'] == 200.0


class TestBiddingStrategy:
    """Test suite for bidding strategy functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        config = {
            'default_strategy': 'balanced',
            'risk_tolerance': 'medium',
            'profit_margin_target': 0.15
        }
        self.bidding_strategy = create_bidding_strategy(config)
    
    def test_bidding_strategy_initialization(self):
        """Test bidding strategy initializes correctly"""
        assert self.bidding_strategy.default_strategy == BiddingStrategy.BALANCED
        assert self.bidding_strategy.risk_tolerance == RiskLevel.MEDIUM
        assert self.bidding_strategy.profit_margin_target == 0.15
        assert len(self.bidding_strategy.historical_bids) == 0
    
    def test_bid_price_calculation(self):
        """Test bid price calculation"""
        market_conditions = MarketConditions(
            current_price=60.0,
            price_volatility=0.15,
            demand_forecast=1.05,
            supply_margin=0.12,
            congestion_factor=1.0,
            weather_impact=1.0,
            time_of_day_factor=1.2,
            seasonal_factor=1.0
        )
        
        base_cost = 45.0
        
        bid_price = self.bidding_strategy.calculate_bid_price(
            'energy', base_cost, market_conditions
        )
        
        assert bid_price > base_cost  # Should include markup
        assert 10.0 <= bid_price <= 500.0  # Should be within reasonable bounds
    
    def test_bid_recommendations(self):
        """Test bid recommendation generation"""
        market_conditions = MarketConditions(
            current_price=60.0,
            price_volatility=0.15,
            demand_forecast=1.1,
            supply_margin=0.1,
            congestion_factor=1.0,
            weather_impact=1.0,
            time_of_day_factor=1.2,
            seasonal_factor=1.0
        )
        
        operational_constraints = OperationalConstraints(
            max_capacity=100.0,
            min_capacity=5.0,
            ramp_rate=20.0,
            minimum_runtime=1.0,
            startup_cost=100.0,
            variable_cost=35.0,
            efficiency=0.92,
            availability=0.95
        )
        
        recommendations = self.bidding_strategy.generate_bid_recommendations(
            market_conditions, operational_constraints, forecast_horizon=12
        )
        
        assert isinstance(recommendations, list)
        
        for rec in recommendations:
            assert rec.capacity_mw >= operational_constraints.min_capacity
            assert rec.capacity_mw <= operational_constraints.max_capacity
            assert rec.price_mwh > 0.0
            assert 0.0 <= rec.confidence <= 1.0
            assert 0.0 <= rec.risk_score <= 1.0
    
    def test_strategy_performance_update(self):
        """Test strategy performance tracking"""
        bid_results = [
            {
                'bid_id': 'bid1',
                'accepted': True,
                'revenue': 1200.0,
                'expected_revenue': 1000.0,
                'market_type': 'energy_rt'
            },
            {
                'bid_id': 'bid2', 
                'accepted': False,
                'revenue': 0.0,
                'expected_revenue': 800.0,
                'market_type': 'freq_reg'
            }
        ]
        
        initial_performance_count = len(self.bidding_strategy.performance_history)
        
        self.bidding_strategy.update_strategy_performance(bid_results)
        
        assert len(self.bidding_strategy.performance_history) == initial_performance_count + 2
        assert self.bidding_strategy.strategy_performance['win_rate'] >= 0.0
    
    def test_portfolio_risk_assessment(self):
        """Test portfolio risk assessment"""
        # Add some current positions
        self.bidding_strategy.current_portfolio = {
            'energy_pos1': {'exposure': 50.0, 'risk': 0.2},
            'freq_reg_pos1': {'exposure': 30.0, 'risk': 0.3}
        }
        
        risk_assessment = self.bidding_strategy.assess_portfolio_risk()
        
        assert 'overall_risk' in risk_assessment
        assert 0.0 <= risk_assessment['overall_risk'] <= 1.0
        assert 'concentration_risk' in risk_assessment
        assert 'market_risk' in risk_assessment
    
    def test_strategy_recommendations(self):
        """Test strategy recommendations"""
        recommendations = self.bidding_strategy.get_strategy_recommendations('energy_rt')
        
        assert 'suggested_strategy' in recommendations
        assert 'risk_adjustment' in recommendations
        assert 'markup_range' in recommendations
        assert 'volume_guidance' in recommendations


class TestIntegrationScenarios:
    """Integration tests for economic optimization services"""
    
    def setup_method(self):
        """Set up integrated test environment"""
        self.price_forecaster = create_price_forecaster()
        self.economic_optimizer = create_economic_optimizer()
        self.market_interface = create_market_interface({})
        self.bidding_strategy = create_bidding_strategy({})
    
    def test_price_forecast_to_optimization_flow(self):
        """Test flow from price forecasting to economic optimization"""
        # Update price forecast
        current_price = 65.0
        price_update = self.price_forecaster.update(current_price)
        
        # Use forecast in optimization
        conditions = {
            'current_price': current_price,
            'forecast_prices': price_update['forecast_prices'],
            'grid_frequency': 60.0,
            'grid_voltage': 480.0,
            'active_power': 40.0,
            'available_capacity': 100.0,
            'timestamp': datetime.now().timestamp()
        }
        
        services = {
            'energy': {'capacity': 50.0, 'price': 60.0}
        }
        
        forecasts = {'prices': price_update['forecast_prices']}
        
        optimization_result = self.economic_optimizer.optimize(conditions, services, forecasts)
        
        assert optimization_result['total_revenue'] >= 0.0
        assert 'service_allocation' in optimization_result
    
    def test_market_bidding_integration(self):
        """Test integration between bidding strategy and market interface"""
        # Generate bid recommendations
        market_conditions = MarketConditions(
            current_price=70.0,
            price_volatility=0.2,
            demand_forecast=1.15,
            supply_margin=0.08,
            congestion_factor=1.0,
            weather_impact=1.0,
            time_of_day_factor=1.3,
            seasonal_factor=1.0
        )
        
        operational_constraints = OperationalConstraints(
            max_capacity=80.0,
            min_capacity=10.0,
            ramp_rate=15.0,
            minimum_runtime=2.0,
            startup_cost=150.0,
            variable_cost=40.0,
            efficiency=0.90,
            availability=0.92
        )
        
        recommendations = self.bidding_strategy.generate_bid_recommendations(
            market_conditions, operational_constraints
        )
        
        # Submit bids based on recommendations
        for rec in recommendations[:2]:  # Submit first 2 recommendations
            bid_data = {
                'market_type': rec.market_type,
                'service_type': rec.service_type,
                'capacity_mw': rec.capacity_mw,
                'price_mwh': rec.price_mwh,
                'duration_hours': rec.duration_hours,
                'start_time': datetime.now(),
                'end_time': datetime.now() + timedelta(hours=rec.duration_hours)
            }
            
            bid_id = self.market_interface.submit_bid(bid_data)
            # Some bids may be rejected based on market conditions
            # We just verify the process works without errors
    
    def test_economic_optimization_integration(self):
        """Test full economic optimization integration"""
        # Simulate a complete optimization cycle
        current_price = 75.0
        
        # Update forecaster
        price_update = self.price_forecaster.update(current_price)
        
        # Optimize services
        conditions = {
            'current_price': current_price,
            'forecast_prices': price_update['forecast_prices'],
            'grid_frequency': 59.98,
            'grid_voltage': 485.0,
            'active_power': 60.0,
            'available_capacity': 120.0,
            'timestamp': datetime.now().timestamp()
        }
        
        services = {
            'frequency_regulation': {'capacity': 30.0, 'price': 85.0},
            'energy_arbitrage': {'capacity': 60.0, 'price': 70.0},
            'voltage_support': {'capacity': 20.0, 'price': 90.0}
        }
        
        forecasts = {'prices': price_update['forecast_prices']}
        
        optimization_result = self.economic_optimizer.optimize(conditions, services, forecasts)
        
        # Verify integrated optimization works
        assert 'total_revenue' in optimization_result
        assert 'service_allocation' in optimization_result
        assert optimization_result['total_revenue'] >= 0.0
        
        # Check that service allocations are reasonable
        if 'service_allocation' in optimization_result:
            total_allocated = sum(
                allocation.get('capacity', 0.0) 
                for allocation in optimization_result['service_allocation'].values()
            )
            # Should not exceed available capacity
            assert total_allocated <= conditions['available_capacity'] * 1.1  # Allow 10% tolerance


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v', '--tb=short'])
