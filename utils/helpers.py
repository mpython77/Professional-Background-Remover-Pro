"""Helper functions — file opening, color conversion, EXIF parsing, debounce."""

import os
import sys
import platform
import subprocess
import threading
from typing import Tuple, Optional, Dict, Any, Callable
from functools import wraps
from PIL import Image
from PIL.ExifTags import TAGS


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert an RGB tuple to a hex color string.

    Args:
        rgb: (R, G, B) values (0-255).

    Returns:
        Hex color string, e.g. '#ff00ff'.
    """
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def resource_path(relative_path: str) -> str:
    """Return a resource path compatible with PyInstaller.

    Args:
        relative_path: Relative file path.

    Returns:
        Absolute file path.
    """
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def open_file(file_path: str) -> bool:
    """Open a file with the OS default application.

    Args:
        file_path: Path to the file to open.

    Returns:
        True if opened successfully, False otherwise.
    """
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(file_path)
        elif system == "Darwin":
            subprocess.call(["open", file_path])
        else:
            subprocess.call(["xdg-open", file_path])
        return True
    except OSError as e:
        from utils.logger import setup_logger
        logger = setup_logger(__name__)
        logger.error("Failed to open file: %s — %s", file_path, e)
        return False


def debounce(wait_seconds: float = 0.3) -> Callable:
    """Debounce a function — only the last call within the wait period is executed.

    Args:
        wait_seconds: Wait time in seconds.

    Returns:
        Decorator function.
    """
    def decorator(func: Callable) -> Callable:
        timer: Optional[threading.Timer] = None

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> None:
            nonlocal timer
            if timer is not None:
                timer.cancel()
            timer = threading.Timer(wait_seconds, func, args=args, kwargs=kwargs)
            timer.start()

        return wrapper
    return decorator


def get_image_info(image: Image.Image, file_path: Optional[str] = None) -> Dict[str, Any]:
    """Return detailed information about an image (size, format, EXIF).

    Args:
        image: PIL Image object.
        file_path: Optional file path (for file size).

    Returns:
        Dictionary of image information.
    """
    info: Dict[str, Any] = {
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "format": image.format or "N/A",
        "pixels": image.width * image.height,
    }

    if file_path and os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        info["file_size_bytes"] = size_bytes
        info["file_size_kb"] = round(size_bytes / 1024, 1)
        info["file_size_mb"] = round(size_bytes / (1024 * 1024), 2)

    # Read EXIF data
    exif_data: Dict[str, Any] = {}
    try:
        raw_exif = image.getexif()
        if raw_exif:
            for tag_id, value in raw_exif.items():
                tag_name = TAGS.get(tag_id, str(tag_id))
                if isinstance(value, bytes):
                    value = value.decode("utf-8", errors="ignore")
                exif_data[tag_name] = str(value)
    except (AttributeError, Exception):
        pass

    info["exif"] = exif_data
    return info


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between a minimum and maximum.

    Args:
        value: Value to clamp.
        min_val: Minimum value.
        max_val: Maximum value.

    Returns:
        Clamped value.
    """
    return max(min_val, min(value, max_val))
