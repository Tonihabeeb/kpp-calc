"""
Gearbox system for the KPP drivetrain.
Implements multi-stage speed conversion with realistic gear ratios.
"""

import math
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class GearStage:
    """
    Individual gear stage within a gearbox.
    """
    
    def __init__(self, ratio: float, efficiency: float = 0.95, max_torque: float = 5000.0):
        """
        Initialize a gear stage.
        
        Args:
            ratio (float): Gear ratio (output_speed / input_speed)
            efficiency (float): Gear stage efficiency (0-1)
            max_torque (float): Maximum torque capacity (N·m)
        """
        self.ratio = ratio
        self.efficiency = efficiency
        self.max_torque = max_torque
        
        # Dynamic properties
        self.input_speed = 0.0  # rad/s
        self.output_speed = 0.0  # rad/s
        self.input_torque = 0.0  # N·m
        self.output_torque = 0.0  # N·m
        
        # Losses
        self.power_loss = 0.0  # W
        self.temperature = 20.0  # °C
        
    def update(self, input_speed: float, input_torque: float):
        """
        Update gear stage based on input conditions.
        
        Args:
            input_speed (float): Input angular velocity (rad/s)
            input_torque (float): Input torque (N·m)
        """
        self.input_speed = input_speed
        self.input_torque = min(input_torque, self.max_torque)
        
        # Calculate output speed and torque
        self.output_speed = self.input_speed * self.ratio
        
        # Torque conversion with efficiency
        self.output_torque = (self.input_torque / self.ratio) * self.efficiency
        
        # Calculate power loss
        input_power = self.input_torque * self.input_speed
        output_power = self.output_torque * self.output_speed
        self.power_loss = input_power - output_power
        
        logger.debug(f"GearStage - Ratio: {self.ratio:.2f}, "
                    f"Input: {self.input_speed:.2f} rad/s, {self.input_torque:.2f} N·m, "
                    f"Output: {self.output_speed:.2f} rad/s, {self.output_torque:.2f} N·m")


class Gearbox:
    """
    Multi-stage gearbox for speed and torque conversion.
    """
    
    def __init__(self):
        """Initialize the gearbox."""
        self.stages: List[GearStage] = []
        self.input_shaft_speed = 0.0  # rad/s
        self.output_shaft_speed = 0.0  # rad/s
        self.input_torque = 0.0  # N·m
        self.output_torque = 0.0  # N·m
        
        # Overall properties
        self.overall_ratio = 1.0
        self.overall_efficiency = 1.0
        self.total_power_loss = 0.0  # W
        
        # Mechanical properties
        self.housing_temperature = 20.0  # °C
        self.oil_temperature = 20.0  # °C
        
    def add_stage(self, ratio: float, efficiency: float = 0.95, max_torque: float = 5000.0):
        """
        Add a gear stage to the gearbox.
        
        Args:
            ratio (float): Gear ratio for this stage
            efficiency (float): Efficiency of this stage
            max_torque (float): Maximum torque capacity
        """
        stage = GearStage(ratio, efficiency, max_torque)
        self.stages.append(stage)
        self._update_overall_properties()
        
    def _update_overall_properties(self):
        """Update overall gearbox properties based on individual stages."""
        self.overall_ratio = 1.0
        self.overall_efficiency = 1.0
        
        for stage in self.stages:
            self.overall_ratio *= stage.ratio
            self.overall_efficiency *= stage.efficiency
    
    def update(self, input_speed: float, input_torque: float):
        """
        Update the entire gearbox.
        
        Args:
            input_speed (float): Input shaft angular velocity (rad/s)
            input_torque (float): Input shaft torque (N·m)
        """
        self.input_shaft_speed = input_speed
        self.input_torque = input_torque
        
        current_speed = input_speed
        current_torque = input_torque
        self.total_power_loss = 0.0
        
        # Process through each stage
        for stage in self.stages:
            stage.update(current_speed, current_torque)
            current_speed = stage.output_speed
            current_torque = stage.output_torque
            self.total_power_loss += stage.power_loss
        
        # Final output values
        self.output_shaft_speed = current_speed
        self.output_torque = current_torque
        
        logger.debug(f"Gearbox - Input: {self.input_shaft_speed:.2f} rad/s, {self.input_torque:.2f} N·m, "
                    f"Output: {self.output_shaft_speed:.2f} rad/s, {self.output_torque:.2f} N·m, "
                    f"Overall Ratio: {self.overall_ratio:.2f}, Efficiency: {self.overall_efficiency:.3f}")
    
    def get_input_rpm(self) -> float:
        """Get input shaft speed in RPM."""
        return self.input_shaft_speed * 60 / (2 * math.pi)
    
    def get_output_rpm(self) -> float:
        """Get output shaft speed in RPM."""
        return self.output_shaft_speed * 60 / (2 * math.pi)
    
    def get_input_power(self) -> float:
        """Get input power (W)."""
        return self.input_torque * self.input_shaft_speed
    
    def get_output_power(self) -> float:
        """Get output power (W)."""
        return self.output_torque * self.output_shaft_speed
    
    def reset(self):
        """Reset the gearbox to initial conditions."""
        self.input_shaft_speed = 0.0
        self.output_shaft_speed = 0.0
        self.input_torque = 0.0
        self.output_torque = 0.0
        self.total_power_loss = 0.0
        
        for stage in self.stages:
            stage.input_speed = 0.0
            stage.output_speed = 0.0
            stage.input_torque = 0.0
            stage.output_torque = 0.0
            stage.power_loss = 0.0


def create_kpp_gearbox() -> Gearbox:
    """
    Create a typical KPP gearbox configuration.
    Based on the example in the technical document:
    - Overall ratio of ~39:1
    - Multi-stage design for better efficiency
    
    Returns:
        Gearbox: Configured gearbox for KPP application
    """
    gearbox = Gearbox()
    
    # Stage 1: Planetary gear stage (3.7:1 ratio)
    gearbox.add_stage(ratio=3.7, efficiency=0.97, max_torque=50000.0)
    
    # Stage 2: Helical gear stage (2.6:1 ratio)
    gearbox.add_stage(ratio=2.6, efficiency=0.96, max_torque=20000.0)
    
    # Stage 3: Final drive stage (4.1:1 ratio) to achieve ~39:1 overall
    gearbox.add_stage(ratio=4.1, efficiency=0.95, max_torque=8000.0)
    
    logger.info(f"Created KPP gearbox with overall ratio: {gearbox.overall_ratio:.1f}:1, "
               f"efficiency: {gearbox.overall_efficiency:.3f}")
    
    return gearbox
