import uuid
import time
import requests
import json
from observability import TRACE_HEADER
#!/usr/bin/env python3
"""
Comprehensive Endpoint Test for KPP Simulator
Tests all 160 discovered endpoints with trace correlation

Endpoints discovered by verification:
- 48 Flask backend endpoints
- 3 WebSocket server endpoints
- 106 Dash callback interactions
- 3 Observability endpoints
"""

