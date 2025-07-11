# KPP Simulator Physics Layer Upgrade - Deployment Guide

## Overview
This document provides instructions for deploying the upgraded KPP simulator with enhanced physics modeling.

## System Requirements
- Python 3.8+
- Required packages (see requirements.txt):
  - PyChrono
  - CoolProp
  - SimPy
  - PyPSA
  - FluidDyn
  - NumPy
  - Matplotlib (for visualization)

## Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. For PyChrono (if conda is available):
   ```bash
   conda install -c projectchrono pychrono
   ```

## Usage
### Basic Usage
```python
from simulation.integration.integrated_simulator import IntegratedKPPSimulator

config = {
    'time_step': 0.02,
    'control': {
        'strategy': 'periodic',
        'injection_interval': 2.0,
        'floater_count': 10
    }
}

simulator = IntegratedKPPSimulator(config)
simulator.start_simulation()

# Run simulation
for i in range(100):
    state = simulator.update_simulation(0.02)
    print(f"Time: {state['simulation_time']:.2f}s, "
          f"Speed: {state['drivetrain_system']['mechanical']['angular_velocity_rpm']:.1f}RPM")

simulator.stop_simulation()
```

### Legacy Interface
```python
from simulation.integration.compatibility_layer import CompatibilityLayer

compatibility = CompatibilityLayer(config)
compatibility.start()

# Use legacy interface
state = compatibility.update(0.02)
speed = compatibility.get_parameter('speed_rpm')
power = compatibility.get_parameter('power_output')
```

## Enhancements
### H1 Enhancement (Nanobubbles)
- Reduces water density and drag
- Enable: `simulator.enable_enhancement('H1', True)`

### H2 Enhancement (Thermal Effects)
- Air heating from water improves buoyancy
- Enable: `simulator.enable_enhancement('H2', True)`

### H3 Enhancement (Pulse-and-Coast)
- Clutch control for power smoothing
- Enable: `simulator.enable_enhancement('H3', True)`

## Performance Tuning
- Target FPS: 50 (configurable)
- Adaptive timestep: Enabled by default
- Parallel processing: Available for large simulations

## Safety Features
- Speed monitoring and limits
- Torque and power monitoring
- Emergency stop functionality
- Real-time safety level assessment

## Troubleshooting
1. **PyChrono import error**: Install via conda or check platform compatibility
2. **Performance issues**: Reduce timestep or disable enhancements
3. **Memory issues**: Enable memory optimization in config

## Migration from Legacy System
1. Replace direct component calls with IntegratedKPPSimulator
2. Update configuration format
3. Use compatibility layer for gradual migration
4. Test all enhancements individually

## Support
For issues and questions, refer to the implementation documentation or contact the development team.
