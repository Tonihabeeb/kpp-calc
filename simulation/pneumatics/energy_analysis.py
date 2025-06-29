"""
Energy Analysis Module for Phase 7: Performance Analysis and Optimization

This module provides comprehensive energy accounting and analysis for the KPP pneumatic system,
tracking energy flows from electrical input through pneumatic storage to mechanical work output.

Key Features:
- Complete energy balance calculations
- Real-time efficiency monitoring
- Energy flow tracking and visualization
- Physics-based validation of energy conservation
"""

import logging
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from utils.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@dataclass
class EnergyBalance:
    """Complete energy balance for pneumatic system operations."""

    timestamp: float = field(default_factory=time.time)

    # Input Energy
    electrical_input: float = 0.0  # J - Electrical energy to compressor
    heat_input: float = 0.0  # J - Heat energy from environment

    # Stored Energy
    pneumatic_storage: float = 0.0  # J - Compressed air energy storage
    thermal_storage: float = 0.0  # J - Thermal energy storage

    # Output Energy
    mechanical_work: float = 0.0  # J - Useful mechanical work output
    heat_losses: float = 0.0  # J - Heat losses to environment
    venting_losses: float = 0.0  # J - Energy lost during venting

    # Efficiency Metrics
    compression_efficiency: float = 0.0  # Ratio of ideal vs actual compression work
    expansion_efficiency: float = 0.0  # Ratio of actual vs ideal expansion work
    overall_efficiency: float = 0.0  # Total system efficiency


@dataclass
class PowerMetrics:
    """Real-time power measurements and calculations."""

    timestamp: float = field(default_factory=time.time)

    # Power Inputs
    compressor_power: float = 0.0  # W - Electrical power to compressor
    heat_input_rate: float = 0.0  # W - Rate of heat energy input

    # Power Outputs
    mechanical_power: float = 0.0  # W - Mechanical power output
    heat_loss_rate: float = 0.0  # W - Rate of heat losses

    # Instantaneous Efficiency
    instantaneous_efficiency: float = 0.0  # Current power efficiency


class EnergyFlowType(Enum):
    """Types of energy flows in the pneumatic system."""

    ELECTRICAL_INPUT = "electrical_input"
    COMPRESSION_WORK = "compression_work"
    PNEUMATIC_STORAGE = "pneumatic_storage"
    THERMAL_ENERGY = "thermal_energy"
    MECHANICAL_OUTPUT = "mechanical_output"
    HEAT_LOSS = "heat_loss"
    VENTING_LOSS = "venting_loss"


@dataclass
class EnergyFlow:
    """Individual energy flow measurement."""

    flow_type: EnergyFlowType
    value: float  # J or W depending on context
    timestamp: float = field(default_factory=time.time)
    description: str = ""


class EnergyAnalyzer:
    """
    Comprehensive energy analysis system for the KPP pneumatic system.

    Provides real-time energy balance tracking, efficiency calculations,
    and performance optimization analysis.
    """

    def __init__(
        self, analysis_window: float = 60.0, sampling_rate: float = 10.0  # seconds
    ):  # Hz
        """
        Initialize the energy analyzer.

        Args:
            analysis_window: Time window for rolling averages (seconds)
            sampling_rate: Data sampling frequency (Hz)
        """
        self.analysis_window = analysis_window
        self.sampling_rate = sampling_rate

        # Energy tracking
        self.energy_balances: List[EnergyBalance] = []
        self.power_metrics: List[PowerMetrics] = []
        self.energy_flows: List[EnergyFlow] = []

        # Running totals
        self.cumulative_energy_input = 0.0
        self.cumulative_energy_output = 0.0
        self.cumulative_losses = 0.0

        # Performance tracking
        self.peak_efficiency = 0.0
        self.average_efficiency = 0.0
        self.efficiency_history: List[float] = []

        logger.info(
            "EnergyAnalyzer initialized: window=%.1fs, rate=%.1fHz",
            analysis_window,
            sampling_rate,
        )

    def calculate_compression_energy(
        self,
        initial_pressure: float,
        final_pressure: float,
        volume: float,
        temperature: float,
        compression_mode: str = "isothermal",
    ) -> Dict[str, float]:
        """
        Calculate energy required for air compression.

        Args:
            initial_pressure: Initial pressure (Pa)
            final_pressure: Final pressure (Pa)
            volume: Gas volume (m³)
            temperature: Gas temperature (K)
            compression_mode: 'isothermal', 'adiabatic', or 'mixed'

        Returns:
            Dictionary with energy calculations
        """
        pressure_ratio = final_pressure / initial_pressure

        if compression_mode == "isothermal":
            # Isothermal compression work: W = P1*V1*ln(P2/P1)
            ideal_work = initial_pressure * volume * math.log(pressure_ratio)

        elif compression_mode == "adiabatic":
            # Adiabatic compression work: W = (P2*V2 - P1*V1)/(γ-1)
            gamma = 1.4  # Heat capacity ratio for air
            ideal_work = (initial_pressure * volume / (gamma - 1)) * (
                pressure_ratio ** ((gamma - 1) / gamma) - 1
            )

        else:  # mixed mode
            # Weighted average of isothermal and adiabatic
            isothermal_work = initial_pressure * volume * math.log(pressure_ratio)
            adiabatic_work = (initial_pressure * volume / 0.4) * (
                pressure_ratio ** (0.4 / 1.4) - 1
            )
            ideal_work = 0.5 * (isothermal_work + adiabatic_work)

        # Heat generated during compression
        heat_generated = ideal_work * 0.3  # Typical compression heat fraction

        return {
            "ideal_work": ideal_work,
            "heat_generated": heat_generated,
            "pressure_ratio": pressure_ratio,
        }

    def calculate_expansion_energy(
        self,
        initial_pressure: float,
        final_pressure: float,
        volume: float,
        temperature: float,
        expansion_mode: str = "mixed",
    ) -> Dict[str, float]:
        """
        Calculate energy extracted during air expansion.

        Args:
            initial_pressure: Initial pressure (Pa)
            final_pressure: Final pressure (Pa)
            volume: Gas volume (m³)
            temperature: Gas temperature (K)
            expansion_mode: 'isothermal', 'adiabatic', or 'mixed'

        Returns:
            Dictionary with energy calculations
        """
        pressure_ratio = initial_pressure / final_pressure

        if expansion_mode == "isothermal":
            # Isothermal expansion work: W = P1*V1*ln(P1/P2)
            ideal_work = initial_pressure * volume * math.log(pressure_ratio)

        elif expansion_mode == "adiabatic":
            # Adiabatic expansion work
            gamma = 1.4
            ideal_work = (initial_pressure * volume / (gamma - 1)) * (
                1 - (1 / pressure_ratio) ** ((gamma - 1) / gamma)
            )

        else:  # mixed mode
            # Weighted average
            isothermal_work = initial_pressure * volume * math.log(pressure_ratio)
            adiabatic_work = (initial_pressure * volume / 0.4) * (
                1 - (1 / pressure_ratio) ** (0.4 / 1.4)
            )
            ideal_work = 0.6 * isothermal_work + 0.4 * adiabatic_work

        # Heat absorbed during expansion
        heat_absorbed = ideal_work * 0.2  # Typical expansion heat fraction

        return {
            "ideal_work": ideal_work,
            "heat_absorbed": heat_absorbed,
            "pressure_ratio": pressure_ratio,
        }

    def calculate_pneumatic_storage_energy(
        self, pressure: float, volume: float, reference_pressure: float = 101325.0
    ) -> float:
        """
        Calculate energy stored in compressed air.

        Args:
            pressure: Current pressure (Pa)
            volume: Volume of compressed air (m³)
            reference_pressure: Reference pressure (Pa, typically atmospheric)

        Returns:
            Stored energy (J)
        """
        # Energy stored in compressed air: E = P*V*ln(P/P_ref)
        if pressure <= reference_pressure:
            return 0.0

        stored_energy = (
            reference_pressure * volume * math.log(pressure / reference_pressure)
        )
        return stored_energy

    def calculate_thermal_energy_contribution(
        self,
        air_temperature: float,
        water_temperature: float,
        volume: float,
        heat_transfer_coefficient: float = 100.0,
    ) -> Dict[str, float]:
        """
        Calculate thermal energy contributions to system performance.

        Args:
            air_temperature: Air temperature (K)
            water_temperature: Water temperature (K)
            volume: Air volume (m³)
            heat_transfer_coefficient: Heat transfer coefficient (W/m²K)

        Returns:
            Dictionary with thermal energy calculations
        """
        # Air properties
        air_density = 1.225  # kg/m³ at standard conditions
        air_specific_heat = 1005.0  # J/kg·K

        # Mass of air
        air_mass = air_density * volume

        # Temperature difference
        temp_difference = air_temperature - water_temperature

        # Thermal energy content
        thermal_energy = air_mass * air_specific_heat * temp_difference

        # Heat transfer rate (simplified)
        surface_area = 6 * (volume ** (2 / 3))  # Approximate surface area
        heat_transfer_rate = heat_transfer_coefficient * surface_area * temp_difference

        # Thermal efficiency factor
        thermal_efficiency = 1.0 + (temp_difference / 50.0)  # Simplified relationship

        return {
            "thermal_energy": thermal_energy,
            "heat_transfer_rate": heat_transfer_rate,
            "thermal_efficiency": thermal_efficiency,
            "temperature_difference": temp_difference,
        }

    def record_energy_balance(
        self,
        electrical_input: float,
        pneumatic_storage: float,
        mechanical_output: float,
        heat_losses: float,
        venting_losses: float = 0.0,
    ) -> EnergyBalance:
        """
        Record a complete energy balance measurement.

        Args:
            electrical_input: Electrical energy input (J)
            pneumatic_storage: Energy stored in compressed air (J)
            mechanical_output: Mechanical work output (J)
            heat_losses: Heat energy losses (J)
            venting_losses: Energy lost during venting (J)

        Returns:
            EnergyBalance object
        """
        # Calculate efficiencies
        total_input = electrical_input
        total_output = mechanical_output + heat_losses + venting_losses

        compression_efficiency = (
            pneumatic_storage / electrical_input if electrical_input > 0 else 0.0
        )
        expansion_efficiency = (
            mechanical_output / pneumatic_storage if pneumatic_storage > 0 else 0.0
        )
        overall_efficiency = (
            mechanical_output / electrical_input if electrical_input > 0 else 0.0
        )

        balance = EnergyBalance(
            electrical_input=electrical_input,
            pneumatic_storage=pneumatic_storage,
            mechanical_work=mechanical_output,
            heat_losses=heat_losses,
            venting_losses=venting_losses,
            compression_efficiency=compression_efficiency,
            expansion_efficiency=expansion_efficiency,
            overall_efficiency=overall_efficiency,
        )

        self.energy_balances.append(balance)

        # Update cumulative totals
        self.cumulative_energy_input += electrical_input
        self.cumulative_energy_output += mechanical_output
        self.cumulative_losses += heat_losses + venting_losses

        # Update efficiency tracking
        self.efficiency_history.append(overall_efficiency)
        if overall_efficiency > self.peak_efficiency:
            self.peak_efficiency = overall_efficiency

        # Maintain rolling window
        self._maintain_rolling_window()

        logger.debug(
            "Energy balance recorded: input=%.2fkJ, output=%.2fkJ, efficiency=%.3f",
            electrical_input / 1000,
            mechanical_output / 1000,
            overall_efficiency,
        )

        return balance

    def record_power_metrics(
        self,
        compressor_power: float,
        mechanical_power: float,
        heat_loss_rate: float = 0.0,
    ) -> PowerMetrics:
        """
        Record instantaneous power measurements.

        Args:
            compressor_power: Electrical power to compressor (W)
            mechanical_power: Mechanical power output (W)
            heat_loss_rate: Rate of heat losses (W)

        Returns:
            PowerMetrics object
        """
        instantaneous_efficiency = (
            mechanical_power / compressor_power if compressor_power > 0 else 0.0
        )

        metrics = PowerMetrics(
            compressor_power=compressor_power,
            mechanical_power=mechanical_power,
            heat_loss_rate=heat_loss_rate,
            instantaneous_efficiency=instantaneous_efficiency,
        )

        self.power_metrics.append(metrics)

        # Maintain rolling window
        self._maintain_rolling_window()

        return metrics

    def record_energy_flow(
        self, flow_type: EnergyFlowType, value: float, description: str = ""
    ) -> EnergyFlow:
        """
        Record an individual energy flow measurement.

        Args:
            flow_type: Type of energy flow
            value: Energy flow value (J or W)
            description: Optional description

        Returns:
            EnergyFlow object
        """
        flow = EnergyFlow(flow_type=flow_type, value=value, description=description)

        self.energy_flows.append(flow)

        return flow

    def get_current_efficiency(self) -> Dict[str, float]:
        """
        Get current system efficiency metrics.

        Returns:
            Dictionary with efficiency metrics
        """
        if not self.energy_balances:
            return {
                "overall_efficiency": 0.0,
                "compression_efficiency": 0.0,
                "expansion_efficiency": 0.0,
                "peak_efficiency": 0.0,
                "average_efficiency": 0.0,
            }

        latest_balance = self.energy_balances[-1]

        # Calculate average efficiency over analysis window
        recent_efficiencies = [b.overall_efficiency for b in self.energy_balances[-10:]]
        self.average_efficiency = sum(recent_efficiencies) / len(recent_efficiencies)

        return {
            "overall_efficiency": latest_balance.overall_efficiency,
            "compression_efficiency": latest_balance.compression_efficiency,
            "expansion_efficiency": latest_balance.expansion_efficiency,
            "peak_efficiency": self.peak_efficiency,
            "average_efficiency": self.average_efficiency,
        }

    def get_energy_summary(self) -> Dict[str, float]:
        """
        Get cumulative energy summary.

        Returns:
            Dictionary with energy totals
        """
        return {
            "total_input": self.cumulative_energy_input,
            "total_output": self.cumulative_energy_output,
            "total_losses": self.cumulative_losses,
            "energy_balance": self.cumulative_energy_input
            - self.cumulative_energy_output
            - self.cumulative_losses,
            "cumulative_efficiency": (
                self.cumulative_energy_output / self.cumulative_energy_input
                if self.cumulative_energy_input > 0
                else 0.0
            ),
        }

    def get_power_analysis(self, window_seconds: float = 10.0) -> Dict[str, float]:
        """
        Get power analysis over specified time window.

        Args:
            window_seconds: Analysis window (seconds)

        Returns:
            Dictionary with power analysis
        """
        if not self.power_metrics:
            return {}

        current_time = time.time()
        recent_metrics = [
            m
            for m in self.power_metrics
            if current_time - m.timestamp <= window_seconds
        ]

        if not recent_metrics:
            return {}

        avg_compressor_power = sum(m.compressor_power for m in recent_metrics) / len(
            recent_metrics
        )
        avg_mechanical_power = sum(m.mechanical_power for m in recent_metrics) / len(
            recent_metrics
        )
        avg_efficiency = sum(m.instantaneous_efficiency for m in recent_metrics) / len(
            recent_metrics
        )

        max_power = max(m.compressor_power for m in recent_metrics)
        min_power = min(m.compressor_power for m in recent_metrics)

        return {
            "average_compressor_power": avg_compressor_power,
            "average_mechanical_power": avg_mechanical_power,
            "average_efficiency": avg_efficiency,
            "max_power": max_power,
            "min_power": min_power,
            "power_variation": max_power - min_power,
        }

    def analyze_energy_flows(
        self, window_seconds: float = 60.0
    ) -> Dict[str, Dict[str, float]]:
        """
        Analyze energy flows by type over specified window.

        Args:
            window_seconds: Analysis window (seconds)

        Returns:
            Dictionary with energy flow analysis by type
        """
        if not self.energy_flows:
            return {}

        current_time = time.time()
        recent_flows = [
            f for f in self.energy_flows if current_time - f.timestamp <= window_seconds
        ]

        # Group by flow type
        flow_analysis = {}
        for flow_type in EnergyFlowType:
            type_flows = [f for f in recent_flows if f.flow_type == flow_type]
            if type_flows:
                total_energy = sum(f.value for f in type_flows)
                avg_rate = total_energy / window_seconds
                max_flow = max(f.value for f in type_flows)
                min_flow = min(f.value for f in type_flows)

                flow_analysis[flow_type.value] = {
                    "total_energy": total_energy,
                    "average_rate": avg_rate,
                    "max_flow": max_flow,
                    "min_flow": min_flow,
                    "flow_count": len(type_flows),
                }

        return flow_analysis

    def _maintain_rolling_window(self):
        """Maintain rolling window for data storage."""
        current_time = time.time()

        # Remove old energy balances
        self.energy_balances = [
            b
            for b in self.energy_balances
            if current_time - b.timestamp <= self.analysis_window
        ]

        # Remove old power metrics
        self.power_metrics = [
            m
            for m in self.power_metrics
            if current_time - m.timestamp <= self.analysis_window
        ]

        # Remove old energy flows
        self.energy_flows = [
            f
            for f in self.energy_flows
            if current_time - f.timestamp <= self.analysis_window
        ]

    def validate_energy_conservation(self, tolerance: float = 0.01) -> Dict[str, Any]:
        """
        Validate energy conservation across the system.

        Args:
            tolerance: Acceptable energy balance error (fraction)

        Returns:
            Dictionary with validation results
        """
        if not self.energy_balances:
            return {"valid": False, "error": "No energy balance data available"}

        summary = self.get_energy_summary()
        energy_error = abs(summary["energy_balance"])
        relative_error = (
            energy_error / summary["total_input"] if summary["total_input"] > 0 else 0.0
        )

        valid = relative_error <= tolerance

        return {
            "valid": valid,
            "energy_error": energy_error,
            "relative_error": relative_error,
            "tolerance": tolerance,
            "total_input": summary["total_input"],
            "total_output": summary["total_output"],
            "total_losses": summary["total_losses"],
        }


# Factory function for creating standard energy analyzer
def create_standard_energy_analyzer(analysis_window: float = 60.0) -> EnergyAnalyzer:
    """
    Create a standard energy analyzer with optimal settings for KPP analysis.

    Args:
        analysis_window: Time window for rolling averages (seconds)

    Returns:
        Configured EnergyAnalyzer instance
    """
    analyzer = EnergyAnalyzer(
        analysis_window=analysis_window, sampling_rate=10.0  # 10 Hz sampling
    )

    logger.info("Created standard energy analyzer for KPP pneumatic system")
    return analyzer
