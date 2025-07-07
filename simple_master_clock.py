import uvicorn
import uuid
import time
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
Simple Master Clock Server for KPP Simulator
Basic version without backend dependencies during startup
"""

