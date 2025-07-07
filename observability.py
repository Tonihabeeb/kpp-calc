import uuid
import time
import threading
import sys
import signal
import logging
import json
import functools
import atexit
from typing import Dict, Any, Optional, Callable
from flask import g, request, current_app
from datetime import datetime
from collections import defaultdict, deque
# observability.py
"""
KPP Simulator - Backend Observability & Tracing System
Provides end-to-end trace-ID correlation for Flask/Dash applications
"""

