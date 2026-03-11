#!/usr/bin/env python3
"""Professional Background Remover Pro v2.1 — Entry Point.

Usage:
    python main.py
"""

import sys
import tkinter as tk

from ui.main_window import MainWindow
from utils.logger import setup_logger

logger = setup_logger("bgremover")


def main() -> None:
    """Launch the application."""
    logger.info("Professional Background Remover Pro v2.1 starting...")

    root = tk.Tk()

    try:
        app = MainWindow(root)
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
    except Exception as e:
        logger.critical("Unexpected error: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
