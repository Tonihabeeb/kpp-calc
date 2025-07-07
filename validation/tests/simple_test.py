        from simulation.pneumatics.energy_analysis import EnergyAnalyzer
        from simulation.grid_services.frequency.primary_frequency_controller import (
        from simulation.grid_services.demand_response.peak_shaving_controller import (
        from simulation.engine import SimulationEngine
        from simulation.control.fault_detector import FaultDetector
        from simulation.control.emergency_response import EmergencyResponseSystem
        from simulation.components.advanced_generator import AdvancedGenerator
#!/usr/bin/env python3
"""Simple integration test for KPP modules."""


def test_imports():
    print("Testing module imports...")

    try:
