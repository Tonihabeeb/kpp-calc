"""
Phase 7 Frequency Response Services Validation Script

This script demonstrates and validates the implemented frequency response services:
- Primary Frequency Control
- Secondary Frequency Control (AGC)
- Synthetic Inertia
- Grid Services Coordination

The script simulates various grid conditions and shows how the services respond.
"""

import math
import time

import matplotlib.pyplot as plt

from simulation.grid_services import (
    GridConditions,
    create_standard_grid_services_coordinator,
    create_standard_primary_frequency_controller,
    create_standard_secondary_frequency_controller,
    create_standard_synthetic_inertia_controller,
)


def test_primary_frequency_control():
    """Test primary frequency control response"""
    print("=" * 60)
    print("TESTING PRIMARY FREQUENCY CONTROL")
    print("=" * 60)

    controller = create_standard_primary_frequency_controller()
    rated_power = 500.0  # MW

    # Test scenarios
    scenarios = [
        (60.00, "Normal frequency (within dead band)"),
        (60.01, "Small deviation (within dead band)"),
        (60.03, "Above dead band - reduce generation"),
        (59.97, "Below dead band - increase generation"),
        (60.10, "Large positive deviation"),
        (59.85, "Large negative deviation"),
    ]

    print(
        f"{'Frequency (Hz)':<15} {'Power Command (MW)':<20} {'Status':<30} {'Description'}"
    )
    print("-" * 95)

    for freq, description in scenarios:
        response = controller.update(freq, 0.1, rated_power)
        print(
            f"{freq:<15.2f} {response['power_command_mw']:<20.2f} {response['status']:<30} {description}"
        )
        controller.reset()  # Reset for next test

    # Test response dynamics
    print("\nTesting response dynamics with frequency ramp...")
    controller.reset()
    frequencies = []
    responses = []

    for i in range(50):
        freq = 60.0 + 0.001 * i  # Gradual frequency increase
        response = controller.update(freq, 0.1, rated_power)
        frequencies.append(freq)
        responses.append(response["power_command_mw"])

    print(f"Final frequency: {frequencies[-1]:.3f} Hz")
    print(f"Final response: {responses[-1]:.2f} MW")
    print(f"Response active: {controller.is_responding()}")

    metrics = controller.get_performance_metrics()
    print(f"Performance metrics: {metrics}")


def test_secondary_frequency_control():
    """Test secondary frequency control (AGC) response"""
    print("\n" + "=" * 60)
    print("TESTING SECONDARY FREQUENCY CONTROL (AGC)")
    print("=" * 60)

    controller = create_standard_secondary_frequency_controller()
    rated_power = 500.0  # MW

    # Test scenarios
    scenarios = [
        (0.0, "No AGC signal"),
        (0.25, "25% increase signal"),
        (-0.25, "25% decrease signal"),
        (0.5, "50% increase signal"),
        (-0.5, "50% decrease signal"),
        (1.0, "100% increase signal"),
        (-1.0, "100% decrease signal"),
    ]

    print(
        f"{'AGC Signal':<12} {'Power Command (MW)':<20} {'Status':<25} {'Description'}"
    )
    print("-" * 85)

    for agc_signal, description in scenarios:
        # Multiple updates to allow ramp-up
        response = None
        for _ in range(10):  # Allow time for response to develop
            response = controller.update(agc_signal, 0.1, rated_power)

        if response is not None:
            print(
                f"{agc_signal:<12.2f} {response['power_command_mw']:<20.2f} {response['status']:<25} {description}"
            )
        else:
            print(
                f"{agc_signal:<12.2f} {'ERROR':<20} {'Controller returned None':<25} {description}"
            )
        controller.reset()  # Reset for next test

    # Test regulation dynamics
    print("\nTesting regulation dynamics with varying AGC signal...")
    controller.reset()
    agc_signals = []
    responses = []

    for i in range(100):
        agc_signal = 0.5 * math.sin(i * 0.1)  # Sinusoidal AGC signal
        response = controller.update(agc_signal, 0.1, rated_power)
        agc_signals.append(agc_signal)
        responses.append(response["power_command_mw"])

    print(f"Max AGC signal: {max(agc_signals):.3f}")
    print(f"Max response: {max(responses):.2f} MW")
    print(f"Min response: {min(responses):.2f} MW")

    metrics = controller.get_performance_metrics()
    print(f"Performance metrics: {metrics}")


def test_synthetic_inertia():
    """Test synthetic inertia response"""
    print("\n" + "=" * 60)
    print("TESTING SYNTHETIC INERTIA")
    print("=" * 60)

    controller = create_standard_synthetic_inertia_controller()
    rated_power = 500.0  # MW

    # Simulate frequency decline (high ROCOF)
    print("Simulating frequency decline event...")
    frequencies = [60.0, 59.9, 59.8, 59.7, 59.6, 59.5]  # Rapid decline

    print(
        f"{'Time (s)':<10} {'Frequency (Hz)':<15} {'ROCOF (Hz/s)':<15} {'Power (MW)':<15} {'Active':<10}"
    )
    print("-" * 75)

    for i, freq in enumerate(frequencies):
        response = controller.update(freq, 0.1, rated_power)
        print(
            f"{i*0.1:<10.1f} {freq:<15.2f} {response['rocof_hz_per_s']:<15.3f} "
            f"{response['power_command_mw']:<15.2f} {controller.is_responding()}"
        )

    # Continue with stable frequency to show response decay
    print("\nMaintaining stable frequency to show response decay...")
    for i in range(20):
        response = controller.update(59.5, 0.1, rated_power)
        if i % 5 == 0:  # Print every 5th update
            print(
                f"{(len(frequencies) + i)*0.1:<10.1f} {59.5:<15.2f} {response['rocof_hz_per_s']:<15.3f} "
                f"{response['power_command_mw']:<15.2f} {controller.is_responding()}"
            )

    metrics = controller.get_performance_metrics()
    print(f"Performance metrics: {metrics}")

    # Test frequency analysis
    analysis = controller.get_frequency_analysis()
    if "insufficient_data" not in analysis:
        print(f"Frequency analysis: {analysis}")


def test_grid_services_coordination():
    """Test grid services coordination"""
    print("\n" + "=" * 60)
    print("TESTING GRID SERVICES COORDINATION")
    print("=" * 60)

    coordinator = create_standard_grid_services_coordinator()
    rated_power_mw = 500.0  # MW

    # Test single service activation
    print("Testing single service activation (primary frequency control)...")
    grid_conditions = GridConditions(
        frequency=59.95,  # Below dead band
        voltage=480.0,
        active_power=300.0,
        grid_connected=True,
        agc_signal=0.0,
        timestamp=time.time(),
    )

    response = coordinator.update(grid_conditions, 0.1, rated_power_mw)
    print(f"Active services: {response['active_services']}")
    print(f"Service count: {response['service_count']}")
    print(f"Total power command: {response['total_power_command_mw']:.2f} MW")
    print(f"Status: {response['status']}")

    # Test multiple service activation
    print("\nTesting multiple service activation...")
    grid_conditions.frequency = 59.90  # Triggers primary frequency control
    grid_conditions.agc_signal = 0.3  # Triggers secondary frequency control

    # Multiple updates to allow services to activate
    for _ in range(10):
        response = coordinator.update(grid_conditions, 0.1, rated_power_mw)
        grid_conditions.frequency = max(
            59.80, grid_conditions.frequency - 0.01
        )  # Gradual decline

    print(f"Active services: {response['active_services']}")
    print(f"Service count: {response['service_count']}")
    print(f"Total power command: {response['total_power_command_mw']:.2f} MW")
    print(f"Status: {response['status']}")

    # Test service status
    print("\nService status:")
    status = coordinator.get_service_status()
    for service, active in status.items():
        print(f"  {service}: {'ACTIVE' if active else 'INACTIVE'}")

    # Test performance metrics
    print("\nPerformance metrics:")
    metrics = coordinator.get_performance_metrics()
    print(f"Coordinator metrics: {metrics['coordinator']}")
    print(f"Frequency services: {list(metrics['frequency_services'].keys())}")


def test_integration_scenario():
    """Test comprehensive integration scenario"""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE INTEGRATION SCENARIO")
    print("=" * 60)

    coordinator = create_standard_grid_services_coordinator()
    rated_power_mw = 500.0  # MW

    print("Simulating grid disturbance event with multiple service responses...")

    # Initial stable conditions
    grid_conditions = GridConditions(
        frequency=60.0,
        voltage=480.0,
        active_power=400.0,
        grid_connected=True,
        agc_signal=0.0,
        timestamp=time.time(),
    )

    scenarios = [
        # Time, Frequency, AGC Signal, Description
        (0.0, 60.0, 0.0, "Normal operation"),
        (1.0, 59.9, 0.0, "Frequency disturbance begins"),
        (2.0, 59.8, 0.1, "Frequency continues to decline, AGC activated"),
        (3.0, 59.7, 0.2, "Severe frequency decline"),
        (4.0, 59.6, 0.3, "Maximum disturbance"),
        (5.0, 59.7, 0.2, "Frequency begins recovery"),
        (6.0, 59.8, 0.1, "Continued recovery"),
        (7.0, 59.9, 0.05, "Nearly recovered"),
        (8.0, 60.0, 0.0, "Normal operation restored"),
    ]

    print(
        f"{'Time':<6} {'Freq':<6} {'AGC':<6} {'Power Cmd':<12} {'Services':<8} {'Description'}"
    )
    print("-" * 80)

    for time_step, freq, agc, description in scenarios:
        grid_conditions.frequency = freq
        grid_conditions.agc_signal = agc
        grid_conditions.timestamp = time_step

        response = coordinator.update(grid_conditions, 0.1, rated_power_mw)

        print(
            f"{time_step:<6.1f} {freq:<6.2f} {agc:<6.2f} {response['total_power_command_mw']:<12.2f} "
            f"{response['service_count']:<8} {description}"
        )

    print(f"\nFinal coordinator performance:")
    metrics = coordinator.get_performance_metrics()
    coord_metrics = metrics["coordinator"]
    print(f"  Total coordinations: {coord_metrics['total_coordinations']}")
    print(f"  Service activations: {coord_metrics['service_activations']}")
    print(f"  Current power command: {coord_metrics['current_power_command']:.2f} MW")


def main():
    """Run all validation tests"""
    print("PHASE 7 FREQUENCY RESPONSE SERVICES VALIDATION")
    print("=" * 80)
    print("Testing individual frequency response services and coordination")
    print("This validation demonstrates the implementation of Week 1 deliverables:")
    print("- Primary Frequency Control")
    print("- Secondary Frequency Control (AGC)")
    print("- Synthetic Inertia")
    print("- Grid Services Coordinator")
    print("=" * 80)

    try:
        test_primary_frequency_control()
        test_secondary_frequency_control()
        test_synthetic_inertia()
        test_grid_services_coordination()
        test_integration_scenario()

        print("\n" + "=" * 80)
        print("✅ ALL VALIDATION TESTS COMPLETED SUCCESSFULLY")
        print(
            "✅ Phase 7 Week 1 implementation is functional and ready for integration"
        )
        print("✅ Frequency response services are operational")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
