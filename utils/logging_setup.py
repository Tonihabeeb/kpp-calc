"""Logger configuration (stub)."""

import logging
import sys
import warnings

try:
    from colorlog import ColoredFormatter
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


def setup_logging():
    # Check if logging is already configured to prevent duplicate setup
    if logging.getLogger().handlers:
        return  # Already configured, skip setup
    
    # Check if we've already set up logging (global flag)
    if hasattr(setup_logging, '_configured'):
        return
    setup_logging._configured = True
    
    # Remove all handlers
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

    logging.info("Logging setup complete. Warnings and errors will be shown in the terminal in real time.")
