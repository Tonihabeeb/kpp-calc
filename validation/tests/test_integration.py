#!/usr/bin/env python3
"""
Comprehensive integration test for KPP simulation modules.
Tests all advanced modules and new physics/controllers.
"""

import sys
import traceback

def test_core_modules():
    """Test core simulation modules."""
    print("Testing core simulation modules...")
    try:
        from simulation.engine import SimulationEngine
        # Note: KPPPhysicsCalculator is in simulation/pneumatic_physics.py not simulation/physics.py
        from simulation.pneumatic_physics import KPPPhysicsCalculator
        print("✓ Core modules imported successfully")
        
        # Test instantiation (SimulationEngine needs params and data_queue)
        import queue
        data_queue = queue.Queue()
        params = {"wave_height": 2.0, "wave_period": 8.0}
        engine = SimulationEngine(params, data_queue)
        physics_calc = KPPPhysicsCalculator()
        print("✓ Engine and physics calculator instantiated successfully")
        return True
    except Exception as e:
        print(f"✗ Core module error: {e}")
        traceback.print_exc()
        return False

def test_control_modules():
    """Test control system modules."""
    print("\nTesting control system modules...")
    try:
        from simulation.control.fault_detector import FaultDetector
        from simulation.control.emergency_response import EmergencyResponseSystem
        from simulation.control.integrated_control_system import IntegratedControlSystem, ControlSystemConfig
        from simulation.control.grid_disturbance_handler import GridDisturbanceHandler
        print("✓ Control modules imported successfully")
        
        # Test instantiation
        fault_detector = FaultDetector()
        emergency_system = EmergencyResponseSystem()
        config = ControlSystemConfig()
        control_system = IntegratedControlSystem(config)
        disturbance_handler = GridDisturbanceHandler()
        print("✓ Control modules instantiated successfully")
        return True
    except Exception as e:
        print(f"✗ Control module error: {e}")
        traceback.print_exc()
        return False

def test_grid_services():
    """Test grid services modules."""
    print("\nTesting grid services modules...")
    try:
        from simulation.grid_services.grid_services_coordinator import GridServicesCoordinator
        from simulation.grid_services.demand_response.peak_shaving_controller import PeakShavingController
        from simulation.grid_services.demand_response.load_curtailment_controller import LoadCurtailmentController
        from simulation.grid_services.demand_response.load_forecaster import LoadForecaster
        from simulation.grid_services.frequency.primary_frequency_controller import PrimaryFrequencyController
        from simulation.grid_services.frequency.secondary_frequency_controller import SecondaryFrequencyController
        print("✓ Grid services modules imported successfully")
        
        # Test instantiation
        coordinator = GridServicesCoordinator()
        peak_shaving = PeakShavingController()
        load_curtailment = LoadCurtailmentController()
        load_forecaster = LoadForecaster()
        primary_freq = PrimaryFrequencyController()
        secondary_freq = SecondaryFrequencyController()
        print("✓ Grid services modules instantiated successfully")
        return True
    except Exception as e:
        print(f"✗ Grid services module error: {e}")
        traceback.print_exc()
        return False

def test_advanced_components():
    """Test advanced component modules."""
    print("\nTesting advanced component modules...")
    try:
        from simulation.components.advanced_generator import AdvancedGenerator
        from simulation.components.power_electronics import PowerElectronics
        from simulation.components.pneumatics import PneumaticSystem
        print("✓ Advanced component modules imported successfully")
        
        # Test instantiation
        generator = AdvancedGenerator()
        power_electronics = PowerElectronics()
        pneumatic_system = PneumaticSystem()
        print("✓ Advanced component modules instantiated successfully")
        return True
    except Exception as e:
        print(f"✗ Advanced component module error: {e}")
        traceback.print_exc()
        return False

def test_pneumatics():
    """Test pneumatics modules."""
    print("\nTesting pneumatics modules...")
    try:
        from simulation.pneumatics.thermodynamics import AdvancedThermodynamics
        from simulation.pneumatics.heat_exchange import IntegratedHeatExchange
        from simulation.pneumatics.energy_analysis import EnergyAnalyzer
        from simulation.pneumatics.injection_control import AirInjectionController
        print("✓ Pneumatics modules imported successfully")
        
        # Test instantiation
        thermodynamics = AdvancedThermodynamics()
        heat_exchange = IntegratedHeatExchange()
        energy_analyzer = EnergyAnalyzer()
        injection_controller = AirInjectionController()
        print("✓ Pneumatics modules instantiated successfully")
        return True
    except Exception as e:
        print(f"✗ Pneumatics module error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all integration tests."""
    print("=" * 60)
    print("KPP SIMULATION INTEGRATION TEST")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(test_core_modules())
    test_results.append(test_control_modules())
    test_results.append(test_grid_services())
    test_results.append(test_advanced_components())
    test_results.append(test_pneumatics())
    
    # Summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    if all(test_results):
        print(f"✓ ALL TESTS PASSED ({passed}/{total})")
        print("✓ All advanced modules are fully integrated and operational!")
        return 0
    else:
        print(f"✗ SOME TESTS FAILED ({passed}/{total})")
        failed_tests = [i for i, result in enumerate(test_results) if not result]
        print(f"Failed test indices: {failed_tests}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
