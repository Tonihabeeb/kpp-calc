import time
import math
from typing import Any, Dict, Optional
from dataclasses import dataclass
"""
Primary Frequency Controller

Provides fast frequency response for grid stability through primary frequency control.
Implements droop control with configurable dead band and response characteristics.

Response time: <2 seconds
Dead band: ±0.02 Hz (configurable)
Droop setting: 2-5% (configurable)
Response range: ±10% of rated power
"""

