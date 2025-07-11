#!/usr/bin/env python3
"""
Phase 1 Implementation Script: Foundation Setup (Fixed)
KPP Simulator Physics Layer Upgrade

This script implements Phase 1 of the physics upgrade plan:
- Dependency installation and configuration
- Project structure preparation
- Configuration system enhancement
- Testing framework setup
"""

import os
import sys
import subprocess
import shutil
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase1_implementation_fixed.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Phase1Implementation:
    """Phase 1 implementation manager"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.requirements_file = self.project_root / "requirements.txt"
        self.backup_dir = self.project_root / "backup" / "phase1_backup"
        
    def run_phase1(self) -> bool:
        """Execute Phase 1 implementation"""
        logger.info("Starting Phase 1: Foundation Setup (Fixed)")
        
        try:
            # Step 1: Create backup
            self.create_backup()
            
            # Step 2: Install dependencies
            if not self.install_dependencies():
                return False
                
            # Step 3: Prepare project structure
            if not self.prepare_project_structure():
                return False
                
            # Step 4: Enhance configuration system
            if not self.enhance_configuration_system():
                return False
                
            # Step 5: Setup testing framework
            if not self.setup_testing_framework():
                return False
                
            # Step 6: Validate installation
            if not self.validate_installation():
                return False
                
            logger.info("Phase 1 completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Phase 1 failed: {e}")
            return False
    
    def create_backup(self) -> None:
        """Create backup of current state"""
        logger.info("Creating backup of current state...")
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup current requirements
        if self.requirements_file.exists():
            shutil.copy2(self.requirements_file, self.backup_dir / "requirements_old.txt")
        
        # Backup current config structure
        config_dir = self.project_root / "config"
        if config_dir.exists():
            shutil.copytree(config_dir, self.backup_dir / "config", dirs_exist_ok=True)
        
        logger.info("Backup created successfully")
    
    def install_dependencies(self) -> bool:
        """Install all required physics dependencies"""
        logger.info("Installing physics dependencies...")
        
        # Install dependencies one by one to handle errors gracefully
        dependencies = [
            ("CoolProp", "6.4.0"),
            ("simpy", "3.0.0"),
            ("pypsa", "0.21.0"),
            ("fluiddyn", "0.8.0"),  # Fixed version
            ("pytest-benchmark", "4.0.0"),
            ("memory-profiler", "0.60.0")
        ]
        
        # Optional dependencies (JAX can be problematic on Windows)
        optional_dependencies = [
            ("jax", "0.4.0"),
            ("jaxlib", "0.4.0")
        ]
        
        # Install required dependencies
        for package, version in dependencies:
            try:
                logger.info(f"Installing {package}>={version}...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", f"{package}>={version}"
                ], capture_output=True, text=True, check=True)
                logger.info(f"✓ {package} installed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"✗ Failed to install {package}: {e}")
                logger.error(f"stderr: {e.stderr}")
                return False
        
        # Try to install optional dependencies
        for package, version in optional_dependencies:
            try:
                logger.info(f"Installing optional {package}>={version}...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", f"{package}>={version}"
                ], capture_output=True, text=True, check=True)
                logger.info(f"✓ {package} installed successfully")
            except subprocess.CalledProcessError as e:
                logger.warning(f"⚠ Optional {package} installation failed: {e}")
                logger.warning("This is not critical - continuing without JAX")
        
        # Update requirements.txt with successful installations
        self.update_requirements_file()
        
        logger.info("Dependencies installed successfully")
        return True
    
    def update_requirements_file(self) -> None:
        """Update requirements.txt with physics dependencies"""
        logger.info("Updating requirements.txt...")
        
        # Read existing requirements
        existing_lines = []
        if self.requirements_file.exists():
            with open(self.requirements_file, 'r') as f:
                existing_lines = f.readlines()
        
        # Find where to insert physics dependencies
        physics_section_start = None
        for i, line in enumerate(existing_lines):
            if "# Physics Layer Dependencies" in line:
                physics_section_start = i
                break
        
        # If physics section doesn't exist, add it at the end
        if physics_section_start is None:
            physics_section_start = len(existing_lines)
            existing_lines.append("\n# Physics Layer Dependencies\n")
        
        # Add physics dependencies
        physics_deps = [
            "# Thermodynamic properties\n",
            "CoolProp>=6.4.0\n",
            "# Discrete event simulation\n",
            "simpy>=3.0.0\n",
            "# Power system analysis\n",
            "pypsa>=0.21.0\n",
            "# Fluid dynamics framework\n",
            "fluiddyn>=0.8.0\n",
            "# Performance testing\n",
            "pytest-benchmark>=4.0.0\n",
            "memory-profiler>=0.60.0\n",
            "# High-performance computing (optional)\n",
            "# jax>=0.4.0\n",
            "# jaxlib>=0.4.0\n"
        ]
        
        # Insert physics dependencies
        for i, dep in enumerate(physics_deps):
            existing_lines.insert(physics_section_start + 1 + i, dep)
        
        # Write updated requirements
        with open(self.requirements_file, 'w') as f:
            f.writelines(existing_lines)
        
        logger.info("requirements.txt updated successfully")
    
    def prepare_project_structure(self) -> bool:
        """Create new directory structure for physics components"""
        logger.info("Preparing project structure...")
        
        # Define new directories to create
        new_directories = [
            "simulation/physics/chrono",
            "simulation/physics/thermodynamics", 
            "simulation/physics/electrical",
            "simulation/physics/fluid",
            "simulation/control/events",
            "simulation/control/strategies",
            "tests/physics",
            "validation/physics",
            "docs/physics"
        ]
        
        # Create directories
        for dir_path in new_directories:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py files
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""Physics layer components."""\n')
        
        logger.info("Project structure prepared successfully")
        return True
    
    def enhance_configuration_system(self) -> bool:
        """Enhance configuration system with physics-specific settings"""
        logger.info("Enhancing configuration system...")
        
        # Create PyChrono configuration
        chrono_config = '''"""
PyChrono configuration for KPP simulator physics.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ChronoConfig:
    """Configuration for PyChrono physics engine"""
    
    # Solver settings
    solver_type: str = "SOR"  # Successive Over-Relaxation
    max_iterations: int = 100
    tolerance: float = 1e-6
    
    # Time stepping
    time_step: float = 0.02  # seconds
    max_time_step: float = 0.05
    min_time_step: float = 0.001
    
    # Physics world settings
    gravity: tuple = (0.0, -9.81, 0.0)  # m/s²
    enable_collision: bool = False
    collision_margin: float = 0.001  # meters
    
    # Performance settings
    enable_parallel: bool = True
    num_threads: int = 4
    enable_profiling: bool = False
    
    # Visualization settings (for debugging)
    enable_visualization: bool = False
    visualization_fps: int = 30
'''
        
        # Create thermodynamics configuration
        thermo_config = '''"""
Thermodynamics configuration for KPP simulator.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ThermodynamicsConfig:
    """Configuration for thermodynamic calculations"""
    
    # Fluid properties
    water_reference_temp: float = 293.15  # K (20°C)
    water_reference_pressure: float = 101325.0  # Pa (1 atm)
    air_reference_temp: float = 293.15  # K (20°C)
    air_reference_pressure: float = 101325.0  # Pa (1 atm)
    
    # Property caching
    enable_property_cache: bool = True
    cache_size: int = 1000
    cache_ttl: float = 3600.0  # seconds
    
    # H2 enhancement settings
    h2_thermal_expansion_coeff: float = 0.0034  # /K for air
    h2_heat_transfer_coeff: float = 1000.0  # W/m²·K
    
    # Error handling
    fallback_to_constants: bool = True
    max_property_error: float = 0.05  # 5% error tolerance
'''
        
        # Create electrical configuration
        electrical_config = '''"""
Electrical system configuration for KPP simulator.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ElectricalConfig:
    """Configuration for electrical power system"""
    
    # Generator settings
    generator_efficiency: float = 0.95
    generator_max_power: float = 100000.0  # W (100 kW)
    generator_min_power: float = 1000.0  # W (1 kW)
    
    # Grid settings
    grid_voltage: float = 480.0  # V
    grid_frequency: float = 60.0  # Hz
    grid_connection_type: str = "infinite_bus"
    
    # Power flow settings
    enable_power_flow: bool = True
    power_flow_tolerance: float = 1e-6
    max_power_flow_iterations: int = 50
    
    # Load modeling
    load_type: str = "constant_power"
    load_power_factor: float = 0.95
    
    # H3 enhancement settings
    h3_clutch_response_time: float = 0.1  # seconds
    h3_pulse_duration: float = 2.0  # seconds
    h3_coast_duration: float = 2.0  # seconds
'''
        
        # Create fluid dynamics configuration
        fluid_config = '''"""
Fluid dynamics configuration for KPP simulator.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class FluidConfig:
    """Configuration for fluid dynamics calculations"""
    
    # Water properties
    water_density: float = 1000.0  # kg/m³
    water_viscosity: float = 1.0e-3  # Pa·s
    water_temperature: float = 293.15  # K
    
    # Drag modeling
    drag_coefficient: float = 0.8
    enable_reynolds_dependent_drag: bool = True
    reynolds_threshold: float = 2300.0
    
    # H1 enhancement settings
    h1_nanobubble_fraction: float = 0.2
    h1_density_reduction: float = 0.1
    h1_drag_reduction: float = 0.15
    
    # Turbulence modeling
    enable_turbulence: bool = False
    turbulence_intensity: float = 0.05
    
    # Performance settings
    enable_drag_cache: bool = True
    drag_cache_size: int = 500
'''
        
        # Write configuration files
        config_files = {
            "config/components/chrono_config.py": chrono_config,
            "config/components/thermodynamics_config.py": thermo_config,
            "config/components/electrical_config.py": electrical_config,
            "config/components/fluid_config.py": fluid_config
        }
        
        for file_path, content in config_files.items():
            full_path = self.project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        logger.info("Configuration system enhanced successfully")
        return True
    
    def setup_testing_framework(self) -> bool:
        """Setup physics-specific testing framework"""
        logger.info("Setting up testing framework...")
        
        # Create physics test configuration
        test_config = '''"""
Physics testing configuration and utilities.
"""

import pytest
import numpy as np
from typing import Dict, Any

class PhysicsTestBase:
    """Base class for physics tests"""
    
    def setup_method(self):
        """Setup test method"""
        self.tolerance = 1e-6
        self.performance_threshold = 0.1  # seconds
        
    def assert_energy_conservation(self, initial_energy: float, final_energy: float, 
                                 tolerance: float = 0.01):
        """Assert energy conservation within tolerance"""
        if initial_energy == 0:
            return
        energy_change = abs(final_energy - initial_energy) / abs(initial_energy)
        assert energy_change <= tolerance, f"Energy not conserved: {energy_change:.6f} > {tolerance}"
    
    def assert_force_balance(self, forces: Dict[str, float], tolerance: float = 1e-6):
        """Assert force balance (sum of forces ≈ 0)"""
        net_force = sum(forces.values())
        assert abs(net_force) <= tolerance, f"Force not balanced: {net_force:.6f} > {tolerance}"
    
    def assert_physical_bounds(self, value: float, min_val: float, max_val: float):
        """Assert value is within physical bounds"""
        assert min_val <= value <= max_val, f"Value {value} outside bounds [{min_val}, {max_val}]"

@pytest.fixture
def physics_test_base():
    """Fixture for physics test base class"""
    return PhysicsTestBase()
'''
        
        # Create performance benchmarking utilities
        benchmark_utils = '''"""
Performance benchmarking utilities for physics components.
"""

import time
import psutil
import numpy as np
from typing import Callable, Dict, Any
from functools import wraps

def benchmark_function(func: Callable) -> Callable:
    """Decorator to benchmark function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        execution_time = end_time - start_time
        memory_used = end_memory - start_memory
        
        # Store benchmark results
        if not hasattr(wrapper, 'benchmark_results'):
            wrapper.benchmark_results = []
        
        wrapper.benchmark_results.append({
            'execution_time': execution_time,
            'memory_used': memory_used,
            'timestamp': time.time()
        })
        
        return result
    
    return wrapper

def get_benchmark_stats(func: Callable) -> Dict[str, Any]:
    """Get benchmark statistics for a function"""
    if not hasattr(func, 'benchmark_results'):
        return {}
    
    times = [r['execution_time'] for r in func.benchmark_results]
    memories = [r['memory_used'] for r in func.benchmark_results]
    
    return {
        'count': len(times),
        'mean_time': np.mean(times),
        'std_time': np.std(times),
        'min_time': np.min(times),
        'max_time': np.max(times),
        'mean_memory': np.mean(memories),
        'max_memory': np.max(memories)
    }

class PerformanceValidator:
    """Validator for performance requirements"""
    
    def __init__(self, max_execution_time: float = 0.1, max_memory_mb: float = 100.0):
        self.max_execution_time = max_execution_time
        self.max_memory_mb = max_memory_mb * 1024 * 1024  # Convert to bytes
    
    def validate_performance(self, func: Callable) -> bool:
        """Validate function performance"""
        stats = get_benchmark_stats(func)
        
        if not stats:
            return False
        
        time_ok = stats['mean_time'] <= self.max_execution_time
        memory_ok = stats['max_memory'] <= self.max_memory_mb
        
        return time_ok and memory_ok
'''
        
        # Create validation utilities
        validation_utils = '''"""
Validation utilities for physics calculations.
"""

import numpy as np
from typing import Dict, Any, List, Tuple

class PhysicsValidator:
    """Validator for physics calculations"""
    
    def __init__(self):
        self.reference_data = self._load_reference_data()
    
    def _load_reference_data(self) -> Dict[str, Any]:
        """Load reference data for validation"""
        return {
            'water_density_20c': 998.2,  # kg/m³ at 20°C
            'air_density_20c': 1.204,    # kg/m³ at 20°C
            'gravity': 9.81,             # m/s²
            'atmospheric_pressure': 101325.0,  # Pa
        }
    
    def validate_fluid_properties(self, temperature: float, pressure: float, 
                                density: float, fluid: str = 'water') -> bool:
        """Validate fluid properties against reference data"""
        if fluid == 'water':
            # Simple validation - density should be close to reference
            expected_density = self.reference_data['water_density_20c']
            tolerance = 0.05  # 5%
            return abs(density - expected_density) / expected_density <= tolerance
        return True
    
    def validate_force_calculation(self, force: float, expected_range: Tuple[float, float]) -> bool:
        """Validate force calculation is within expected range"""
        min_force, max_force = expected_range
        return min_force <= force <= max_force
    
    def validate_energy_conservation(self, initial_energy: float, final_energy: float,
                                   tolerance: float = 0.01) -> bool:
        """Validate energy conservation"""
        if initial_energy == 0:
            return True
        energy_change = abs(final_energy - initial_energy) / abs(initial_energy)
        return energy_change <= tolerance
    
    def validate_physical_constraints(self, values: Dict[str, float]) -> List[str]:
        """Validate physical constraints and return list of violations"""
        violations = []
        
        # Check for negative masses
        if 'mass' in values and values['mass'] < 0:
            violations.append("Mass cannot be negative")
        
        # Check for negative volumes
        if 'volume' in values and values['volume'] < 0:
            violations.append("Volume cannot be negative")
        
        # Check for negative forces
        if 'force' in values and values['force'] < 0:
            violations.append("Force cannot be negative")
        
        return violations
'''
        
        # Write testing framework files
        test_files = {
            "tests/physics/test_config.py": test_config,
            "tests/physics/benchmark_utils.py": benchmark_utils,
            "tests/physics/validation_utils.py": validation_utils
        }
        
        for file_path, content in test_files.items():
            full_path = self.project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        logger.info("Testing framework setup successfully")
        return True
    
    def validate_installation(self) -> bool:
        """Validate that all dependencies are properly installed"""
        logger.info("Validating installation...")
        
        # Test imports
        test_imports = [
            "CoolProp",
            "simpy", 
            "pypsa",
            "fluiddyn"
        ]
        
        failed_imports = []
        
        for module in test_imports:
            try:
                __import__(module)
                logger.info(f"✓ {module} imported successfully")
            except ImportError as e:
                logger.warning(f"✗ {module} import failed: {e}")
                failed_imports.append(module)
        
        # Test optional imports
        optional_imports = ["jax", "jaxlib"]
        for module in optional_imports:
            try:
                __import__(module)
                logger.info(f"✓ {module} imported successfully (optional)")
            except ImportError:
                logger.info(f"⚠ {module} not available (optional)")
        
        if failed_imports:
            logger.error(f"Critical dependencies failed to import: {failed_imports}")
            return False
        
        # Test basic functionality
        try:
            import CoolProp.CoolProp as CP
            water_density = CP.PropsSI('D', 'T', 293.15, 'P', 101325, 'Water')
            logger.info(f"✓ CoolProp water density test: {water_density:.2f} kg/m³")
        except Exception as e:
            logger.error(f"✗ CoolProp functionality test failed: {e}")
            return False
        
        try:
            import simpy
            env = simpy.Environment()
            logger.info("✓ SimPy environment creation test passed")
        except Exception as e:
            logger.error(f"✗ SimPy functionality test failed: {e}")
            return False
        
        logger.info("Installation validation completed successfully")
        return True

def main():
    """Main execution function"""
    logger.info("Starting KPP Simulator Physics Layer Upgrade - Phase 1 (Fixed)")
    
    implementation = Phase1Implementation()
    success = implementation.run_phase1()
    
    if success:
        logger.info("Phase 1 completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Review the new project structure")
        logger.info("2. Test the configuration system")
        logger.info("3. Run the physics test suite")
        logger.info("4. Proceed to Phase 2: PyChrono Integration")
    else:
        logger.error("Phase 1 failed. Check the log file for details.")
        sys.exit(1)

if __name__ == "__main__":
    main() 