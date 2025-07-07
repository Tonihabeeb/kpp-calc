import time
import math
from typing import Any, Dict, Optional
from dataclasses import dataclass
from collections import deque
"""
Voltage Regulator

Provides automatic voltage regulation (AVR) services for maintaining voltage
stability at the point of interconnection through reactive power control.

Response time: <500ms for fast voltage changes
Voltage range: 0.95-1.05 p.u.
Reactive power capacity: ±30% of rated power
Dead band: ±1% of nominal voltage
Droop: 2-5% typical
"""

