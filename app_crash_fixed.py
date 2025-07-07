import time
import threading
import queue
import logging
from flask_cors import CORS
from flask import Flask, request, jsonify
        from simulation.engine import SimulationEngine
            import json
# CRASH-FIXED Flask app - Removes blocking operations that cause timeouts
