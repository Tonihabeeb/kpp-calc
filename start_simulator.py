#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KPP Simulator - Comprehensive Startup Script
Manages all server components in the correct order with proper error handling.
"""

import subprocess
import time
import sys
import os
import signal
import threading
import requests
import logging
from typing import Dict, List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimulatorManager:
    """Manages all KPP simulator server components"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.ports = {
            'master_clock': 9201,
            'backend_api': 9100,
            'websocket_server': 9101,
            'dashboard': 9103
        }
        self.startup_order = [
            'master_clock',
            'backend_api', 
            'websocket_server',
            'dashboard'
        ]
        self.running = False
        
    def start_master_clock(self) -> bool:
        """Start the master clock server"""
        try:
            logger.info("Starting Master Clock Server (Port 9201)...")
            process = subprocess.Popen([
                sys.executable, 'realtime_sync_master_fixed.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes['master_clock'] = process
            
            # Wait for server to start
            time.sleep(2)
            
            # Check if server is responding
            if self._check_server_health('master_clock'):
                logger.info("✅ Master Clock Server started successfully")
                return True
            else:
                logger.error("❌ Master Clock Server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start Master Clock Server: {e}")
            return False
    
    def start_backend_api(self) -> bool:
        """Start the backend API server"""
        try:
            logger.info("Starting Backend API Server (Port 9100)...")
            process = subprocess.Popen([
                sys.executable, 'app.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes['backend_api'] = process
            
            # Wait for server to start
            time.sleep(3)
            
            # Check if server is responding
            if self._check_server_health('backend_api'):
                logger.info("✅ Backend API Server started successfully")
                return True
            else:
                logger.error("❌ Backend API Server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start Backend API Server: {e}")
            return False
    
    def start_websocket_server(self) -> bool:
        """Start the WebSocket server"""
        try:
            logger.info("Starting WebSocket Server (Port 9101)...")
            process = subprocess.Popen([
                sys.executable, 'main.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes['websocket_server'] = process
            
            # Wait for server to start
            time.sleep(2)
            
            # Check if server is responding
            if self._check_server_health('websocket_server'):
                logger.info("✅ WebSocket Server started successfully")
                return True
            else:
                logger.error("❌ WebSocket Server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start WebSocket Server: {e}")
            return False
    
    def start_dashboard(self) -> bool:
        """Start the dashboard server"""
        try:
            logger.info("Starting Dashboard Server (Port 9103)...")
            process = subprocess.Popen([
                sys.executable, 'dash_app.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes['dashboard'] = process
            
            # Wait for server to start
            time.sleep(5)
            
            # Check if server is responding
            if self._check_server_health('dashboard'):
                logger.info("✅ Dashboard Server started successfully")
                return True
            else:
                logger.error("❌ Dashboard Server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start Dashboard Server: {e}")
            return False
    
    def _check_server_health(self, server_name: str) -> bool:
        """Check if a server is responding"""
        try:
            port = self.ports[server_name]
            
            if server_name == 'master_clock':
                response = requests.get(f'http://localhost:{port}/health', timeout=5)
            elif server_name == 'backend_api':
                response = requests.get(f'http://localhost:{port}/status', timeout=5)
            elif server_name == 'websocket_server':
                response = requests.get(f'http://localhost:{port}/', timeout=5)
            elif server_name == 'dashboard':
                response = requests.get(f'http://localhost:{port}/', timeout=5)
            else:
                return False
            
            return response.status_code == 200
            
        except requests.exceptions.RequestException:
            return False
        except Exception as e:
            logger.debug(f"Health check error for {server_name}: {e}")
            return False
    
    def start_all_servers(self) -> bool:
        """Start all servers in the correct order"""
        logger.info("🚀 Starting KPP Simulator - All Components")
        logger.info("=" * 50)
        
        for server_name in self.startup_order:
            logger.info(f"\n📡 Starting {server_name.replace('_', ' ').title()}...")
            
            if server_name == 'master_clock':
                success = self.start_master_clock()
            elif server_name == 'backend_api':
                success = self.start_backend_api()
            elif server_name == 'websocket_server':
                success = self.start_websocket_server()
            elif server_name == 'dashboard':
                success = self.start_dashboard()
            else:
                success = False
            
            if not success:
                logger.error(f"❌ Failed to start {server_name}. Stopping all servers...")
                self.stop_all_servers()
                return False
            
            # Wait between server starts
            time.sleep(1)
        
        self.running = True
        logger.info("\n" + "=" * 50)
        logger.info("🎉 KPP Simulator Started Successfully!")
        logger.info("=" * 50)
        logger.info("📊 Dashboard: http://localhost:9103")
        logger.info("🔧 API Status: http://localhost:9100/status")
        logger.info("⏰ Master Clock: http://localhost:9201/health")
        logger.info("🔌 WebSocket: ws://localhost:9101/state")
        logger.info("=" * 50)
        logger.info("Press Ctrl+C to stop all servers")
        
        return True
    
    def stop_server(self, server_name: str):
        """Stop a specific server"""
        if server_name in self.processes:
            process = self.processes[server_name]
            try:
                logger.info(f"Stopping {server_name}...")
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"✅ {server_name} stopped")
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing {server_name}...")
                process.kill()
            except Exception as e:
                logger.error(f"Error stopping {server_name}: {e}")
            finally:
                del self.processes[server_name]
    
    def stop_all_servers(self):
        """Stop all running servers"""
        logger.info("\n🛑 Stopping all KPP Simulator servers...")
        
        # Stop in reverse order
        for server_name in reversed(self.startup_order):
            if server_name in self.processes:
                self.stop_server(server_name)
        
        self.running = False
        logger.info("✅ All servers stopped")
    
    def get_status(self) -> Dict[str, bool]:
        """Get status of all servers"""
        status = {}
        for server_name in self.startup_order:
            status[server_name] = self._check_server_health(server_name)
        return status
    
    def print_status(self):
        """Print current status of all servers"""
        logger.info("\n📊 Server Status:")
        logger.info("-" * 30)
        
        status = self.get_status()
        for server_name, is_running in status.items():
            port = self.ports[server_name]
            status_icon = "✅" if is_running else "❌"
            logger.info(f"{status_icon} {server_name.replace('_', ' ').title()}: http://localhost:{port}")
    
    def monitor_servers(self):
        """Monitor all servers and restart if needed"""
        while self.running:
            try:
                time.sleep(10)  # Check every 10 seconds
                
                for server_name in self.startup_order:
                    if not self._check_server_health(server_name):
                        logger.warning(f"⚠️ {server_name} is not responding, attempting restart...")
                        
                        # Stop the server
                        self.stop_server(server_name)
                        
                        # Restart the server
                        if server_name == 'master_clock':
                            self.start_master_clock()
                        elif server_name == 'backend_api':
                            self.start_backend_api()
                        elif server_name == 'websocket_server':
                            self.start_websocket_server()
                        elif server_name == 'dashboard':
                            self.start_dashboard()
                        
                        logger.info(f"🔄 {server_name} restart completed")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("\n🛑 Received shutdown signal...")
    if hasattr(signal_handler, 'manager'):
        signal_handler.manager.stop_all_servers()
    sys.exit(0)

def main():
    """Main entry point"""
    print("🚀 KPP Simulator - Advanced Kinetic Power Plant Simulation")
    print("=" * 60)
    
    # Check if required files exist
    required_files = [
        'realtime_sync_master_fixed.py',
        'app.py',
        'main.py',
        'dash_app.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"❌ Missing required files: {', '.join(missing_files)}")
        logger.error("Please ensure all server files are present in the current directory")
        return False
    
    # Create manager
    manager = SimulatorManager()
    signal_handler.manager = manager
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start all servers
        if not manager.start_all_servers():
            return False
        
        # Print initial status
        manager.print_status()
        
        # Start monitoring in background
        monitor_thread = threading.Thread(target=manager.monitor_servers, daemon=True)
        monitor_thread.start()
        
        # Keep main thread alive
        while manager.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutdown requested by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        manager.stop_all_servers()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 