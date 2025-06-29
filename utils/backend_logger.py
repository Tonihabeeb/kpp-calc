import logging
import os


def setup_backend_logger(log_file="simulation.log", level=logging.DEBUG):
    """Set up a backend logger that writes to a file and the console."""
    logger = logging.getLogger()
    logger.setLevel(level)
    # Remove all handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    # File handler
    fh = logging.FileHandler(log_file, mode="w")
    fh.setLevel(level)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.info(f"Backend logger initialized. Logging to {os.path.abspath(log_file)}")


# To use: import and call setup_backend_logger() at the start of your app
