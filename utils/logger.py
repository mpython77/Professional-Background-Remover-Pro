"""Professional logging system — file + console output."""

import os
import sys
import logging
from typing import Dict

# Logger singleton cache — prevents creating duplicate handlers
_loggers: Dict[str, logging.Logger] = {}

LOG_DIR = os.path.join(os.path.expanduser("~"), ".bgremover_logs")
LOG_FILE = os.path.join(LOG_DIR, "bgremover.log")

# Create the formatter once
_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# File handler — singleton (shared by all loggers)
_file_handler = None


def _get_file_handler() -> logging.FileHandler:
    """Return a singleton file handler."""
    global _file_handler
    if _file_handler is None:
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
            _file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
            _file_handler.setLevel(logging.DEBUG)
            _file_handler.setFormatter(_FORMATTER)
        except OSError:
            _file_handler = logging.NullHandler()
    return _file_handler


def setup_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """Create a professional logger or return an existing one.

    Uses the singleton pattern — a logger with the same name is
    never created twice.

    Args:
        name: Logger name (typically __name__).
        level: Logging level.

    Returns:
        A configured Logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Only add handlers if they haven't been added already
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(_FORMATTER)

        logger.addHandler(console_handler)
        logger.addHandler(_get_file_handler())

    # Disable propagation to prevent duplicate log entries
    logger.propagate = False

    _loggers[name] = logger
    return logger
