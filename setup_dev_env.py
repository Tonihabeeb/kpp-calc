import venv
import sys
import subprocess
import os
import argparse
from pathlib import Path
            import shutil
#!/usr/bin/env python3
"""
KPP Simulator - Development Environment Setup Script

This script automates the setup of a development environment for the KPP Simulator.
It handles virtual environment creation, dependency installation,
     and development tool setup.

Usage:
    python setup_dev_env.py [--force] [--advanced]

Options:
    --force     : Force recreation of virtual environment if it exists
    --advanced  : Install advanced/optional dependencies
"""

