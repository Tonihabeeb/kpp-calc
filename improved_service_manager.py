import time
import sys
import subprocess
import signal
import requests
import os
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager
        import socket
#!/usr/bin/env python3
"""
Improved KPP Service Manager
Handles service dependencies, graceful startup/shutdown, and better error handling
"""
