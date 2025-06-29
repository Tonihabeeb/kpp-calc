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
    airPressure: float = 3.0
    air_fill_time: float = 0.5
    air_pressure: float = 300000
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
            if self.running:
                self.tick()
                self.broadcast()
            time.sleep(0.1)

    def tick(self):
        with self.lock:
            self.state.tick += 1
            self.state.timestamp = time.time()
            self.state.data = {"example": self.state.tick}  # Replace with real simulation logic
            logging.info(f"tick() -> {self.state}")

    def broadcast(self):
        for queue in self.listeners:
            try:
                queue.put_nowait(self.state.dict())
            except Exception as e:
                logging.warning(f"Broadcast failed: {e}")
        logging.info(f"broadcast() -> {len(self.listeners)} clients")

    def register_listener(self, queue: asyncio.Queue):
        self.listeners.append(queue)

    def unregister_listener(self, queue: asyncio.Queue):
        if queue in self.listeners:
            self.listeners.remove(queue)

# --- FastAPI App ---
logging.basicConfig(level=logging.INFO)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
sim_core = SimulationCore(SimulationConfig())
sim_core.start()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()
    sim_core.register_listener(queue)
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
