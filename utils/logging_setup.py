"""Logger configuration (stub)."""

import logging
import sys
import warnings
import threading

try:
    from colorlog import ColoredFormatter
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False

# Global lock for thread-safe logging setup
_setup_lock = threading.Lock()
_setup_complete = False

def setup_logging():
    """Setup logging with thread-safe singleton pattern"""
    global _setup_complete
    
    # Use lock to ensure thread safety
    with _setup_lock:
        # Check if already configured
        if _setup_complete or logging.getLogger().handlers:
            return  # Already configured, skip setup
        
        # Mark as complete before setup to prevent recursion
        _setup_complete = True
        
        # Remove all handlers to ensure clean setup
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        log_level = logging.INFO
        log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

        if COLORLOG_AVAILABLE:
            formatter = ColoredFormatter(
                "%(log_color)s%(asctime)s [%(levelname)s] %(name)s - %(message)s",
                log_colors={
                    'DEBUG':    'cyan',
                    'INFO':     'white',
                    'WARNING':  'yellow',
                    'ERROR':    'red',
                    'CRITICAL': 'bold_red',
                },
                reset=True
            )
        else:
            formatter = logging.Formatter(log_format)

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(log_level)
        ch.setFormatter(formatter)
        logging.getLogger().addHandler(ch)
        logging.getLogger().setLevel(log_level)

        # Ensure warnings are logged
        logging.captureWarnings(True)
        warnings.simplefilter('default')  # Show all warnings
        
        # Only show warnings and errors in the terminal
        class WarningErrorFilter(logging.Filter):
            def filter(self, record):
                return record.levelno >= logging.WARNING
        
        warning_error_handler = logging.StreamHandler(sys.stdout)
        warning_error_handler.setLevel(logging.WARNING)
        warning_error_handler.setFormatter(formatter)
        warning_error_handler.addFilter(WarningErrorFilter())
        logging.getLogger().addHandler(warning_error_handler)

        # Log setup message only once
        logging.info("Logging setup complete. Warnings and errors will be shown in the terminal in real time.")
