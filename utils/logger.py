import logging

# Configure root logger (done once in the application entry point)
logging.basicConfig(
    level=logging.DEBUG,
    filename="simulation.log",
    filemode="w",
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)

class Logger:
    """
    Utility class for obtaining configured logger instances.
    """
    @staticmethod
    def get_logger(name: str):
        """
        Get a logger with the given name, creating it if not already exists.
        """
        return logging.getLogger(name)
