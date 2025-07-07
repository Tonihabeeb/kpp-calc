import websockets
import uvicorn
import uuid
import time
import threading
import requests
import logging
import json
import asyncio
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from datetime import datetime
from contextlib import asynccontextmanager
from collections import deque
#!/usr/bin/env python3
"""
Synchronized WebSocket server for KPP simulation data
Connects to master clock for real-time coordination
"""

