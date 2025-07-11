"""
SimPy event system for pneumatic operations.
"""

import simpy
import numpy as np
from typing import Dict, Any, Optional

class PneumaticEventSystem:
    """SimPy-based event system for pneumatic operations"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize pneumatic event system"""
        self.config = config
        
        # Create SimPy environment
        self.env = simpy.Environment()
        
        # Event timing parameters
        self.injection_duration = config.get('injection_duration', 0.5)  # seconds
        self.valve_response_time = config.get('valve_response_time', 0.1)  # seconds
        self.compressor_cycle_time = config.get('compressor_cycle_time', 2.0)  # seconds
        
        # Event tracking
        self.active_injections = {}
        self.compressor_state = 'idle'
        self.injection_queue = []
        
        print("PneumaticEventSystem initialized with SimPy")
        
    def start_injection(self, floater_id: int, target_pressure: float) -> None:
        """Start air injection for a floater"""
        if floater_id in self.active_injections:
            print(f"Injection already active for floater {floater_id}")
            return
            
        # Create injection process
        process = self.env.process(self._injection_process(floater_id, target_pressure))
        self.active_injections[floater_id] = {
            'process': process,
            'target_pressure': target_pressure,
            'start_time': self.env.now,
            'status': 'starting'
        }
        
        print(f"Started injection for floater {floater_id}")
        
    def stop_injection(self, floater_id: int) -> None:
        """Stop air injection for a floater"""
        if floater_id in self.active_injections:
            process = self.active_injections[floater_id]['process']
            process.interrupt()
            del self.active_injections[floater_id]
            print(f"Stopped injection for floater {floater_id}")
            
    def _injection_process(self, floater_id: int, target_pressure: float):
        """SimPy process for air injection"""
        try:
            # Valve opening delay
            yield self.env.timeout(self.valve_response_time)
            
            # Update status
            if floater_id in self.active_injections:
                self.active_injections[floater_id]['status'] = 'injecting'
            
            # Injection duration
            yield self.env.timeout(self.injection_duration)
            
            # Injection complete
            if floater_id in self.active_injections:
                self.active_injections[floater_id]['status'] = 'complete'
                print(f"Injection complete for floater {floater_id}")
                
        except simpy.Interrupt:
            print(f"Injection interrupted for floater {floater_id}")
            
    def start_compressor_cycle(self) -> None:
        """Start compressor cycling process"""
        process = self.env.process(self._compressor_cycle_process())
        
    def _compressor_cycle_process(self):
        """SimPy process for compressor cycling"""
        while True:
            try:
                # Compressor on
                self.compressor_state = 'running'
                print(f"Compressor started at time {self.env.now}")
                yield self.env.timeout(self.compressor_cycle_time / 2)
                
                # Compressor off
                self.compressor_state = 'idle'
                print(f"Compressor stopped at time {self.env.now}")
                yield self.env.timeout(self.compressor_cycle_time / 2)
                
            except simpy.Interrupt:
                print("Compressor cycle interrupted")
                break
                
    def step_simulation(self, dt: float) -> None:
        """Step the SimPy environment forward"""
        self.env.run(until=self.env.now + dt)
        
    def get_active_injections(self) -> Dict[int, Dict[str, Any]]:
        """Get status of active injections"""
        return self.active_injections.copy()
        
    def get_compressor_state(self) -> str:
        """Get current compressor state"""
        return self.compressor_state
        
    def get_system_state(self) -> Dict[str, Any]:
        """Get overall system state"""
        return {
            'time': self.env.now,
            'active_injections': len(self.active_injections),
            'compressor_state': self.compressor_state,
            'injection_queue_length': len(self.injection_queue)
        }
