import time
from typing import Any, Dict, Optional
from enum import Enum
from dataclasses import dataclass
from collections import deque
"""
Load Curtailment Controller

Provides emergency load reduction and economic curtailment services for
grid reliability and economic optimization. Implements utility demand
response programs and automated load shedding capabilities.

Response time: <60 seconds for emergency
Curtailment capacity: 10-50% of connected load
Duration: 1 minute to 6 hours
Recovery time: <5 minutes
Frequency: <10 events per month
"""

