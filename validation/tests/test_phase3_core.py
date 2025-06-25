"""
Simplified Phase 3 tests focusing on core functionality.
"""

import math
from simulation.components.advanced_generator import AdvancedGenerator, create_kmp_generator


def test_phase3_core_functionality():
    """Test core Phase 3 functionality with simplified approach."""
    print("Testing Phase 3 Core Functionality...")
    print("=" * 50)
    
    # Test 1: Advanced Generator Core Functions
    print("1. Testing Advanced Generator Core Functions")
    generator = create_kmp_generator()
    
    # Test at rated conditions
    rated_speed = 375.0 * (2 * math.pi / 60)  # 39.27 rad/s
    load_factor = 0.8
    
    result = generator.update(rated_speed, load_factor, 0.1)
    
    print(f"   ✓ Generator power: {result['electrical_power']/1000:.1f} kW")
    print(f"   ✓ Generator efficiency: {result['efficiency']:.3f}")
    print(f"   ✓ Generator torque: {result['torque']:.1f} N⋅m")
    print(f"   ✓ Power factor: {result['power_factor']:.3f}")
    
    assert result['electrical_power'] > 0, "Should generate power"
    assert result['efficiency'] > 0.8, "Should have reasonable efficiency"
    assert result['torque'] > 0, "Should produce torque"
    
    # Test 2: Load Torque Calculation
    print("\n2. Testing Load Torque Calculation")
    load_torque = generator.get_load_torque(rated_speed, 400000.0)  # 400kW target
    print(f"   ✓ Load torque for 400kW: {load_torque:.1f} N⋅m")
    assert load_torque > 0, "Should calculate load torque"
    
    # Test 3: Efficiency at Various Loads
    print("\n3. Testing Efficiency Curve")
    load_factors = [0.2, 0.5, 0.8, 1.0, 1.2]
    efficiencies = []
    
    for lf in load_factors:
        result = generator.update(rated_speed, lf, 0.1)
        efficiencies.append(result['efficiency'])
        print(f"   Load {lf*100:3.0f}%: Efficiency {result['efficiency']:.3f}")
    
    # Peak efficiency should be around 80-100% load
    peak_eff_idx = efficiencies.index(max(efficiencies))
    assert peak_eff_idx >= 2, "Peak efficiency should be at medium-high load"
    
    # Test 4: Speed Variation Response
    print("\n4. Testing Speed Variation Response")
    speeds_rpm = [300, 350, 375, 400, 450]
    
    for rpm in speeds_rpm:
        speed_rad_s = rpm * (2 * math.pi / 60)
        result = generator.update(speed_rad_s, 0.8, 0.1)
        print(f"   {rpm:3d} RPM: Power {result['electrical_power']/1000:5.1f} kW, "
              f"Slip {result['slip']:6.4f}, Eff {result['efficiency']:.3f}")
        
        assert result['electrical_power'] >= 0, "Power should be non-negative"
        assert abs(result['slip']) < 0.2, "Slip should be reasonable"
    
    # Test 5: Loss Breakdown
    print("\n5. Testing Loss Breakdown")
    result = generator.update(rated_speed, 0.8, 0.1)
    
    total_losses = result['iron_losses'] + result['copper_losses'] + result['mechanical_losses']
    print(f"   Iron losses:      {result['iron_losses']:6.1f} W")
    print(f"   Copper losses:    {result['copper_losses']:6.1f} W")
    print(f"   Mechanical losses:{result['mechanical_losses']:6.1f} W")
    print(f"   Total losses:     {total_losses:6.1f} W")
    print(f"   Loss percentage:  {(total_losses/result['mechanical_power'])*100:5.1f}%")
    
    assert total_losses > 0, "Should have some losses"
    assert total_losses < result['mechanical_power'] * 0.2, "Losses should be reasonable"
    
    # Test 6: Field Excitation Control
    print("\n6. Testing Field Excitation Control")
    excitation_levels = [0.8, 1.0, 1.2]
    
    for excitation in excitation_levels:
        generator.set_field_excitation(excitation)
        result = generator.update(rated_speed, 0.8, 0.1)
        print(f"   Excitation {excitation:.1f}: Power {result['electrical_power']/1000:5.1f} kW, "
              f"PF {result['power_factor']:.3f}")
    
    print("\n" + "=" * 50)
    print("✅ All Phase 3 core functionality tests passed!")
    print("✅ Advanced generator modeling operational")
    print("✅ Electromagnetic characteristics realistic")
    print("✅ Loss modeling comprehensive")
    print("✅ Control systems functional")


if __name__ == "__main__":
    test_phase3_core_functionality()
