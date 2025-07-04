#!/usr/bin/env python3
"""
KPP Simulator Synchronized System Launcher
Starts all servers in the correct order for real-time synchronization
"""

import subprocess
import time
import logging
import sys
import os
import signal
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KPPSynchronizedSystemLauncher:
    """Launcher for the complete KPP synchronized system"""
    
    def __init__(self):
        self.processes = []
        self.server_configs = [
            {
                'name': 'Flask Backend',
                'script': 'app.py',
                'port': 9100,
                'health_url': 'http://localhost:9100/status',
                'startup_delay': 3
            },
            {
                'name': 'Master Clock Server',
                'script': 'realtime_sync_master.py',
                'port': 9200,
                'health_url': 'http://localhost:9200/health',
                'startup_delay': 2
            },
            {
                'name': 'WebSocket Server',
                'script': 'main.py',
                'port': 9101,
                'health_url': 'http://localhost:9101/',
                'startup_delay': 2
            },
            {
                'name': 'Dash Frontend',
                'script': 'dash_app.py',
                'port': 9103,
                'health_url': 'http://localhost:9103/',
                'startup_delay': 3
            }
        ]
        
    def check_port_available(self, port):
        """Check if a port is available"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) != 0
    
    def wait_for_server(self, config, timeout=30):
        """Wait for a server to become healthy"""
        logger.info(f"Waiting for {config['name']} to start on port {config['port']}...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(config['health_url'], timeout=2)
                if response.status_code == 200:
                    logger.info(f"✅ {config['name']} is healthy!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
        
        logger.error(f"❌ {config['name']} failed to start within {timeout}s")
        return False
    
    def start_server(self, config):
        """Start a single server"""
        logger.info(f"🚀 Starting {config['name']}...")
        
        # Check if port is available
        if not self.check_port_available(config['port']):
            logger.warning(f"⚠️ Port {config['port']} is already in use")
            return None
        
        try:
            # Start the process
            process = subprocess.Popen(
                [sys.executable, config['script']],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            self.processes.append({
                'name': config['name'],
                'process': process,
                'config': config
            })
            
            # Wait for startup
            time.sleep(config['startup_delay'])
            
            # Check if process is still running
            if process.poll() is None:
                logger.info(f"✅ {config['name']} process started (PID: {process.pid})")
                return process
            else:
                stdout, stderr = process.communicate()
                logger.error(f"❌ {config['name']} failed to start")
                logger.error(f"stdout: {stdout.decode()}")
                logger.error(f"stderr: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to start {config['name']}: {e}")
            return None
    
    def start_all_servers(self):
        """Start all servers in the correct order"""
        logger.info("🔄 Starting KPP Synchronized System...")
        logger.info("=" * 60)
        
        success_count = 0
        
        for config in self.server_configs:
            process = self.start_server(config)
            
            if process:
                # Wait for server to become healthy
                if self.wait_for_server(config):
                    success_count += 1
                else:
                    logger.error(f"❌ {config['name']} failed health check")
            
            # Small delay between servers
            time.sleep(1)
        
        logger.info("=" * 60)
        
        if success_count == len(self.server_configs):
            logger.info("🎉 All servers started successfully!")
            self.print_system_status()
            return True
        else:
            logger.error(f"❌ Only {success_count}/{len(self.server_configs)} servers started successfully")
            return False
    
    def print_system_status(self):
        """Print the current system status"""
        logger.info("\n📊 KPP Synchronized System Status:")
        logger.info("-" * 50)
        
        for config in self.server_configs:
            try:
                response = requests.get(config['health_url'], timeout=2)
                status = "🟢 HEALTHY" if response.status_code == 200 else "🟡 DEGRADED"
            except:
                status = "🔴 OFFLINE"
            
            logger.info(f"{config['name']:20} | Port {config['port']} | {status}")
        
        logger.info("-" * 50)
        logger.info("🌐 Access URLs:")
        logger.info(f"  • Backend API:     http://localhost:9100")
        logger.info(f"  • Master Clock:    http://localhost:9200/metrics")
        logger.info(f"  • WebSocket:       http://localhost:9101")
        logger.info(f"  • Dashboard:       http://localhost:9103")
        logger.info("-" * 50)
    
    def stop_all_servers(self):
        """Stop all running servers"""
        logger.info("🛑 Stopping all servers...")
        
        for server_info in self.processes:
            try:
                process = server_info['process']
                if process.poll() is None:  # Process is still running
                    logger.info(f"Stopping {server_info['name']}...")
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Force killing {server_info['name']}...")
                        process.kill()
                        process.wait()
                    
                    logger.info(f"✅ {server_info['name']} stopped")
                    
            except Exception as e:
                logger.error(f"Error stopping {server_info['name']}: {e}")
        
        self.processes.clear()
        logger.info("✅ All servers stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"\n🛑 Received signal {signum}, shutting down...")
        self.stop_all_servers()
        sys.exit(0)

def main():
    """Main launcher function"""
    launcher = KPPSynchronizedSystemLauncher()
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, launcher.signal_handler)
    signal.signal(signal.SIGTERM, launcher.signal_handler)
    
    try:
        # Start all servers
        if launcher.start_all_servers():
            logger.info("\n🎯 System ready for real-time synchronized operation!")
            logger.info("Press Ctrl+C to stop all servers")
            
            # Keep the launcher running
            while True:
                time.sleep(10)
                
                # Periodic health check
                try:
                    healthy_count = 0
                    for config in launcher.server_configs:
                        try:
                            response = requests.get(config['health_url'], timeout=1)
                            if response.status_code == 200:
                                healthy_count += 1
                        except:
                            pass
                    
                    if healthy_count < len(launcher.server_configs):
                        logger.warning(f"⚠️ Only {healthy_count}/{len(launcher.server_configs)} servers healthy")
                    
                except KeyboardInterrupt:
                    break
        
        else:
            logger.error("❌ Failed to start system")
            launcher.stop_all_servers()
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        launcher.stop_all_servers()
        sys.exit(1)

if __name__ == "__main__":
    main() 