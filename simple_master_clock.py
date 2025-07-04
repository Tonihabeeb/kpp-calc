#!/usr/bin/env python3
"""
Simple Master Clock Server for KPP Simulator
Basic version without backend dependencies during startup
"""

import asyncio
import time
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FrameData:
    """Represents a synchronized frame of data"""
    frame_id: int
    timestamp: float
    simulation_time: float
    power: float
    torque: float
    efficiency: float
    status: str
    metadata: Dict[str, Any]

@dataclass
class ClientConnection:
    """Represents a connected client"""
    client_id: str
    websocket: Optional[WebSocket]
    client_type: str
    last_ping: float
    frame_buffer: deque
    max_buffer_size: int = 60

class SimpleMasterClockServer:
    """Simple master synchronization server"""
    
    def __init__(self, target_fps: int = 30):
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.running = False
        
        # Synchronization state
        self.master_clock = 0.0
        self.frame_counter = 0
        self.clients: Dict[str, ClientConnection] = {}
        self.data_buffer = deque(maxlen=1000)
        
        # Performance metrics
        self.metrics = {
            'frames_sent': 0,
            'clients_connected': 0,
            'average_latency': 0.0,
            'frame_drops': 0,
            'sync_errors': 0
        }
        
        # Latest simulation data (dummy data for now)
        self.latest_frame = FrameData(
            frame_id=0,
            timestamp=time.time(),
            simulation_time=0.0,
            power=0.0,
            torque=0.0,
            efficiency=0.0,
            status='standalone',
            metadata={'mode': 'standalone', 'note': 'No backend connection'}
        )
        
        logger.info(f"Simple Master Clock Server initialized - Target FPS: {target_fps}")
    
    async def register_client(self, websocket: WebSocket, client_type: str) -> str:
        """Register a new client connection"""
        client_id = f"{client_type}_{uuid.uuid4().hex[:8]}"
        
        self.clients[client_id] = ClientConnection(
            client_id=client_id,
            websocket=websocket,
            client_type=client_type,
            last_ping=time.time(),
            frame_buffer=deque(maxlen=60)
        )
        
        self.metrics['clients_connected'] = len(self.clients)
        logger.info(f"Client registered: {client_id} ({client_type})")
        
        return client_id
    
    async def unregister_client(self, client_id: str):
        """Unregister a client connection"""
        if client_id in self.clients:
            del self.clients[client_id]
            self.metrics['clients_connected'] = len(self.clients)
            logger.info(f"Client unregistered: {client_id}")
    
    def generate_dummy_frame(self) -> FrameData:
        """Generate dummy frame data for testing"""
        current_time = time.time()
        
        frame = FrameData(
            frame_id=self.frame_counter,
            timestamp=current_time,
            simulation_time=current_time % 100,  # Cycle through 0-100 seconds
            power=100.0 + (current_time % 50),  # Varying power
            torque=50.0 + (current_time % 30),  # Varying torque
            efficiency=0.8 + (current_time % 20) / 100,  # Varying efficiency
            status='standalone',
            metadata={
                'mode': 'standalone',
                'note': 'Dummy data for testing',
                'cycle_time': current_time % 60
            }
        )
        
        return frame
    
    async def broadcast_frame(self, frame: FrameData):
        """Broadcast synchronized frame to all clients"""
        frame_data = {
            'type': 'frame_update',
            'frame': asdict(frame),
            'master_clock': self.master_clock,
            'sync_info': {
                'frame_interval': self.frame_interval,
                'target_fps': self.target_fps,
                'server_timestamp': time.time()
            }
        }
        
        # Send to all connected WebSocket clients
        disconnected_clients = []
        
        for client_id, client in self.clients.items():
            try:
                if client.websocket:
                    await client.websocket.send_json(frame_data)
                    client.last_ping = time.time()
                    
                    # Buffer frame for client
                    client.frame_buffer.append(frame)
                    
            except Exception as e:
                logger.warning(f"Error sending to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.unregister_client(client_id)
        
        self.metrics['frames_sent'] += 1
    
    async def sync_loop(self):
        """Main synchronization loop running at target FPS"""
        logger.info(f"Starting sync loop at {self.target_fps} FPS")
        self.running = True
        
        last_frame_time = time.time()
        
        while self.running:
            try:
                loop_start = time.time()
                
                # Update master clock
                self.master_clock = loop_start
                self.frame_counter += 1
                
                # Generate dummy frame data
                frame = self.generate_dummy_frame()
                self.latest_frame = frame
                
                # Store in buffer
                self.data_buffer.append(frame)
                
                # Broadcast to all clients
                await self.broadcast_frame(frame)
                
                # Calculate timing for next frame
                loop_duration = time.time() - loop_start
                sleep_time = max(0, self.frame_interval - loop_duration)
                
                # Performance monitoring
                if self.frame_counter % 100 == 0:  # Log every ~3.3 seconds
                    actual_fps = 1.0 / (loop_start - last_frame_time + 1e-9)
                    logger.info(f"Frame {self.frame_counter}: FPS={actual_fps:.1f}, "
                              f"Clients={len(self.clients)}, Latency={loop_duration*1000:.1f}ms")
                    last_frame_time = loop_start
                
                # Sleep until next frame
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                else:
                    self.metrics['frame_drops'] += 1
                    
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                self.metrics['sync_errors'] += 1
                # Continue running despite errors
                await asyncio.sleep(0.1)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            **self.metrics,
            'master_clock': self.master_clock,
            'frame_counter': self.frame_counter,
            'buffer_size': len(self.data_buffer),
            'uptime': time.time() - (self.master_clock - self.frame_counter * self.frame_interval),
            'latest_frame': asdict(self.latest_frame)
        }
    
    def start_sync_task(self):
        """Start the synchronization loop in background"""
        if not self.running:
            try:
                self.sync_task = asyncio.create_task(self.sync_loop())
                logger.info("Sync task started successfully")
            except Exception as e:
                logger.error(f"Failed to start sync task: {e}")
    
    def stop(self):
        """Stop the synchronization server"""
        self.running = False
        logger.info("Simple Master Clock Server stopped")

# FastAPI app
app = FastAPI(title="KPP Simple Master Clock Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global master clock instance
master_clock = SimpleMasterClockServer(target_fps=30)

@app.on_event("startup")
async def startup_event():
    """Start the master clock when server starts"""
    try:
        logger.info("Starting simple master clock sync task...")
        master_clock.start_sync_task()
        logger.info("Simple master clock sync task started successfully")
    except Exception as e:
        logger.error(f"Failed to start simple master clock: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the master clock when server shuts down"""
    try:
        master_clock.stop()
        logger.info("Simple master clock stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping simple master clock: {e}")

@app.websocket("/sync")
async def websocket_sync_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time synchronization"""
    await websocket.accept()
    
    # Get client type from query parameters
    client_type = websocket.query_params.get('type', 'unknown')
    client_id = await master_clock.register_client(websocket, client_type)
    
    try:
        while True:
            # Keep connection alive and handle client messages
            message = await websocket.receive_json()
            
            # Handle ping/pong for connection health
            if message.get('type') == 'ping':
                await websocket.send_json({
                    'type': 'pong',
                    'client_id': client_id,
                    'server_time': time.time()
                })
            
    except WebSocketDisconnect:
        await master_clock.unregister_client(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        await master_clock.unregister_client(client_id)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'running': master_clock.running,
        'metrics': master_clock.get_metrics()
    }

@app.get("/metrics")
async def get_metrics():
    """Get detailed performance metrics"""
    return master_clock.get_metrics()

@app.get("/frame/latest")
async def get_latest_frame():
    """Get the latest synchronized frame"""
    return {
        'frame': asdict(master_clock.latest_frame),
        'master_clock': master_clock.master_clock,
        'frame_counter': master_clock.frame_counter
    }

if __name__ == "__main__":
    logger.info("Starting KPP Simple Master Clock Server on port 9200")
    uvicorn.run(app, host="0.0.0.0", port=9200, log_level="info") 