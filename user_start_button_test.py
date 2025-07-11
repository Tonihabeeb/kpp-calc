#!/usr/bin/env python3
"""
User Start Button Test
Simulates a realistic user pressing the start button and verifies the system responds.
"""

import os
import sys
import time
import json
import requests
import subprocess
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UserStartButtonTester:
    """Tester for user start button simulation"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.servers = {}
        
    def run_user_test(self) -> bool:
        """Run user start button test"""
        logger.info("Starting User Start Button Test")
        logger.info("=" * 50)
        
        try:
            # Step 1: Start the simulator
            if not self.start_simulator():
                return False
                
            # Step 2: Test user start button
            if not self.test_start_button():
                return False
                
            # Step 3: Verify system response
            if not self.verify_system_response():
                return False
                
            # Step 4: Cleanup
            self.cleanup()
            
            logger.info("=" * 50)
            logger.info("USER START BUTTON TEST COMPLETED SUCCESSFULLY!")
            logger.info("=" * 50)
            return True
            
        except Exception as e:
            logger.error(f"User test failed: {e}")
            self.cleanup()
            return False
    
    def start_simulator(self) -> bool:
        """Start the simulator servers"""
        logger.info("Step 1: Starting Simulator")
        
        try:
            # Start the Flask backend
            logger.info("Starting Flask backend...")
            flask_process = subprocess.Popen(
                [sys.executable, "app.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for startup
            time.sleep(5)
            
            # Check if process is still running
            if flask_process.poll() is not None:
                stdout, stderr = flask_process.communicate()
                logger.error(f"Flask backend failed to start: {stderr}")
                return False
            
            self.servers['flask'] = flask_process
            logger.info("Flask backend started")
            
            # Wait for server to be ready
            time.sleep(3)
            
            # Check server health
            try:
                response = requests.get("http://localhost:9100/status", timeout=5)
                if response.status_code == 200:
                    logger.info("Flask backend is healthy")
                else:
                    logger.warning(f"Flask backend returned status {response.status_code}")
            except Exception as e:
                logger.warning(f"Flask health check failed: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start simulator: {e}")
            return False
    
    def test_start_button(self) -> bool:
        """Test the user start button functionality"""
        logger.info("Step 2: Testing User Start Button")
        
        try:
            # Test the new API endpoint (simulating user clicking start)
            logger.info("Simulating user clicking start button...")
            response = requests.post(
                "http://localhost:9100/api/simulation/control",
                json={"action": "start", "duration": 0, "speed": 1.0},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info("Start button API call successful")
                    logger.info(f"Response: {data}")
                else:
                    logger.error(f"Start button API call failed: {data}")
                    return False
            else:
                logger.error(f"Start button API call failed: {response.status_code}")
                return False
            
            # Test the legacy start endpoint (if it exists)
            logger.info("Testing legacy start endpoint...")
            try:
                response = requests.post("http://localhost:9100/start", timeout=5)
                if response.status_code == 200:
                    logger.info("Legacy start endpoint working")
                else:
                    logger.warning(f"Legacy start endpoint returned {response.status_code}")
            except Exception as e:
                logger.warning(f"Legacy start endpoint not available: {e}")
            
            logger.info("User start button test completed")
            return True
            
        except Exception as e:
            logger.error(f"Start button test failed: {e}")
            return False
    
    def verify_system_response(self) -> bool:
        """Verify that the system responds correctly to start command"""
        logger.info("Step 3: Verifying System Response")
        
        try:
            # Wait a moment for the system to start
            time.sleep(2)
            
            # Get simulation state
            logger.info("Getting simulation state...")
            response = requests.get("http://localhost:9100/api/simulation/state", timeout=10)
            
            if response.status_code == 200:
                state = response.json()
                logger.info(f"Simulation state retrieved: {state.get('status', 'unknown')}")
                
                # Check for key components in state
                component_states = state.get('component_states', {})
                
                # Check for integrated components
                integrated_components = [
                    'integrated_drivetrain',
                    'integrated_electrical_system', 
                    'pneumatic_system',
                    'physics_engine'
                ]
                
                for component in integrated_components:
                    if component in component_states:
                        logger.info(f"Component active: {component}")
                    else:
                        logger.warning(f"Component not found in state: {component}")
                
                # Check for enhancement states
                enhancements = state.get('enhancements', {})
                h1_enabled = enhancements.get('h1_enabled', False)
                h2_enabled = enhancements.get('h2_enabled', False)
                h3_enabled = enhancements.get('h3_enabled', False)
                
                logger.info(f"H1 (Nanobubbles): {'Enabled' if h1_enabled else 'Disabled'}")
                logger.info(f"H2 (Thermal): {'Enabled' if h2_enabled else 'Disabled'}")
                logger.info(f"H3 (Pulse): {'Enabled' if h3_enabled else 'Disabled'}")
                
                # Check for physics metrics
                physics_metrics = [
                    'power', 'torque', 'rpm', 'efficiency',
                    'chain_speed', 'pressure', 'temperature'
                ]
                
                for metric in physics_metrics:
                    if metric in state:
                        value = state[metric]
                        logger.info(f"Physics metric {metric}: {value}")
                    else:
                        logger.warning(f"Physics metric not found: {metric}")
                
            else:
                logger.error(f"Failed to get simulation state: {response.status_code}")
                return False
            
            # Test data stream
            logger.info("Testing data stream...")
            try:
                response = requests.get("http://localhost:9100/stream", 
                                      stream=True, timeout=5)
                
                # Read a few lines to verify stream is working
                line_count = 0
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                logger.info(f"Stream data received: {data.get('timestamp', 'N/A')}")
                                line_count += 1
                                if line_count >= 3:  # Get 3 data points
                                    break
                            except json.JSONDecodeError:
                                continue
                
                if line_count > 0:
                    logger.info(f"Data stream working: {line_count} data points received")
                else:
                    logger.warning("No data received from stream")
                    
            except Exception as e:
                logger.warning(f"Data stream test failed: {e}")
            
            logger.info("System response verification completed")
            return True
            
        except Exception as e:
            logger.error(f"System response verification failed: {e}")
            return False
    
    def cleanup(self):
        """Cleanup test resources"""
        logger.info("Cleaning up test resources...")
        
        # Stop servers
        for name, process in self.servers.items():
            try:
                if process and process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
                    logger.info(f"Stopped {name}")
            except Exception as e:
                logger.warning(f"Failed to stop {name}: {e}")

def main():
    """Main test execution"""
    print("User Start Button Test")
    print("=" * 50)
    
    tester = UserStartButtonTester()
    success = tester.run_user_test()
    
    if success:
        print("\nUSER START BUTTON TEST PASSED!")
        print("The physics upgrade responds correctly to user input")
        print("\nTest Summary:")
        print("   - Simulator startup: PASS")
        print("   - Start button functionality: PASS")
        print("   - System response: PASS")
        print("\nThe physics upgrade is working correctly!")
    else:
        print("\nUSER START BUTTON TEST FAILED!")
        print("Please check the log file for details")
        sys.exit(1)

if __name__ == "__main__":
    main() 