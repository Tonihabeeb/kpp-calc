#!/usr/bin/env python3
"""
Automated Testing Script for KPP Simulation
Continuously monitors simulation output and provides diagnostics
"""

import requests
import json
import time
import sys
import subprocess
import threading
from datetime import datetime
import csv
import os

class SimulationTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.test_results = []
        self.monitoring = False
        
    def start_flask_app(self):
        """Start the Flask application in the background"""
        try:
            # Check if app is already running
            response = requests.get(f"{self.base_url}/data/summary", timeout=2)
            print("✓ Flask app is already running")
            return True
        except:
            print("Starting Flask app...")
            # Start Flask app in background
            subprocess.Popen([sys.executable, "app.py"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            time.sleep(3)
            
            # Verify it started
            try:
                response = requests.get(f"{self.base_url}/data/summary", timeout=5)
                print("✓ Flask app started successfully")
                return True
            except:
                print("✗ Failed to start Flask app")
                return False
    
    def start_simulation(self):
        """Start the simulation with proper headers"""
        try:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(f"{self.base_url}/start", 
                                   headers=headers, 
                                   data=json.dumps({}))
            if response.status_code == 200:
                print("✓ Simulation started successfully")
                return True
            else:
                print(f"✗ Failed to start simulation: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"✗ Error starting simulation: {e}")
            return False
    
    def stop_simulation(self):
        """Stop the simulation"""
        try:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(f"{self.base_url}/stop", headers=headers)
            if response.status_code == 200:
                print("✓ Simulation stopped")
                return True
            else:
                print(f"✗ Failed to stop simulation: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Error stopping simulation: {e}")
            return False
    
    def get_simulation_data(self):
        """Get current simulation data"""
        try:
            # Get summary data
            summary_response = requests.get(f"{self.base_url}/data/summary")
            summary_data = summary_response.json() if summary_response.status_code == 200 else {}
            
            # Get system overview
            system_response = requests.get(f"{self.base_url}/data/system_overview")
            system_data = system_response.json() if system_response.status_code == 200 else {}
            
            # Get electrical status
            electrical_response = requests.get(f"{self.base_url}/data/electrical_status")
            electrical_data = electrical_response.json() if electrical_response.status_code == 200 else {}
            
            return {
                'summary': summary_data,
                'system': system_data,
                'electrical': electrical_data,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error getting simulation data: {e}")
            return None
    
    def check_recent_csv_data(self):
        """Check the most recent entries in the CSV log"""
        try:
            if os.path.exists('realtime_log.csv'):
                with open('realtime_log.csv', 'r') as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        # Get last few entries
                        recent_entries = []
                        for line in lines[-3:]:
                            parts = line.strip().split(',')
                            if len(parts) >= 3:
                                recent_entries.append({
                                    'time': float(parts[0]) if parts[0] else 0.0,
                                    'power': float(parts[1]) if parts[1] else 0.0,
                                    'torque': float(parts[2]) if parts[2] else 0.0
                                })
                        return recent_entries
        except Exception as e:
            print(f"Error reading CSV: {e}")
        return []
    
    def analyze_results(self, data):
        """Analyze simulation results and provide diagnostics"""
        analysis = {
            'timestamp': data['timestamp'],
            'power_output': 0.0,
            'torque': 0.0,
            'efficiency': 0.0,
            'issues': [],
            'status': 'unknown'
        }
        
        # Check summary data
        summary = data.get('summary', {})
        if summary:
            analysis['power_output'] = summary.get('power', 0.0)
            analysis['torque'] = summary.get('torque', 0.0)
            analysis['efficiency'] = summary.get('overall_efficiency', 0.0)
            analysis['clutch_engaged'] = summary.get('clutch_engaged', False)
            analysis['chain_speed'] = summary.get('chain_speed_rpm', 0.0)
            
            # Analyze issues
            if analysis['power_output'] == 0.0:
                analysis['issues'].append("No power output")
            if analysis['torque'] == 0.0:
                analysis['issues'].append("No torque")
            if analysis['efficiency'] == 0.0:
                analysis['issues'].append("Zero efficiency")
            if not analysis['clutch_engaged']:
                analysis['issues'].append("Clutch not engaged")
        else:
            analysis['issues'].append("No summary data available")
        
        # Check electrical data
        electrical = data.get('electrical', {})
        if electrical:
            gen_data = electrical.get('advanced_generator', {})
            analysis['generator_power'] = gen_data.get('electrical_power', 0.0)
            analysis['generator_torque'] = gen_data.get('torque', 0.0)
            analysis['generator_efficiency'] = gen_data.get('efficiency', 0.0)
            
            if analysis['generator_power'] == 0.0:
                analysis['issues'].append("Generator producing no power")
        
        # Determine overall status
        if len(analysis['issues']) == 0:
            analysis['status'] = 'healthy'
        elif analysis['power_output'] > 0:
            analysis['status'] = 'partial'
        else:
            analysis['status'] = 'faulty'
        
        return analysis
    
    def print_analysis(self, analysis):
        """Print analysis results"""
        status_symbols = {
            'healthy': '✓',
            'partial': '⚠',
            'faulty': '✗',
            'unknown': '?'
        }
        
        symbol = status_symbols.get(analysis['status'], '?')
        print(f"\n{symbol} Simulation Status: {analysis['status'].upper()}")
        print(f"   Time: {analysis['timestamp']}")
        print(f"   Power Output: {analysis['power_output']:.2f} W")
        print(f"   Torque: {analysis['torque']:.2f} N⋅m")
        print(f"   Efficiency: {analysis['efficiency']:.2%}")
        
        if 'generator_power' in analysis:
            print(f"   Generator Power: {analysis['generator_power']:.2f} W")
        if 'chain_speed' in analysis:
            print(f"   Chain Speed: {analysis['chain_speed']:.1f} RPM")
        
        if analysis['issues']:
            print("   Issues detected:")
            for issue in analysis['issues']:
                print(f"     • {issue}")
    
    def run_single_test(self):
        """Run a single test cycle"""
        print(f"\n{'='*60}")
        print(f"Running simulation test at {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        # Stop any existing simulation
        self.stop_simulation()
        time.sleep(1)
        
        # Start new simulation
        if not self.start_simulation():
            return False
        
        # Wait for simulation to stabilize
        print("Waiting for simulation to stabilize...")
        time.sleep(5)
        
        # Get data and analyze
        data = self.get_simulation_data()
        if data:
            analysis = self.analyze_results(data)
            self.print_analysis(analysis)
            self.test_results.append(analysis)
            
            # Also check CSV data
            csv_data = self.check_recent_csv_data()
            if csv_data:
                print(f"\nRecent CSV entries:")
                for entry in csv_data:
                    print(f"   t={entry['time']:.1f}s, P={entry['power']:.1f}W, τ={entry['torque']:.1f}N⋅m")
            
            return analysis['status'] in ['healthy', 'partial']
        else:
            print("✗ Failed to get simulation data")
            return False
    
    def run_continuous_monitoring(self, duration=60, interval=10):
        """Run continuous monitoring for specified duration"""
        print(f"\nStarting continuous monitoring for {duration} seconds (interval: {interval}s)")
        
        if not self.start_simulation():
            return
        
        start_time = time.time()
        self.monitoring = True
        
        while self.monitoring and (time.time() - start_time) < duration:
            data = self.get_simulation_data()
            if data:
                analysis = self.analyze_results(data)
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Status: {analysis['status']} | "
                      f"Power: {analysis['power_output']:.1f}W | "
                      f"Torque: {analysis['torque']:.1f}N⋅m | "
                      f"Issues: {len(analysis['issues'])}")
                
                if analysis['issues']:
                    print(f"   Issues: {', '.join(analysis['issues'])}")
                
                self.test_results.append(analysis)
            
            time.sleep(interval)
        
        self.monitoring = False
        print(f"\nMonitoring completed. Collected {len(self.test_results)} data points.")
    
    def save_results(self, filename="test_results.json"):
        """Save test results to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            print(f"✓ Results saved to {filename}")
        except Exception as e:
            print(f"✗ Error saving results: {e}")
    
    def print_summary(self):
        """Print summary of all test results"""
        if not self.test_results:
            print("No test results available")
            return
        
        healthy_count = sum(1 for r in self.test_results if r['status'] == 'healthy')
        partial_count = sum(1 for r in self.test_results if r['status'] == 'partial')
        faulty_count = sum(1 for r in self.test_results if r['status'] == 'faulty')
        
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY ({len(self.test_results)} tests)")
        print(f"{'='*60}")
        print(f"✓ Healthy: {healthy_count}")
        print(f"⚠ Partial:  {partial_count}")
        print(f"✗ Faulty:   {faulty_count}")
        
        if self.test_results:
            latest = self.test_results[-1]
            print(f"\nLatest Results:")
            print(f"   Power: {latest['power_output']:.2f} W")
            print(f"   Torque: {latest['torque']:.2f} N⋅m")
            print(f"   Efficiency: {latest['efficiency']:.2%}")


def main():
    """Main function - can be called with different modes"""
    tester = SimulationTester()
    
    # Start Flask app
    if not tester.start_flask_app():
        return
    
    print("KPP Simulation Automated Tester")
    print("Options:")
    print("1. Single test")
    print("2. Continuous monitoring (60s)")
    print("3. Quick diagnostic")
    
    try:
        choice = input("Enter choice (1-3) or Enter for single test: ").strip()
        
        if choice == "2":
            tester.run_continuous_monitoring(duration=60, interval=5)
        elif choice == "3":
            # Quick diagnostic - just get current status
            data = tester.get_simulation_data()
            if data:
                analysis = tester.analyze_results(data)
                tester.print_analysis(analysis)
        else:
            # Default: single test
            tester.run_single_test()
        
        tester.print_summary()
        tester.save_results()
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        tester.monitoring = False
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
