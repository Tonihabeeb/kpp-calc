"""
Performance Metrics Module for Phase 7: Advanced Performance Analysis

This module provides comprehensive performance metrics, analysis, and optimization
algorithms for the KPP pneumatic system.

Key Features:
- Advanced performance metrics calculation
- Energy return on investment (EROI) analysis
- Capacity factor and power factor calculations
- Comparative analysis with baseline systems
- Real-time optimization recommendations
"""

import logging
import time
import math
import statistics
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@dataclass
class PerformanceSnapshot:
    """Complete performance snapshot at a specific time."""
    timestamp: float = field(default_factory=time.time)
    
    # Power Metrics
    electrical_power: float = 0.0      # W - Input electrical power
    mechanical_power: float = 0.0      # W - Output mechanical power
    thermal_power: float = 0.0         # W - Thermal power contribution
    
    # Efficiency Metrics
    instantaneous_efficiency: float = 0.0    # Current efficiency
    compression_efficiency: float = 0.0      # Compression stage efficiency
    expansion_efficiency: float = 0.0        # Expansion stage efficiency
    thermal_efficiency: float = 0.0          # Thermal boost efficiency
    
    # Operational Metrics
    capacity_factor: float = 0.0        # Actual vs rated capacity
    power_factor: float = 0.0           # Power quality metric
    availability: float = 0.0           # System availability
    
    # Environmental Conditions
    ambient_temperature: float = 293.15  # K
    water_temperature: float = 288.15    # K
    depth: float = 10.0                  # m
    pressure_ratio: float = 1.0          # Compression ratio


@dataclass
class EROIAnalysis:
    """Energy Return on Investment analysis."""
    energy_invested: float = 0.0        # J - Total energy invested
    energy_returned: float = 0.0        # J - Total energy returned
    eroi_ratio: float = 0.0             # Energy return ratio
    payback_time: float = 0.0           # s - Energy payback time
    net_energy_gain: float = 0.0        # J - Net energy gain
    
    # Component breakdown
    compressor_investment: float = 0.0   # J - Compressor energy
    control_investment: float = 0.0      # J - Control system energy
    thermal_investment: float = 0.0      # J - Thermal system energy


@dataclass
class CapacityAnalysis:
    """System capacity and utilization analysis."""
    rated_power: float = 0.0            # W - Rated system power
    actual_power: float = 0.0           # W - Actual average power
    peak_power: float = 0.0             # W - Peak power achieved
    capacity_factor: float = 0.0        # Actual/rated capacity
    utilization_factor: float = 0.0     # Operating time fraction
    
    # Performance characteristics
    power_curve_efficiency: float = 0.0  # Power curve performance
    part_load_efficiency: float = 0.0    # Part-load performance
    startup_efficiency: float = 0.0      # Startup performance


class OptimizationTarget(Enum):
    """Optimization targets for system performance."""
    MAXIMIZE_EFFICIENCY = "maximize_efficiency"
    MINIMIZE_ENERGY_CONSUMPTION = "minimize_energy_consumption"
    MAXIMIZE_POWER_OUTPUT = "maximize_power_output"
    OPTIMIZE_THERMAL_BOOST = "optimize_thermal_boost"
    BALANCE_PERFORMANCE = "balance_performance"


@dataclass
class OptimizationRecommendation:
    """System optimization recommendation."""
    target: OptimizationTarget
    parameter: str
    current_value: float
    recommended_value: float
    expected_improvement: float         # Expected improvement (fraction)
    confidence: float                   # Confidence in recommendation (0-1)
    description: str = ""


class PerformanceAnalyzer:
    """
    Advanced performance analysis system for the KPP pneumatic system.
    
    Provides comprehensive performance metrics, EROI analysis, capacity analysis,
    and optimization recommendations.
    """
    
    def __init__(self, 
                 rated_power: float = 5000.0,    # W
                 analysis_window: float = 300.0,  # seconds
                 baseline_efficiency: float = 0.75):
        """
        Initialize the performance analyzer.
        
        Args:
            rated_power: Rated system power (W)
            analysis_window: Analysis window for metrics (seconds)
            baseline_efficiency: Baseline efficiency for comparison
        """
        self.rated_power = rated_power
        self.analysis_window = analysis_window
        self.baseline_efficiency = baseline_efficiency
        
        # Performance tracking
        self.performance_snapshots: List[PerformanceSnapshot] = []
        self.eroi_analyses: List[EROIAnalysis] = []
        self.capacity_analyses: List[CapacityAnalysis] = []
        self.optimization_recommendations: List[OptimizationRecommendation] = []
        
        # Running statistics
        self.total_energy_invested = 0.0
        self.total_energy_returned = 0.0
        self.total_operating_time = 0.0
        self.peak_efficiency_achieved = 0.0
        
        # Performance baselines
        self.efficiency_baseline = baseline_efficiency
        self.power_baseline = rated_power * 0.8  # 80% of rated power
        
        logger.info("PerformanceAnalyzer initialized: rated_power=%.1fW, baseline_eff=%.3f", 
                   rated_power, baseline_efficiency)
    
    def record_performance_snapshot(self,
                                  electrical_power: float,
                                  mechanical_power: float,
                                  thermal_power: float = 0.0,
                                  compression_efficiency: float = 0.0,
                                  expansion_efficiency: float = 0.0,
                                  ambient_temp: float = 293.15,
                                  water_temp: float = 288.15,
                                  depth: float = 10.0) -> PerformanceSnapshot:
        """
        Record a complete performance snapshot.
        
        Args:
            electrical_power: Input electrical power (W)
            mechanical_power: Output mechanical power (W)
            thermal_power: Thermal power contribution (W)
            compression_efficiency: Compression efficiency
            expansion_efficiency: Expansion efficiency
            ambient_temp: Ambient temperature (K)
            water_temp: Water temperature (K)
            depth: Operating depth (m)
        
        Returns:
            PerformanceSnapshot object
        """
        # Calculate derived metrics
        total_output = mechanical_power + thermal_power
        instantaneous_efficiency = total_output / electrical_power if electrical_power > 0 else 0.0
        
        # Thermal efficiency boost
        thermal_efficiency = 1.0 + (thermal_power / mechanical_power) if mechanical_power > 0 else 1.0
        
        # Capacity factor
        capacity_factor = electrical_power / self.rated_power if self.rated_power > 0 else 0.0
        
        # Power factor (simplified - assuming good power quality)
        power_factor = 0.95 if electrical_power > 0 else 0.0
        
        # Availability (based on operational status)
        availability = 1.0 if electrical_power > 0 else 0.0
        
        # Pressure ratio from depth
        pressure_ratio = 1.0 + (depth * 9.81 * 1000) / 101325.0  # Hydrostatic pressure
        
        snapshot = PerformanceSnapshot(
            electrical_power=electrical_power,
            mechanical_power=mechanical_power,
            thermal_power=thermal_power,
            instantaneous_efficiency=instantaneous_efficiency,
            compression_efficiency=compression_efficiency,
            expansion_efficiency=expansion_efficiency,
            thermal_efficiency=thermal_efficiency,
            capacity_factor=capacity_factor,
            power_factor=power_factor,
            availability=availability,
            ambient_temperature=ambient_temp,
            water_temperature=water_temp,
            depth=depth,
            pressure_ratio=pressure_ratio
        )
        
        self.performance_snapshots.append(snapshot)
        
        # Update running statistics
        if instantaneous_efficiency > self.peak_efficiency_achieved:
            self.peak_efficiency_achieved = instantaneous_efficiency
        
        # Maintain rolling window
        self._maintain_rolling_window()
        
        logger.debug("Performance snapshot recorded: power=%.1fW, efficiency=%.3f",
                    electrical_power, instantaneous_efficiency)
        
        return snapshot
    
    def reset_performance_history(self) -> None:
        """
        Reset performance history for fresh analysis.
        
        Useful for testing optimization workflows where you want to
        measure performance after implementing recommendations.
        """
        self.performance_snapshots.clear()
        self.optimization_recommendations.clear()
        logger.info("Performance history reset")
    
    def calculate_eroi_analysis(self, time_window: float = 3600.0) -> EROIAnalysis:
        """
        Calculate Energy Return on Investment analysis.
        
        Args:
            time_window: Analysis time window (seconds)
        
        Returns:
            EROIAnalysis object
        """
        if not self.performance_snapshots:
            return EROIAnalysis()
        
        current_time = time.time()
        recent_snapshots = [s for s in self.performance_snapshots 
                          if current_time - s.timestamp <= time_window]
        
        if not recent_snapshots:
            return EROIAnalysis()
        
        # Calculate energy flows
        total_invested = 0.0
        total_returned = 0.0
        compressor_energy = 0.0
        control_energy = 0.0
        thermal_energy = 0.0
        
        dt = time_window / len(recent_snapshots)  # Average time step
        
        for snapshot in recent_snapshots:
            # Energy invested
            electrical_energy = snapshot.electrical_power * dt
            total_invested += electrical_energy
            
            # Energy returned
            mechanical_energy = snapshot.mechanical_power * dt
            thermal_contribution = snapshot.thermal_power * dt
            total_returned += mechanical_energy + thermal_contribution
            
            # Component breakdown
            compressor_energy += electrical_energy * 0.8  # 80% to compressor
            control_energy += electrical_energy * 0.05    # 5% to control
            thermal_energy += thermal_contribution
        
        # Calculate EROI metrics
        eroi_ratio = total_returned / total_invested if total_invested > 0 else 0.0
        net_energy_gain = total_returned - total_invested
        
        # Payback time (simplified)
        avg_return_rate = total_returned / time_window if time_window > 0 else 0.0
        payback_time = total_invested / avg_return_rate if avg_return_rate > 0 else float('inf')
        
        analysis = EROIAnalysis(
            energy_invested=total_invested,
            energy_returned=total_returned,
            eroi_ratio=eroi_ratio,
            payback_time=payback_time,
            net_energy_gain=net_energy_gain,
            compressor_investment=compressor_energy,
            control_investment=control_energy,
            thermal_investment=thermal_energy
        )
        
        self.eroi_analyses.append(analysis)
        
        logger.info("EROI analysis: ratio=%.2f, payback=%.1fs, net_gain=%.2fkJ",
                   eroi_ratio, payback_time, net_energy_gain/1000)
        
        return analysis
    
    def calculate_capacity_analysis(self, time_window: float = 3600.0) -> CapacityAnalysis:
        """
        Calculate system capacity and utilization analysis.
        
        Args:
            time_window: Analysis time window (seconds)
        
        Returns:
            CapacityAnalysis object
        """
        if not self.performance_snapshots:
            return CapacityAnalysis(rated_power=self.rated_power)
        
        current_time = time.time()
        recent_snapshots = [s for s in self.performance_snapshots 
                          if current_time - s.timestamp <= time_window]
        
        if not recent_snapshots:
            return CapacityAnalysis(rated_power=self.rated_power)
        
        # Power statistics
        power_values = [s.electrical_power for s in recent_snapshots]
        actual_power = statistics.mean(power_values)
        peak_power = max(power_values)
        
        # Capacity factor
        capacity_factor = actual_power / self.rated_power if self.rated_power > 0 else 0.0
        
        # Utilization factor (time operating vs total time)
        operating_snapshots = [s for s in recent_snapshots if s.electrical_power > 0]
        utilization_factor = len(operating_snapshots) / len(recent_snapshots)
        
        # Performance characteristics
        efficiency_values = [s.instantaneous_efficiency for s in operating_snapshots]
        power_curve_efficiency = statistics.mean(efficiency_values) if efficiency_values else 0.0
        
        # Part-load efficiency (efficiency at partial loads)
        part_load_snapshots = [s for s in operating_snapshots 
                              if 0.2 * self.rated_power <= s.electrical_power <= 0.8 * self.rated_power]
        part_load_efficiency = statistics.mean([s.instantaneous_efficiency for s in part_load_snapshots]) \
                              if part_load_snapshots else 0.0
        
        # Startup efficiency (first 10% of operational snapshots)
        startup_count = max(1, len(operating_snapshots) // 10)
        startup_snapshots = operating_snapshots[:startup_count]
        startup_efficiency = statistics.mean([s.instantaneous_efficiency for s in startup_snapshots]) \
                           if startup_snapshots else 0.0
        
        analysis = CapacityAnalysis(
            rated_power=self.rated_power,
            actual_power=actual_power,
            peak_power=peak_power,
            capacity_factor=capacity_factor,
            utilization_factor=utilization_factor,
            power_curve_efficiency=power_curve_efficiency,
            part_load_efficiency=part_load_efficiency,
            startup_efficiency=startup_efficiency
        )
        
        self.capacity_analyses.append(analysis)
        
        logger.info("Capacity analysis: factor=%.3f, utilization=%.3f, efficiency=%.3f",
                   capacity_factor, utilization_factor, power_curve_efficiency)
        
        return analysis
    
    def generate_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """
        Generate optimization recommendations based on performance analysis.
        
        Returns:
            List of OptimizationRecommendation objects
        """
        recommendations = []
        
        if not self.performance_snapshots:
            return recommendations
        
        # Get recent performance data
        recent_snapshots = self.performance_snapshots[-10:]  # Last 10 snapshots
        
        if not recent_snapshots:
            return recommendations
        
        # Calculate current averages
        avg_efficiency = statistics.mean([s.instantaneous_efficiency for s in recent_snapshots])
        avg_power = statistics.mean([s.electrical_power for s in recent_snapshots])
        avg_thermal_efficiency = statistics.mean([s.thermal_efficiency for s in recent_snapshots])
        
        # Efficiency optimization
        if avg_efficiency < self.efficiency_baseline * 0.9:
            improvement = (self.efficiency_baseline - avg_efficiency) / avg_efficiency
            recommendations.append(OptimizationRecommendation(
                target=OptimizationTarget.MAXIMIZE_EFFICIENCY,
                parameter="system_efficiency",
                current_value=avg_efficiency,
                recommended_value=self.efficiency_baseline,
                expected_improvement=improvement,
                confidence=0.8,
                description=f"Current efficiency ({avg_efficiency:.3f}) below baseline ({self.efficiency_baseline:.3f})"
            ))
        
        # Power optimization
        if avg_power < self.power_baseline * 0.8:
            improvement = (self.power_baseline - avg_power) / avg_power
            recommendations.append(OptimizationRecommendation(
                target=OptimizationTarget.MAXIMIZE_POWER_OUTPUT,
                parameter="operating_power",
                current_value=avg_power,
                recommended_value=self.power_baseline,
                expected_improvement=improvement,
                confidence=0.7,
                description=f"Operating power ({avg_power:.1f}W) below optimal range"
            ))
        
        # Thermal optimization
        if avg_thermal_efficiency < 1.1:  # Less than 10% thermal boost
            target_thermal = 1.2  # 20% thermal boost target
            improvement = (target_thermal - avg_thermal_efficiency) / avg_thermal_efficiency
            recommendations.append(OptimizationRecommendation(
                target=OptimizationTarget.OPTIMIZE_THERMAL_BOOST,
                parameter="thermal_efficiency",
                current_value=avg_thermal_efficiency,
                recommended_value=target_thermal,
                expected_improvement=improvement,
                confidence=0.6,
                description="Thermal boost potential underutilized"
            ))
        
        # Pressure optimization based on depth
        current_depths = [s.depth for s in recent_snapshots]
        avg_depth = statistics.mean(current_depths)
        optimal_pressure_ratio = 1.0 + (avg_depth * 9.81 * 1000) / 101325.0 * 1.1  # 10% margin
        
        current_pressure_ratios = [s.pressure_ratio for s in recent_snapshots]
        avg_pressure_ratio = statistics.mean(current_pressure_ratios)
        
        if avg_pressure_ratio < optimal_pressure_ratio * 0.9:
            improvement = (optimal_pressure_ratio - avg_pressure_ratio) / avg_pressure_ratio
            recommendations.append(OptimizationRecommendation(
                target=OptimizationTarget.MAXIMIZE_EFFICIENCY,
                parameter="pressure_ratio",
                current_value=avg_pressure_ratio,
                recommended_value=optimal_pressure_ratio,
                expected_improvement=improvement,
                confidence=0.75,
                description="Compression ratio suboptimal for operating depth"
            ))
        
        # Energy consumption optimization
        recent_power_values = [s.electrical_power for s in recent_snapshots]
        power_variation = max(recent_power_values) - min(recent_power_values)
        avg_power_current = statistics.mean(recent_power_values)
        
        if power_variation > avg_power_current * 0.3:  # High power variation
            target_power = avg_power_current * 0.95  # 5% reduction target
            improvement = 0.05  # 5% energy savings
            recommendations.append(OptimizationRecommendation(
                target=OptimizationTarget.MINIMIZE_ENERGY_CONSUMPTION,
                parameter="power_stability",
                current_value=power_variation,
                recommended_value=target_power * 0.2,  # 20% of average as target variation
                expected_improvement=improvement,
                confidence=0.65,
                description="High power variation indicates efficiency losses"
            ))
        
        self.optimization_recommendations.extend(recommendations)
        
        logger.info("Generated %d optimization recommendations", len(recommendations))
        
        return recommendations
    
    def calculate_power_factor(self, time_window: float = 60.0) -> float:
        """
        Calculate power factor for the system.
        
        Args:
            time_window: Analysis window (seconds)
        
        Returns:
            Power factor (0-1)
        """
        if not self.performance_snapshots:
            return 0.0
        
        current_time = time.time()
        recent_snapshots = [s for s in self.performance_snapshots 
                          if current_time - s.timestamp <= time_window]
        
        if not recent_snapshots:
            return 0.0
        
        # Simplified power factor calculation
        # In a real system, this would consider reactive power
        power_factors = [s.power_factor for s in recent_snapshots]
        return statistics.mean(power_factors)
    
    def calculate_system_availability(self, time_window: float = 3600.0) -> float:
        """
        Calculate system availability over time window.
        
        Args:
            time_window: Analysis window (seconds)
        
        Returns:
            Availability (0-1)
        """
        if not self.performance_snapshots:
            return 0.0
        
        current_time = time.time()
        recent_snapshots = [s for s in self.performance_snapshots 
                          if current_time - s.timestamp <= time_window]
        
        if not recent_snapshots:
            return 0.0
        
        # Calculate availability as fraction of time system was operational
        operational_snapshots = [s for s in recent_snapshots if s.electrical_power > 0]
        availability = len(operational_snapshots) / len(recent_snapshots)
        
        return availability
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.
        
        Returns:
            Dictionary with performance summary
        """
        if not self.performance_snapshots:
            return {}
        
        recent_snapshots = self.performance_snapshots[-10:]  # Last 10 snapshots
        
        # Efficiency metrics
        efficiencies = [s.instantaneous_efficiency for s in recent_snapshots]
        avg_efficiency = statistics.mean(efficiencies)
        peak_efficiency = max(efficiencies)
        
        # Power metrics
        power_values = [s.electrical_power for s in recent_snapshots]
        avg_power = statistics.mean(power_values)
        peak_power = max(power_values)
        
        # Capacity metrics
        capacity_factors = [s.capacity_factor for s in recent_snapshots]
        avg_capacity_factor = statistics.mean(capacity_factors)
        
        # Thermal metrics
        thermal_efficiencies = [s.thermal_efficiency for s in recent_snapshots]
        avg_thermal_efficiency = statistics.mean(thermal_efficiencies)
        
        return {
            'average_efficiency': avg_efficiency,
            'peak_efficiency': peak_efficiency,
            'average_power': avg_power,
            'peak_power': peak_power,
            'capacity_factor': avg_capacity_factor,
            'thermal_efficiency': avg_thermal_efficiency,
            'availability': self.calculate_system_availability(),
            'power_factor': self.calculate_power_factor(),
            'baseline_comparison': avg_efficiency / self.efficiency_baseline,
            'peak_efficiency_achieved': self.peak_efficiency_achieved,
            'recommendation_count': len(self.optimization_recommendations)
        }
    
    def get_trend_analysis(self, window_hours: float = 24.0) -> Dict[str, Any]:
        """
        Get performance trend analysis over extended period.
        
        Args:
            window_hours: Analysis window (hours)
        
        Returns:
            Dictionary with trend analysis
        """
        if not self.performance_snapshots:
            return {}
        
        window_seconds = window_hours * 3600.0
        current_time = time.time()
        
        recent_snapshots = [s for s in self.performance_snapshots 
                          if current_time - s.timestamp <= window_seconds]
        
        if len(recent_snapshots) < 2:
            return {}
        
        # Sort by timestamp
        recent_snapshots.sort(key=lambda x: x.timestamp)
        
        # Calculate trends
        timestamps = [s.timestamp for s in recent_snapshots]
        efficiencies = [s.instantaneous_efficiency for s in recent_snapshots]
        powers = [s.electrical_power for s in recent_snapshots]
        
        # Simple linear trend calculation
        time_deltas = [(t - timestamps[0]) / 3600.0 for t in timestamps]  # Hours from start
        
        if len(time_deltas) > 1:
            # Efficiency trend
            efficiency_trend = np.polyfit(time_deltas, efficiencies, 1)[0]  # Slope
            
            # Power trend
            power_trend = np.polyfit(time_deltas, powers, 1)[0]  # Slope
            
            # Performance stability (coefficient of variation)
            efficiency_stability = statistics.stdev(efficiencies) / statistics.mean(efficiencies)
            power_stability = statistics.stdev(powers) / statistics.mean(powers)
        else:
            efficiency_trend = 0.0
            power_trend = 0.0
            efficiency_stability = 0.0
            power_stability = 0.0
        
        return {
            'efficiency_trend': efficiency_trend,  # Change per hour
            'power_trend': power_trend,            # Change per hour
            'efficiency_stability': efficiency_stability,
            'power_stability': power_stability,
            'data_points': len(recent_snapshots),
            'analysis_window_hours': window_hours
        }
    
    def _maintain_rolling_window(self):
        """Maintain rolling window for data storage."""
        current_time = time.time()
        
        # Remove old performance snapshots
        self.performance_snapshots = [s for s in self.performance_snapshots 
                                    if current_time - s.timestamp <= self.analysis_window]
        
        # Limit optimization recommendations to prevent excessive accumulation
        if len(self.optimization_recommendations) > 100:
            self.optimization_recommendations = self.optimization_recommendations[-50:]


# Factory function for creating standard performance analyzer
def create_standard_performance_analyzer(rated_power: float = 5000.0) -> PerformanceAnalyzer:
    """
    Create a standard performance analyzer with optimal settings for KPP analysis.
    
    Args:
        rated_power: Rated system power (W)
    
    Returns:
        Configured PerformanceAnalyzer instance
    """
    analyzer = PerformanceAnalyzer(
        rated_power=rated_power,
        analysis_window=300.0,    # 5 minute rolling window
        baseline_efficiency=0.80  # 80% baseline efficiency
    )
    
    logger.info("Created standard performance analyzer for KPP pneumatic system")
    return analyzer
