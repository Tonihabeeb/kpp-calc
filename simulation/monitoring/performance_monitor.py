import time
import threading
import psutil
import os
import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from collections import deque
"""
Performance monitoring system for KPP Simulator.

This module provides comprehensive performance monitoring including:
- Step execution time tracking
- Memory usage monitoring
- Error rate tracking
- Performance alerts and warnings
"""

