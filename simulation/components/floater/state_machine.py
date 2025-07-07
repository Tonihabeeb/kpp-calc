import logging
from typing import Callable, Optional
from enum import Enum
from dataclasses import dataclass
"""
State machine for floater operation cycles.
Manages transitions between empty, filling, full, and venting states.
"""

