import threading
import queue
from typing import Dict, Any

from .engine import SimulationEngine
import config


class SimulationController:
    """Handle engine threads and provide simple start/stop interface."""

    def __init__(self, params: Dict[str, Any] | None = None):
        self.params = params or config.DEFAULT_PARAMS.copy()
        self.data_queue = queue.Queue()
        self.engine = SimulationEngine(self.params, self.data_queue)
        self.thread: threading.Thread | None = None

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.engine.time = 0.0
        self.engine.running = True
        self.thread = threading.Thread(target=self.engine.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.engine.pause()
        if self.thread:
            self.thread.join(timeout=0.1)

    def update_params(self, params: Dict[str, Any]):
        self.engine.update_params(params)

    def get_queue(self):
        return self.data_queue

