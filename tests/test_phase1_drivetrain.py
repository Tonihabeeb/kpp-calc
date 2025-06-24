"""
Test script for Phase 1 drivetrain components.
Tests the sprocket and gearbox implementation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.components.sprocket import Sprocket
from simulation.components.gearbox import create_kpp_gearbox


def test_sprocket():
    """Test basic sprocket functionality."""
    print("Testing Sprocket...")
    
    # Create a sprocket
    sprocket = Sprocket(radius=1.0, tooth_count=20, position='top')
    
    # Test with some chain tension
    chain_tension = 1000.0  # 1000 N
    dt = 0.1  # 0.1 second time step
    
    # Update sprocket
    sprocket.update(chain_tension, dt)
    
    print(f"Chain tension: {chain_tension} N")
    print(f"Sprocket torque: {sprocket.torque:.2f} N·m")
    print(f"Expected torque: {chain_tension * sprocket.radius:.2f} N·m")
    print(f"Sprocket speed: {sprocket.get_rpm():.2f} RPM")
    print(f"Chain speed: {sprocket.get_chain_speed():.2f} m/s")
    print()


def test_gearbox():
    """Test basic gearbox functionality."""
    print("Testing Gearbox...")
    
    # Create KPP gearbox
    gearbox = create_kpp_gearbox()
    
    # Test with input conditions
    input_speed = 1.0  # 1 rad/s (~9.5 RPM)
    input_torque = 5000.0  # 5000 N·m
    
    # Update gearbox
    gearbox.update(input_speed, input_torque)
    
    print(f"Input: {gearbox.get_input_rpm():.1f} RPM, {input_torque:.0f} N·m")
    print(f"Output: {gearbox.get_output_rpm():.1f} RPM, {gearbox.output_torque:.0f} N·m")
    print(f"Overall ratio: {gearbox.overall_ratio:.1f}:1")
    print(f"Overall efficiency: {gearbox.overall_efficiency:.3f}")
    print(f"Input power: {gearbox.get_input_power():.0f} W")
    print(f"Output power: {gearbox.get_output_power():.0f} W")
    print(f"Power loss: {gearbox.total_power_loss:.0f} W")
    print()


def test_integrated_drivetrain():
    """Test sprocket and gearbox working together."""
    print("Testing Integrated Drivetrain...")
    
    # Create components
    sprocket = Sprocket(radius=1.0, tooth_count=20, position='top')
    gearbox = create_kpp_gearbox()
    
    # Simulate a typical operating condition
    chain_tension = 2000.0  # 2000 N chain tension
    dt = 0.1
    
    # Update sprocket with chain tension
    sprocket.update(chain_tension, dt)
    
    # Feed sprocket output to gearbox
    gearbox.update(sprocket.angular_velocity, sprocket.torque)
    
    print(f"Chain tension: {chain_tension} N")
    print(f"Sprocket: {sprocket.torque:.0f} N·m @ {sprocket.get_rpm():.1f} RPM")
    print(f"Gearbox output: {gearbox.output_torque:.0f} N·m @ {gearbox.get_output_rpm():.1f} RPM")
    print(f"Power flow: {sprocket.get_power_output():.0f} W -> {gearbox.get_output_power():.0f} W")
    
    # Calculate speed-up ratio achieved
    if sprocket.get_rpm() > 0:
        actual_ratio = gearbox.get_output_rpm() / sprocket.get_rpm()
        print(f"Actual speed ratio: {actual_ratio:.1f}:1")
    print()


if __name__ == "__main__":
    print("Phase 1 Drivetrain Components Test")
    print("=" * 40)
    
    test_sprocket()
    test_gearbox() 
    test_integrated_drivetrain()
    
    print("Phase 1 testing complete!")
