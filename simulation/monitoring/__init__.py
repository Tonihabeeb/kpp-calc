try:
    from .real_time_monitor import RealTimeMonitor
except ImportError:
    class RealTimeMonitor:
        pass

"""
Monitoring module initialization
"""

