import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import threading
import time

# --- Pydantic Models ---
class SimulationConfig(BaseModel):
    num_floaters: int = 8
    floater_volume: float = 0.3
    floater_mass_empty: float = 18.0
    floater_area: float = 0.035
    # Fixed: Remove duplicate air pressure fields, use consistent naming
    air_pressure: float = 300000  # Pa (Pascals)
    air_fill_time: float = 0.5
    air_flow_rate: float = 0.6
    jet_efficiency: float = 0.85
    sprocket_radius: float = 0.5
    flywheel_inertia: float = 50.0
    pulse_interval: float = 2.0
    nanobubble_frac: float = 0.0
    thermal_coeff: float = 0.0001
    water_temp: float = 20.0
    ref_temp: float = 20.0

class SimulationState(BaseModel):
    tick: int
    timestamp: float
    data: Dict[str, Any]

# --- Simulation Core ---
class SimulationCore:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.state = SimulationState(tick=0, timestamp=time.time(), data={})
        self.running = False
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None
        self.listeners: List[asyncio.Queue] = []

    def start(self):
        with self.lock:
            if not self.running:
                self.running = True
                self._stop_event.clear()
                if not self._thread or not self._thread.is_alive():
                    self._thread = threading.Thread(target=self._run_loop, daemon=True)
                    self._thread.start()
                logging.info("Simulation started.")

    def stop(self):
        with self.lock:
            self.running = False
            self._stop_event.set()
            logging.info("Simulation stopped.")

    def reset(self):
        with self.lock:
            self.state = SimulationState(tick=0, timestamp=time.time(), data={})
            logging.info("Simulation reset.")

    def update_params(self, config: SimulationConfig):
        with self.lock:
            self.config = config
            logging.info(f"Simulation parameters updated: {config}")

    def _run_loop(self):
        while not self._stop_event.is_set():
            # Check running state with proper synchronization
            with self.lock:
                should_run = self.running
            
            if should_run:
                self.tick()
                self.broadcast()
            
            # Use the stop event for sleeping to enable immediate shutdown
            self._stop_event.wait(timeout=0.1)

    def tick(self):
        with self.lock:
            self.state.tick += 1
            self.state.timestamp = time.time()
            self.state.data = {"example": self.state.tick}  # Replace with real simulation logic
            logging.info(f"tick() -> {self.state}")

    def broadcast(self):
        # Clean up disconnected listeners to prevent memory leaks
        active_listeners = []
        for queue in self.listeners[:]:  # Create a copy to iterate safely
            try:
                queue.put_nowait(self.state.dict())
                active_listeners.append(queue)
            except Exception as e:
                logging.warning(f"Broadcast failed, removing listener: {e}")
                # Don't add failed listeners to active list (auto-cleanup)
        
        # Update listeners list with only active ones
        with self.lock:
            self.listeners = active_listeners
        
        logging.info(f"broadcast() -> {len(self.listeners)} clients")

    def register_listener(self, queue: asyncio.Queue):
        with self.lock:
            # Prevent excessive memory usage by limiting concurrent listeners
            if len(self.listeners) >= 100:  # Reasonable limit
                logging.warning("Maximum listener limit reached, rejecting new listener")
                return False
            self.listeners.append(queue)
            return True

    def unregister_listener(self, queue: asyncio.Queue):
        with self.lock:
            if queue in self.listeners:
                self.listeners.remove(queue)

# --- FastAPI App ---
logging.basicConfig(level=logging.INFO)
app = FastAPI()
# Configure CORS with secure defaults
# In production, replace with specific allowed origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://localhost:8000",  # Local development
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

# Get allowed origins from environment variable for production
import os
if origins_env := os.getenv("ALLOWED_ORIGINS"):
    ALLOWED_ORIGINS = origins_env.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Specific methods only
    allow_headers=["Content-Type", "Authorization"],  # Specific headers only
)
sim_core = SimulationCore(SimulationConfig())
sim_core.start()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()
    
    # Check if listener registration was successful
    if not sim_core.register_listener(queue):
        await websocket.close(code=1013, reason="Server overloaded")
        return
    
    try:
        while True:
            data = await queue.get()
            await websocket.send_json(data)
    except WebSocketDisconnect:
        sim_core.unregister_listener(queue)
    except Exception as e:
        sim_core.unregister_listener(queue)
        logging.warning(f"WebSocket error: {e}")

@app.post("/start")
def start_sim():
    sim_core.start()
    return JSONResponse({"status": "started"})

@app.post("/stop")
def stop_sim():
    sim_core.stop()
    return JSONResponse({"status": "stopped"})

@app.post("/reset")
def reset_sim():
    sim_core.reset()
    return JSONResponse({"status": "reset"})

@app.post("/update_params")
def update_params(config: SimulationConfig):
    sim_core.update_params(config)
    return JSONResponse({"status": "params updated"})

@app.get("/state", response_model=SimulationState)
def get_state():
    return sim_core.state
