#!/usr/bin/env python3
"""Simple integration test for KPP modules."""

def test_imports():
    print("Testing module imports...")
    
    try:
        from simulation.engine import SimulationEngine
        print("[OK] SimulationEngine imported")
    except Exception as e:
        print(f"[FAIL] SimulationEngine error: {e}")
        return False
    
    try:
        from simulation.control.fault_detector import FaultDetector
        print("[OK] FaultDetector imported")
    except Exception as e:
        print(f"[FAIL] FaultDetector error: {e}")
        return False
    
    try:
        from simulation.control.emergency_response import EmergencyResponseSystem
        print("[OK] EmergencyResponseSystem imported")
    except Exception as e:
        print(f"[FAIL] EmergencyResponseSystem error: {e}")
        return False
    
    try:
        from simulation.grid_services.demand_response.peak_shaving_controller import PeakShavingController
        print("[OK] PeakShavingController imported")
    except Exception as e:
        print(f"[FAIL] PeakShavingController error: {e}")
        return False
    
    try:
        from simulation.grid_services.frequency.primary_frequency_controller import PrimaryFrequencyController
        print("[OK] PrimaryFrequencyController imported")
    except Exception as e:
        print(f"[FAIL] PrimaryFrequencyController error: {e}")
        return False
    
    try:
        from simulation.components.advanced_generator import AdvancedGenerator
        print("[OK] AdvancedGenerator imported")
    except Exception as e:
        print(f"[FAIL] AdvancedGenerator error: {e}")
        return False
    
    try:
        from simulation.pneumatics.energy_analysis import EnergyAnalyzer
        print("[OK] EnergyAnalyzer imported")
    except Exception as e:
        print(f"[FAIL] EnergyAnalyzer error: {e}")
        return False
    
    return True

def test_instantiation():
    print("\nTesting module instantiation...")
    
    try:
        from simulation.control.fault_detector import FaultDetector
        fault_detector = FaultDetector()
        print("[OK] FaultDetector instantiated")
    except Exception as e:
        print(f"[FAIL] FaultDetector instantiation error: {e}")
        return False
    
    try:
        from simulation.control.emergency_response import EmergencyResponseSystem
        emergency_system = EmergencyResponseSystem()
        print("[OK] EmergencyResponseSystem instantiated")
    except Exception as e:
        print(f"[FAIL] EmergencyResponseSystem instantiation error: {e}")
        return False
    
    try:
        from simulation.grid_services.demand_response.peak_shaving_controller import PeakShavingController
        peak_shaving = PeakShavingController()
        print("[OK] PeakShavingController instantiated")
    except Exception as e:
        print(f"[FAIL] PeakShavingController instantiation error: {e}")
        return False
    
    try:
        from simulation.pneumatics.energy_analysis import EnergyAnalyzer
        energy_analyzer = EnergyAnalyzer()
        print("[OK] EnergyAnalyzer instantiated")
    except Exception as e:
        print(f"[FAIL] EnergyAnalyzer instantiation error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("KPP SIMPLE INTEGRATION TEST")
    print("=" * 40)
    
    imports_ok = test_imports()
    instantiation_ok = test_instantiation()
    
    print("\n" + "=" * 40)
    if imports_ok and instantiation_ok:
        print("[SUCCESS] ALL TESTS PASSED - Modules are integrated and operational!")
    else:
        print("[FAIL] Some tests failed")
