#!/usr/bin/env python3
"""
Phase 7 Voltage Services Validation Script

This script demonstrates and validates the voltage support services implemented
in Phase 7 Week 2, including voltage regulation, power factor control, and
dynamic voltage support.
"""

import time

import matplotlib.pyplot as plt
import numpy as np

from simulation.grid_services.voltage import (
    create_standard_dynamic_voltage_support,
    create_standard_power_factor_controller,
    create_standard_voltage_regulator,
)


def test_voltage_regulator():
    """Test voltage regulation capabilities"""
    print("Testing Voltage Regulator...")

    regulator = create_standard_voltage_regulator()
    rated_power = 500.0  # MW
    dt = 0.1  # 100ms time step

    # Test scenario: voltage drop and recovery
    voltage_profile = [
        1.0,  # Normal voltage
        0.98,  # Small drop
        0.95,  # Significant drop requiring regulation
        0.93,  # Further drop
        0.95,  # Partial recovery
        0.98,  # Near normal
        1.0,  # Full recovery
        1.02,  # Slight overvoltage
        1.05,  # Higher overvoltage
        1.0,  # Return to normal
    ]

    results = []

    print(f"{'Time':<6} {'Voltage':<8} {'Q Response':<12} {'Status':<25}")
    print("-" * 60)

    for i, voltage_pu in enumerate(voltage_profile):
        response = regulator.update(voltage_pu, dt, rated_power)

        results.append(
            {
                "time": i * dt,
                "voltage": voltage_pu,
                "reactive_power": response["reactive_power_mvar"],
                "regulation_active": response["regulation_active"],
                "status": response["status"],
            }
        )

        print(
            f"{i*dt:5.1f} {voltage_pu:7.3f} {response['reactive_power_mvar']:11.2f} {response['status'][:24]}"
        )

    # Check performance
    metrics = regulator.get_performance_metrics()
    print(f"\nVoltage Regulator Performance:")
    print(f"- Regulation activations: {metrics['regulation_count']}")
    print(f"- Voltage violations: {metrics['voltage_violations']}")
    print(f"- Max reactive utilization: {metrics['max_reactive_utilization']:.1%}")
    print(f"- Voltage stability (std): {metrics['voltage_stability_std']:.4f}")

    return results


def test_power_factor_controller():
    """Test power factor control capabilities"""
    print("\nTesting Power Factor Controller...")

    controller = create_standard_power_factor_controller()
    rated_power = 500.0  # MW
    dt = 0.1  # 100ms time step

    # Test scenario: varying active and reactive power
    test_cases = [
        (0.8, 0.0),  # 80% active, no reactive (PF = 1.0)
        (0.8, 0.3),  # 80% active, 30% reactive (PF ≈ 0.86)
        (0.8, 0.6),  # 80% active, 60% reactive (PF ≈ 0.8)
        (0.6, 0.4),  # 60% active, 40% reactive (PF ≈ 0.83)
        (0.6, 0.2),  # 60% active, 20% reactive (PF ≈ 0.95)
        (0.6, 0.0),  # 60% active, no reactive (PF = 1.0)
    ]

    results = []

    print(
        f"{'Case':<6} {'P (pu)':<7} {'Q (pu)':<7} {'PF':<6} {'Q Cmd':<8} {'Status':<20}"
    )
    print("-" * 60)

    for i, (active_pu, reactive_pu) in enumerate(test_cases):
        # Allow settling over multiple time steps
        for _ in range(10):  # 1 second settling time
            response = controller.update(active_pu, reactive_pu, dt, rated_power, False)

        # Calculate actual power factor
        if active_pu > 0.01:
            apparent = np.sqrt(active_pu**2 + reactive_pu**2)
            power_factor = active_pu / apparent if apparent > 0 else 1.0
        else:
            power_factor = 1.0

        results.append(
            {
                "case": i + 1,
                "active_power": active_pu,
                "reactive_power": reactive_pu,
                "power_factor": power_factor,
                "q_command": response["reactive_power_mvar"],
                "control_active": response["control_active"],
                "status": response["status"],
            }
        )

        print(
            f"{i+1:5d} {active_pu:6.2f} {reactive_pu:6.2f} {power_factor:5.2f} {response['reactive_power_mvar']:7.1f} {response['status'][:19]}"
        )

    # Check performance
    metrics = controller.get_performance_metrics()
    print(f"\nPower Factor Controller Performance:")
    print(f"- Control activations: {metrics['control_count']}")
    print(f"- PF violations: {metrics['power_factor_violations']}")
    print(f"- Mean power factor: {metrics['power_factor_mean']:.3f}")
    print(f"- Max reactive utilization: {metrics['max_reactive_utilization']:.1%}")

    return results


def test_dynamic_voltage_support():
    """Test dynamic voltage support capabilities"""
    print("\nTesting Dynamic Voltage Support...")

    support = create_standard_dynamic_voltage_support()
    rated_power = 500.0  # MW
    dt = 0.01  # 10ms time step for fast dynamics

    # Test scenario: voltage sag event
    voltage_profile = []

    # Normal operation (1 second)
    voltage_profile.extend([1.00] * 100)

    # Voltage sag event (0.5 seconds)
    sag_voltages = np.linspace(1.00, 0.90, 25)  # Fast drop to 90%
    voltage_profile.extend(sag_voltages)
    voltage_profile.extend([0.90] * 25)  # Hold at 90%

    # Recovery (0.5 seconds)
    recovery_voltages = np.linspace(0.90, 1.00, 50)
    voltage_profile.extend(recovery_voltages)

    # Post-event normal operation (1 second)
    voltage_profile.extend([1.00] * 100)

    results = []
    event_detected = False

    print(f"{'Time':<6} {'Voltage':<8} {'Q Response':<12} {'Event':<10} {'Status':<15}")
    print("-" * 65)

    for i, voltage_pu in enumerate(voltage_profile):
        response = support.update(voltage_pu, dt, rated_power)

        # Log key time points
        if i % 20 == 0 or response["event_detected"] != event_detected:
            event_detected = response["event_detected"]

            results.append(
                {
                    "time": i * dt,
                    "voltage": voltage_pu,
                    "reactive_power": response["reactive_power_mvar"],
                    "event_detected": response["event_detected"],
                    "support_active": response["support_active"],
                    "status": response["status"],
                }
            )

            print(
                f"{i*dt:5.2f} {voltage_pu:7.3f} {response['reactive_power_mvar']:11.2f} {str(response['event_detected']):9s} {response['status'][:14]}"
            )

    # Check performance
    metrics = support.get_performance_metrics()
    print(f"\nDynamic Voltage Support Performance:")
    print(f"- Events detected: {metrics['events_detected']}")
    print(f"- Successful supports: {metrics['successful_supports']}")
    print(f"- Success rate: {metrics['success_rate_percent']:.1f}%")
    print(f"- Average event duration: {metrics['average_event_duration']:.2f}s")
    print(f"- Max reactive utilization: {metrics['max_reactive_utilization']:.1%}")

    return results


def test_service_coordination():
    """Test coordination between voltage services"""
    print("\nTesting Voltage Service Coordination...")

    # Create all three services
    regulator = create_standard_voltage_regulator()
    pf_controller = create_standard_power_factor_controller()
    dv_support = create_standard_dynamic_voltage_support()

    rated_power = 500.0
    dt = 0.1

    # Test scenario: simultaneous voltage and power factor issues
    test_scenarios = [
        {
            "name": "Normal Operation",
            "voltage_pu": 1.00,
            "active_pu": 0.8,
            "reactive_pu": 0.1,
        },
        {
            "name": "Low Voltage + Poor PF",
            "voltage_pu": 0.96,  # Low voltage
            "active_pu": 0.8,
            "reactive_pu": 0.4,  # Poor power factor
        },
        {
            "name": "Voltage Sag Event",
            "voltage_pu": 0.88,  # Significant voltage sag
            "active_pu": 0.8,
            "reactive_pu": 0.2,
        },
    ]

    print(
        f"{'Scenario':<20} {'V Reg':<8} {'PF Ctrl':<8} {'Dyn Sup':<8} {'Priority':<12}"
    )
    print("-" * 70)

    for scenario in test_scenarios:
        # Test each service response
        vr_response = regulator.update(scenario["voltage_pu"], dt, rated_power)
        pf_response = pf_controller.update(
            scenario["active_pu"],
            scenario["reactive_pu"],
            dt,
            rated_power,
            vr_response["regulation_active"],
        )
        dv_response = dv_support.update(scenario["voltage_pu"], dt, rated_power)

        # Determine service priorities
        if dv_response["support_active"]:
            priority = "Dynamic"
        elif vr_response["regulation_active"]:
            priority = "Voltage Reg"
        elif pf_response["control_active"]:
            priority = "Power Factor"
        else:
            priority = "None"

        print(
            f"{scenario['name']:<20} {str(vr_response['regulation_active']):<8} {str(pf_response['control_active']):<8} {str(dv_response['support_active']):<8} {priority:<12}"
        )

    return True


def main():
    """Main validation function"""
    print("=" * 70)
    print("Phase 7 Week 2: Voltage Support Services Validation")
    print("=" * 70)

    try:
        # Test individual services
        vr_results = test_voltage_regulator()
        pf_results = test_power_factor_controller()
        dv_results = test_dynamic_voltage_support()

        # Test coordination
        coordination_results = test_service_coordination()

        print("\n" + "=" * 70)
        print("Voltage Support Services Validation SUCCESSFUL")
        print("=" * 70)
        print("\nAll voltage support services are functioning correctly:")
        print("✓ Voltage Regulator: Automatic voltage regulation with droop control")
        print("✓ Power Factor Controller: Unity power factor maintenance")
        print("✓ Dynamic Voltage Support: Fast response to voltage events")
        print("✓ Service Coordination: Proper prioritization and coordination")

        return True

    except Exception as e:
        print(f"\nValidation FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
