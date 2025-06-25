"""
Debug gas dissolution logic
"""

from simulation.pneumatics.pressure_expansion import PressureExpansionPhysics

def debug_dissolution():
    physics = PressureExpansionPhysics()
    
    high_pressure = 300000.0  # 3 bar
    low_pressure = 101325.0   # 1 bar
    dt = 1.0
    
    print("=== Gas Dissolution Debug ===")
    print(f"High pressure: {high_pressure/101325:.2f} atm")
    print(f"Low pressure: {low_pressure/101325:.2f} atm")
    print(f"Henry constant: {physics.henry_constant_air}")
    print(f"Max dissolution fraction: {physics.max_dissolution_fraction}")
    print(f"Dissolution rate: {physics.dissolution_rate}")
    print(f"Release rate: {physics.release_rate}")
    
    # Start with no dissolved air
    dissolved_fraction = 0.0
    print(f"\nInitial dissolved fraction: {dissolved_fraction}")
      # Under high pressure
    pressure_atm = high_pressure / physics.P_atm
    base_equilibrium = 0.01
    equilibrium_high = min(physics.max_dissolution_fraction, 
                          base_equilibrium * pressure_atm)
    
    print(f"\nHigh pressure calculation:")
    print(f"  Pressure: {pressure_atm:.2f} atm")
    print(f"  Equilibrium fraction: {equilibrium_high:.8f}")
    
    new_fraction_high = physics.calculate_gas_dissolution(
        high_pressure, dissolved_fraction, dt)
    print(f"  New fraction: {new_fraction_high:.8f}")
    
    # Under low pressure
    pressure_atm = low_pressure / physics.P_atm
    equilibrium_low = min(physics.max_dissolution_fraction, 
                         base_equilibrium * pressure_atm)
    
    print(f"\nLow pressure calculation:")
    print(f"  Pressure: {pressure_atm:.2f} atm")
    print(f"  Equilibrium fraction: {equilibrium_low:.8f}")
    
    new_fraction_low = physics.calculate_gas_dissolution(
        low_pressure, new_fraction_high, dt)
    print(f"  New fraction: {new_fraction_low:.8f}")
    
    print(f"\nTest assertion:")
    print(f"  new_fraction_low ({new_fraction_low:.8f}) < new_fraction_high ({new_fraction_high:.8f})? {new_fraction_low < new_fraction_high}")

if __name__ == "__main__":
    debug_dissolution()
