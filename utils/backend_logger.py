import logging
import os
import sys


def setup_backend_logger(log_file="simulation.log", level=logging.DEBUG):
    """Set up a backend logger that writes to a file and the console."""
    logger = logging.getLogger()
    logger.setLevel(level)
    # Remove all handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    # File handler
    fh = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    fh.setLevel(level)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    # Try to set encoding for console handler if possible
    if hasattr(ch, "setStream") and hasattr(ch.stream, "reconfigure"):
        try:
            ch.stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    logger.addHandler(ch)
    logger.info(f"Backend logger initialized. Logging to {os.path.abspath(log_file)}")


# To use: import and call setup_backend_logger() at the start of your app
