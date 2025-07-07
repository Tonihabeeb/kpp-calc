import websockets
import uvicorn
import uuid
import time
import threading
import requests
import logging
import json
import asyncio
from typing import Dict, List, Set, Any, Optional
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import deque
#!/usr/bin/env python3
"""
Master Clock Server for KPP Simulator Real-Time Synchronization
Provides centralized timing coordination for all servers
FIXED VERSION with better error handling
"""

