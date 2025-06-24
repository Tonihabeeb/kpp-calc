"""
Test suite for Phase 6: Transient Event Handling
Tests startup sequences, emergency response, and grid disturbance handling.
"""

import unittest
import sys
import os
import time
from unittest.mock import Mock, patch

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation.control.startup_controller import StartupController, StartupPhase
from simulation.control.emergency_response import EmergencyResponseSystem, EmergencyType
from simulation.control.grid_disturbance_handler import GridDisturbanceHandler, DisturbanceType, ResponseMode
from simulation.control.transient_event_controller import TransientEventController, SystemState
from simulation.engine import SimulationEngine
import queue

class TestStartupController(unittest.TestCase):
    """Test the startup sequence controller"""
    
    def setUp(self):
        self.startup_controller = StartupController()
    
    def test_startup_controller_initialization(self):
        """Test startup controller initialization"""
        self.assertEqual(self.startup_controller.current_phase, StartupPhase.INITIALIZATION)
        self.assertFalse(self.startup_controller.is_startup_active)
        self.assertEqual(self.startup_controller.target_operational_speed, 375.0)
    
    def test_startup_initiation(self):
        """Test startup sequence initiation"""
        current_time = 0.0
        success = self.startup_controller.initiate_startup(current_time)
        
        self.assertTrue(success)
        self.assertTrue(self.startup_controller.is_startup_active)
        self.assertEqual(self.startup_controller.current_phase, StartupPhase.INITIALIZATION)
        self.assertEqual(self.startup_controller.startup_start_time, current_time)
    
    def test_startup_sequence_progression(self):
        """Test startup sequence phase progression"""
        current_time = 0.0
        self.startup_controller.initiate_startup(current_time)
        
        # Mock system state
        system_state = {
            'pneumatics': {'tank_pressure': 5.0, 'compressor_running': True},
            'component_temperatures': {'generator': 25.0},
            'floaters': [{'id': 0}, {'id': 1}],
            'chain_speed_rpm': 0.0,
            'flywheel_speed_rpm': 0.0,
            'synchronized': False,
            'grid_frequency': 60.0
        }
        
        # Test initialization phase
        commands = self.startup_controller.update_startup_sequence(system_state, current_time + 1.0)
        self.assertTrue(commands['startup_active'])
        
        # Progress through phases by updating system state
        current_time += 15.0  # Allow phase progression
        system_state['chain_speed_rpm'] = 10.0  # Simulate movement
        commands = self.startup_controller.update_startup_sequence(system_state, current_time)
        
        # Should progress through multiple phases
        self.assertIn(self.startup_controller.current_phase.value, 
                     ['system_checks', 'pressure_build', 'first_injection', 'acceleration'])
    
    def test_startup_system_checks(self):
        """Test system checks functionality"""
        system_state = {
            'pneumatics': {'tank_pressure': 5.0},
            'component_temperatures': {'generator': 25.0},
            'floaters': [{'id': 0}, {'id': 1}]
        }
        
        checks = self.startup_controller._perform_system_checks(system_state)
        
        self.assertIn('pneumatic_system', checks)
        self.assertIn('electrical_system', checks)
        self.assertIn('mechanical_system', checks)
        self.assertTrue(checks['all_passed'])
    
    def test_startup_timeout_handling(self):
        """Test startup phase timeout handling"""
        current_time = 0.0
        self.startup_controller.initiate_startup(current_time)
        
        system_state = {
            'pneumatics': {'tank_pressure': 0.0},  # Insufficient pressure
            'component_temperatures': {'generator': 25.0},
            'floaters': []
        }
        
        # Simulate timeout by advancing time significantly
        current_time += 100.0  # Well beyond phase timeout
        commands = self.startup_controller.update_startup_sequence(system_state, current_time)
        
        self.assertTrue(commands.get('startup_failed', False))
        self.assertEqual(self.startup_controller.current_phase, StartupPhase.FAILED)

class TestEmergencyResponseSystem(unittest.TestCase):
    """Test the emergency response system"""
    
    def setUp(self):
        self.emergency_system = EmergencyResponseSystem()
    
    def test_emergency_system_initialization(self):
        """Test emergency system initialization"""
        self.assertFalse(self.emergency_system.emergency_active)
        self.assertEqual(len(self.emergency_system.emergency_conditions), 0)
        self.assertEqual(len(self.emergency_system.active_emergencies), 0)
    
    def test_overspeed_detection(self):
        """Test overspeed emergency detection"""
        current_time = 0.0
        system_state = {
            'flywheel_speed_rpm': 500.0,  # Above 450 RPM limit
            'pneumatics': {'tank_pressure': 5.0},
            'component_temperatures': {'generator': 25.0},
            'grid_voltage': 480.0,
            'grid_frequency': 60.0,
            'torque': 1000.0
        }
        
        commands = self.emergency_system.monitor_emergency_conditions(system_state, current_time)
        
        self.assertTrue(commands.get('emergency_active', False))
        self.assertIn(EmergencyType.OVERSPEED, self.emergency_system.active_emergencies)
    
    def test_overpressure_detection(self):
        """Test overpressure emergency detection"""
        current_time = 0.0
        system_state = {
            'flywheel_speed_rpm': 300.0,
            'pneumatics': {'tank_pressure': 10.0},  # Above 8.0 bar limit
            'component_temperatures': {'generator': 25.0},
            'grid_voltage': 480.0,
            'grid_frequency': 60.0,
            'torque': 1000.0
        }
        
        commands = self.emergency_system.monitor_emergency_conditions(system_state, current_time)
        
        self.assertTrue(commands.get('emergency_active', False))
        self.assertIn(EmergencyType.OVERPRESSURE, self.emergency_system.active_emergencies)
    
    def test_overtemperature_detection(self):
        """Test overtemperature emergency detection"""
        current_time = 0.0
        system_state = {
            'flywheel_speed_rpm': 300.0,
            'pneumatics': {'tank_pressure': 5.0},
            'component_temperatures': {'generator': 100.0},  # Above 85°C limit
            'grid_voltage': 480.0,
            'grid_frequency': 60.0,
            'torque': 1000.0
        }
        
        commands = self.emergency_system.monitor_emergency_conditions(system_state, current_time)
        
        self.assertTrue(commands.get('emergency_active', False))
        self.assertIn(EmergencyType.OVERTEMPERATURE, self.emergency_system.active_emergencies)
    
    def test_emergency_shutdown_sequence(self):
        """Test emergency shutdown sequence"""
        current_time = 0.0
        
        # Trigger manual emergency stop
        response = self.emergency_system.trigger_manual_emergency_stop("Test emergency", current_time)
        
        self.assertTrue(response.get('emergency_active', False))
        self.assertTrue(self.emergency_system.shutdown_initiated)
        
        # Simulate shutdown sequence progression
        system_state = {
            'flywheel_speed_rpm': 300.0,
            'pneumatics': {'tank_pressure': 5.0},
            'component_temperatures': {'generator': 25.0},
            'grid_voltage': 480.0,
            'grid_frequency': 60.0,
            'torque': 1000.0
        }
        
        # Progress through shutdown phases
        for i in range(6):  # 6 shutdown phases
            current_time += 3.0  # 3 seconds per phase
            commands = self.emergency_system.monitor_emergency_conditions(system_state, current_time)
            
            if commands.get('shutdown_complete', False):
                break
        
        self.assertTrue(self.emergency_system.shutdown_complete)
    
    def test_emergency_acknowledgment(self):
        """Test emergency acknowledgment"""
        current_time = 0.0
        self.emergency_system.trigger_manual_emergency_stop("Test emergency", current_time)
        
        # Acknowledge the emergency
        acknowledged = self.emergency_system.acknowledge_emergency('manual_stop')
        self.assertTrue(acknowledged)

class TestGridDisturbanceHandler(unittest.TestCase):
    """Test the grid disturbance handler"""
    
    def setUp(self):
        self.grid_handler = GridDisturbanceHandler()
    
    def test_grid_handler_initialization(self):
        """Test grid disturbance handler initialization"""
        self.assertEqual(self.grid_handler.grid_frequency, 60.0)
        self.assertEqual(self.grid_handler.grid_voltage, 480.0)
        self.assertTrue(self.grid_handler.grid_connected)
        self.assertEqual(len(self.grid_handler.active_disturbances), 0)
    
    def test_frequency_disturbance_detection(self):
        """Test frequency disturbance detection"""
        current_time = 0.0
        system_state = {
            'grid_frequency': 61.0,  # High frequency
            'grid_voltage': 480.0,
            'grid_connected': True
        }
        
        commands = self.grid_handler.monitor_grid_conditions(system_state, current_time)
        
        self.assertTrue(commands.get('grid_disturbance_active', False))
        self.assertEqual(len(self.grid_handler.active_disturbances), 1)
        self.assertEqual(self.grid_handler.active_disturbances[0].disturbance_type, DisturbanceType.FREQUENCY_HIGH)
    
    def test_voltage_disturbance_detection(self):
        """Test voltage disturbance detection"""
        current_time = 0.0
        system_state = {
            'grid_frequency': 60.0,
            'grid_voltage': 400.0,  # Low voltage
            'grid_connected': True
        }
        
        commands = self.grid_handler.monitor_grid_conditions(system_state, current_time)
        
        self.assertTrue(commands.get('grid_disturbance_active', False))
        self.assertEqual(len(self.grid_handler.active_disturbances), 1)
        self.assertEqual(self.grid_handler.active_disturbances[0].disturbance_type, DisturbanceType.VOLTAGE_LOW)
    
    def test_frequency_support_response(self):
        """Test frequency support response"""
        current_time = 0.0
        system_state = {
            'grid_frequency': 60.2,  # Moderate frequency deviation
            'grid_voltage': 480.0,
            'grid_connected': True
        }
        
        commands = self.grid_handler.monitor_grid_conditions(system_state, current_time)
        
        if commands.get('response_mode') == 'frequency_support':
            self.assertTrue(commands.get('frequency_support_active', False))
            self.assertIn('frequency_response', commands)
    
    def test_load_shedding_response(self):
        """Test load shedding response for severe disturbances"""
        current_time = 0.0
        system_state = {
            'grid_frequency': 61.5,  # Severe frequency deviation
            'grid_voltage': 480.0,
            'grid_connected': True
        }
        
        commands = self.grid_handler.monitor_grid_conditions(system_state, current_time)
        
        if commands.get('response_mode') == 'load_shedding':
            self.assertTrue(commands.get('load_shedding_active', False))
            self.assertIn('load_shed_percentage', commands)
    
    def test_grid_disconnect_response(self):
        """Test grid disconnect for emergency conditions"""
        current_time = 0.0
        system_state = {
            'grid_frequency': 60.0,
            'grid_voltage': 480.0,
            'grid_connected': False  # Grid outage
        }
        
        commands = self.grid_handler.monitor_grid_conditions(system_state, current_time)
        
        self.assertEqual(commands.get('response_mode'), 'disconnect')
        self.assertTrue(commands.get('grid_disconnect_required', False))

class TestTransientEventController(unittest.TestCase):
    """Test the transient event controller coordination"""
    
    def setUp(self):
        self.transient_controller = TransientEventController()
    
    def test_transient_controller_initialization(self):
        """Test transient event controller initialization"""
        self.assertEqual(self.transient_controller.system_state, SystemState.OFFLINE)
        self.assertIsNotNone(self.transient_controller.startup_controller)
        self.assertIsNotNone(self.transient_controller.emergency_system)
        self.assertIsNotNone(self.transient_controller.grid_handler)
    
    def test_startup_coordination(self):
        """Test startup event coordination"""
        current_time = 0.0
        
        # Initiate startup
        success = self.transient_controller.initiate_startup(current_time, "Test startup")
        self.assertTrue(success)
        
        system_state = {
            'time': current_time,
            'pneumatics': {'tank_pressure': 5.0},
            'component_temperatures': {'generator': 25.0},
            'floaters': [{'id': 0}, {'id': 1}],
            'flywheel_speed_rpm': 0.0,
            'chain_speed_rpm': 0.0,
            'torque': 0.0,
            'grid_voltage': 480.0,
            'grid_frequency': 60.0,
            'grid_connected': False
        }
        
        commands = self.transient_controller.update_transient_events(system_state, current_time)
        
        self.assertTrue(commands.get('transient_event_active', False))
        self.assertEqual(commands.get('primary_event_type'), 'startup')
    
    def test_emergency_priority(self):
        """Test emergency event priority over startup"""
        current_time = 0.0
        
        # Start with startup active
        self.transient_controller.initiate_startup(current_time, "Test startup")
        
        # Trigger emergency condition
        system_state = {
            'time': current_time,
            'pneumatics': {'tank_pressure': 5.0},
            'component_temperatures': {'generator': 25.0},
            'floaters': [{'id': 0}, {'id': 1}],
            'flywheel_speed_rpm': 500.0,  # Overspeed emergency
            'chain_speed_rpm': 0.0,
            'torque': 0.0,
            'grid_voltage': 480.0,
            'grid_frequency': 60.0,
            'grid_connected': False
        }
        
        commands = self.transient_controller.update_transient_events(system_state, current_time)
          # Emergency should override startup
        self.assertEqual(commands.get('primary_event_type'), 'emergency')
        # For critical overspeed, system should go to shutdown immediately
        self.assertEqual(self.transient_controller.system_state, SystemState.SHUTDOWN)
    
    def test_grid_support_coordination(self):
        """Test grid support event coordination"""
        current_time = 0.0
        
        # Set system to operational state
        self.transient_controller.system_state = SystemState.OPERATIONAL
        
        system_state = {
            'time': current_time,
            'pneumatics': {'tank_pressure': 5.0},
            'component_temperatures': {'generator': 25.0},
            'floaters': [{'id': 0}, {'id': 1}],
            'flywheel_speed_rpm': 375.0,
            'chain_speed_rpm': 10.0,
            'torque': 1000.0,
            'grid_voltage': 480.0,
            'grid_frequency': 60.2,  # Frequency disturbance
            'grid_connected': True
        }
        
        commands = self.transient_controller.update_transient_events(system_state, current_time)
        
        self.assertEqual(commands.get('primary_event_type'), 'grid_support')
    
    def test_system_state_transitions(self):
        """Test system state transitions"""
        current_time = 0.0
        
        # Start offline
        self.assertEqual(self.transient_controller.system_state, SystemState.OFFLINE)
        
        # Initiate startup
        self.transient_controller.initiate_startup(current_time, "Test startup")
        
        system_state = {
            'time': current_time,
            'pneumatics': {'tank_pressure': 5.0},
            'component_temperatures': {'generator': 25.0},
            'floaters': [{'id': 0}, {'id': 1}],
            'flywheel_speed_rpm': 0.0,
            'chain_speed_rpm': 0.0,
            'torque': 0.0,
            'grid_voltage': 480.0,
            'grid_frequency': 60.0,
            'grid_connected': False
        }
        
        # Update to starting state
        commands = self.transient_controller.update_transient_events(system_state, current_time)
        self.assertEqual(self.transient_controller.system_state, SystemState.STARTING)
        
        # Simulate startup completion
        startup_complete_commands = {'startup_commands': {'startup_complete': True}}
        self.transient_controller._update_system_state(startup_complete_commands, current_time)
        self.assertEqual(self.transient_controller.system_state, SystemState.OPERATIONAL)

class TestEngineIntegration(unittest.TestCase):
    """Test Phase 6 integration with main simulation engine"""
    
    def setUp(self):
        self.params = {
            'time_step': 0.1,
            'target_power': 530000.0,
            'target_rpm': 375.0,
            'num_floaters': 4,
            'ambient_temperature': 20.0
        }
        self.data_queue = queue.Queue()
        self.engine = SimulationEngine(self.params, self.data_queue)
    
    def test_engine_transient_controller_initialization(self):
        """Test that engine properly initializes transient controller"""
        self.assertIsNotNone(self.engine.transient_controller)
        self.assertEqual(self.engine.transient_controller.system_state, SystemState.OFFLINE)
    
    def test_engine_startup_initiation(self):
        """Test engine startup initiation"""
        success = self.engine.initiate_startup("Test startup")
        self.assertTrue(success)
        
        status = self.engine.get_transient_status()
        self.assertEqual(status['system_state'], SystemState.STARTING.value)
    
    def test_engine_emergency_stop(self):
        """Test engine emergency stop"""
        response = self.engine.trigger_emergency_stop("Test emergency")
        self.assertTrue(response.get('emergency_active', False))
        
        status = self.engine.get_transient_status()
        self.assertEqual(status['system_state'], SystemState.EMERGENCY.value)
    
    def test_engine_transient_event_integration(self):
        """Test that transient events are integrated into simulation step"""
        # Run one simulation step
        self.engine.step(0.1)
        
        # Get transient status
        status = self.engine.get_transient_status()
        
        # Should have transient controller status
        self.assertIn('startup_status', status)
        self.assertIn('emergency_status', status)
        self.assertIn('grid_status', status)
    
    def test_engine_reset_with_transient_controller(self):
        """Test engine reset includes transient controller"""
        # Modify state
        self.engine.initiate_startup("Test startup")
        
        # Reset
        self.engine.reset()
        
        # Verify reset
        status = self.engine.get_transient_status()
        self.assertEqual(status['system_state'], SystemState.OFFLINE.value)

if __name__ == '__main__':
    unittest.main()
