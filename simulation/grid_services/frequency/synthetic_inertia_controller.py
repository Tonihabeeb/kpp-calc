import time
import math
from typing import Any, Dict, Optional
from dataclasses import dataclass
from collections import deque
"""
Synthetic Inertia Controller

Provides virtual inertia response to emulate synchronous generator behavior.
Implements ROCOF (Rate of Change of Frequency) detection and fast response.

Response time: <500ms
ROCOF threshold: 0.5 Hz/s (configurable)
Inertia constant: 2-8 seconds (configurable)
Response duration: 10-30 seconds
Measurement window: 100ms for ROCOF calculation
"""

