import time
import math
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
"""
Dynamic Voltage Support

Provides fast dynamic voltage support for grid stability through rapid
reactive power injection during voltage transients and disturbances.

Response time: <100ms for voltage events
Voltage change threshold: >2% voltage deviation
Maximum reactive power: ±40% of rated power
Hold time: 5-30 seconds after event
Recovery time: <10 seconds
"""

