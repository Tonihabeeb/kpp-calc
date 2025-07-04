#!/usr/bin/env python3
"""
Improved KPP Service Manager
Handles service dependencies, graceful startup/shutdown, and better error handling
"""
import subprocess
import time
import signal
import sys
import os
import requests
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    name: str
    script: str
    port: int
    health_url: str
    startup_delay: int
    dependencies: List[str]
    max_retries: int = 3
    health_timeout: int = 5

class ImprovedServiceManager:
    def __init__(self):
        self.services: Dict[str, ServiceConfig] = {
            'flask_backend': ServiceConfig(
                name="Flask Backend",
                script="app.py",
                port=9100,
                health_url="http://localhost:9100/status",
                startup_delay=3,
                dependencies=[],
                max_retries=3
            ),
            'master_clock': ServiceConfig(
                name="Master Clock Server",
                script="realtime_sync_master_fixed.py",
                port=9201,
                health_url="http://localhost:9201/health",
                startup_delay=2,
                dependencies=['flask_backend'],
                max_retries=3
            ),
            'websocket_server': ServiceConfig(
                name="WebSocket Server",
                script="main.py",
                port=9101,
                health_url="http://localhost:9101/",
                startup_delay=2,
                dependencies=['flask_backend'],
                max_retries=3
            ),
            'dash_frontend': ServiceConfig(
                name="Dash Frontend",
                script="simple_ui.py",
                port=9103,
                health_url="http://localhost:9103/",
                startup_delay=3,
                dependencies=['flask_backend', 'websocket_server'],
                max_retries=3
            )
        }
        
        self.running_processes: Dict[str, subprocess.Popen] = {}
        self.service_status: Dict[str, str] = {}  # 'running', 'stopped', 'error'
        self.shutdown_requested = False
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
        self.stop_all_services()
        sys.exit(0)
    
    def check_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) != 0
    
    def check_service_health(self, config: ServiceConfig) -> bool:
        """Check if a service is healthy"""
        try:
            response = requests.get(config.health_url, timeout=config.health_timeout)
            return response.status_code == 200
        except:
            return False
    
    def wait_for_service_health(self, config: ServiceConfig, timeout: int = 30) -> bool:
        """Wait for a service to become healthy"""
        logger.info(f"Waiting for {config.name} to become healthy...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.check_service_health(config):
                logger.info(f"✅ {config.name} is healthy!")
                return True
            time.sleep(1)
        
        logger.error(f"❌ {config.name} failed to become healthy within {timeout}s")
        return False
    
    def start_service(self, service_name: str) -> bool:
        """Start a single service with dependency checking"""
        config = self.services[service_name]
        
        # Check dependencies first
        for dep_name in config.dependencies:
            if not self.check_service_health(self.services[dep_name]):
                logger.error(f"❌ Cannot start {config.name}: dependency {dep_name} not healthy")
                return False
        
        logger.info(f"🚀 Starting {config.name}...")
        
        # Check if port is available
        if not self.check_port_available(config.port):
            logger.warning(f"⚠️ Port {config.port} is already in use")
            
            # Check if the service is actually healthy
            if self.check_service_health(config):
                logger.info(f"✅ {config.name} is already running and healthy!")
                self.service_status[service_name] = 'running'
                return True
            else:
                logger.error(f"❌ {config.name} port in use but service not healthy")
                return False
        
        # Start the service
        try:
            process = subprocess.Popen(
                [sys.executable, config.script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            self.running_processes[service_name] = process
            
            # Wait for startup
            time.sleep(config.startup_delay)
            
            # Check if process is still running
            if process.poll() is None:
                logger.info(f"✅ {config.name} process started (PID: {process.pid})")
                
                # Wait for health check
                if self.wait_for_service_health(config):
                    self.service_status[service_name] = 'running'
                    return True
                else:
                    self.service_status[service_name] = 'error'
                    return False
            else:
                stdout, stderr = process.communicate()
                logger.error(f"❌ {config.name} failed to start")
                logger.error(f"stdout: {stdout.decode()}")
                logger.error(f"stderr: {stderr.decode()}")
                self.service_status[service_name] = 'error'
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start {config.name}: {e}")
            self.service_status[service_name] = 'error'
            return False
    
    def start_all_services(self) -> bool:
        """Start all services in dependency order"""
        logger.info("🔄 Starting KPP Services with Improved Management...")
        logger.info("=" * 60)
        
        # Sort services by dependencies (topological sort)
        service_order = self._get_service_order()
        
        success_count = 0
        for service_name in service_order:
            if self.shutdown_requested:
                break
                
            if self.start_service(service_name):
                success_count += 1
            else:
                logger.error(f"❌ Failed to start {service_name}, stopping startup sequence")
                self.stop_all_services()
                return False
        
        logger.info("=" * 60)
        
        if success_count == len(self.services):
            logger.info("🎉 All services started successfully!")
            self.print_status()
            return True
        else:
            logger.error(f"❌ Only {success_count}/{len(self.services)} services started successfully")
            return False
    
    def _get_service_order(self) -> List[str]:
        """Get service startup order based on dependencies"""
        # Simple topological sort
        visited = set()
        order = []
        
        def visit(service_name):
            if service_name in visited:
                return
            visited.add(service_name)
            
            # Visit dependencies first
            for dep in self.services[service_name].dependencies:
                visit(dep)
            
            order.append(service_name)
        
        for service_name in self.services:
            visit(service_name)
        
        return order
    
    def stop_service(self, service_name: str):
        """Stop a single service gracefully"""
        config = self.services[service_name]
        
        if service_name in self.running_processes:
            process = self.running_processes[service_name]
            logger.info(f"🛑 Stopping {config.name}...")
            
            try:
                # Try graceful shutdown first
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"✅ {config.name} stopped gracefully")
            except subprocess.TimeoutExpired:
                logger.warning(f"⚠️ Force killing {config.name}...")
                process.kill()
                process.wait()
                logger.info(f"✅ {config.name} force stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping {config.name}: {e}")
            
            del self.running_processes[service_name]
        
        self.service_status[service_name] = 'stopped'
    
    def stop_all_services(self):
        """Stop all services in reverse dependency order"""
        logger.info("🛑 Stopping all services...")
        
        # Stop in reverse order
        service_order = self._get_service_order()
        for service_name in reversed(service_order):
            self.stop_service(service_name)
        
        logger.info("✅ All services stopped")
    
    def print_status(self):
        """Print current system status"""
        logger.info("\n📊 KPP Service Status:")
        logger.info("-" * 50)
        
        for service_name, config in self.services.items():
            status = self.service_status.get(service_name, 'unknown')
            health = "🟢 HEALTHY" if self.check_service_health(config) else "🔴 UNHEALTHY"
            
            logger.info(f"{config.name:20} | Port {config.port} | {status.upper()} | {health}")
        
        logger.info("-" * 50)
        logger.info("🌐 Access URLs:")
        logger.info(f"  • Backend API:     http://localhost:9100")
        logger.info(f"  • Master Clock:    http://localhost:9201/metrics")
        logger.info(f"  • WebSocket:       http://localhost:9101")
        logger.info(f"  • Dashboard:       http://localhost:9103")
        logger.info("-" * 50)
    
    def monitor_services(self):
        """Monitor services and restart failed ones"""
        logger.info("🔍 Starting service monitoring...")
        
        while not self.shutdown_requested:
            try:
                # Check all services
                for service_name, config in self.services.items():
                    if service_name in self.running_processes:
                        process = self.running_processes[service_name]
                        
                        # Check if process is still running
                        if process.poll() is not None:
                            logger.warning(f"⚠️ {config.name} process died, restarting...")
                            self.stop_service(service_name)
                            if not self.start_service(service_name):
                                logger.error(f"❌ Failed to restart {config.name}")
                        
                        # Check health
                        elif not self.check_service_health(config):
                            logger.warning(f"⚠️ {config.name} not responding, restarting...")
                            self.stop_service(service_name)
                            if not self.start_service(service_name):
                                logger.error(f"❌ Failed to restart {config.name}")
                
                time.sleep(10)  # Check every 10 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                time.sleep(5)

def main():
    """Main function"""
    manager = ImprovedServiceManager()
    
    try:
        # Start all services
        if manager.start_all_services():
            logger.info("\n🎯 System ready for operation!")
            logger.info("Press Ctrl+C to stop all services")
            
            # Start monitoring
            manager.monitor_services()
        else:
            logger.error("❌ Failed to start system")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        manager.stop_all_services()
        sys.exit(1)

if __name__ == "__main__":
    main() 