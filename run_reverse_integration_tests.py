import time
import threading
import sys
import subprocess
import signal
import requests
import psutil
import os
import logging
import json
from pathlib import Path
from datetime import datetime
#!/usr/bin/env python3
"""
Comprehensive Reverse Integration Test Runner for KPP Simulator
Tests complete flows from backend endpoints → main server → frontend

This runner:
1. Starts all required services (Flask, WebSocket, Dash)
2. Runs reverse integration tests with real services
3. Provides comprehensive reporting
4. Cleans up services after testing
"""

