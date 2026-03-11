"""Configuration manager — save, load, and validate settings."""

import os
import json
from typing import Any, Dict, List, Optional, Tuple

from utils.logger import setup_logger

logger = setup_logger(__name__)

# Default settings
DEFAULT_CONFIG: Dict[str, Any] = {
    "output_directory": os.path.join(os.path.expanduser("~"), "Pictures"),
    "bg_color": [240, 240, 240],
    "format": "png",
    "quality": 90,
    "theme": "light",
    "recent_files": [],
    "max_recent_files": 10,
    "undo_limit": 20,
    "auto_save": False,
    "default_zoom": 1.0,
    "last_export_preset": "web",
    "window_geometry": None,
}


class ConfigManager:
    """JSON-based configuration manager.

    Reads and writes settings to disk. Validates values against
    their expected types and ranges.

    Attributes:
        config_path: Full path to the configuration file.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = config_path or os.path.join(
            os.path.expanduser("~"), ".bgremover_config.json"
        )
        self._config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load()

    def load(self) -> None:
        """Load the configuration from disk."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                # Merge with defaults (preserves new keys)
                for key, default_val in DEFAULT_CONFIG.items():
                    if key in saved:
                        self._config[key] = saved[key]
                    else:
                        self._config[key] = default_val
                self._validate()
                logger.info("Configuration loaded: %s", self.config_path)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load configuration: %s. Using defaults.", e)
            self._config = DEFAULT_CONFIG.copy()

    def save(self) -> None:
        """Save the configuration to disk."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info("Configuration saved: %s", self.config_path)
        except OSError as e:
            logger.error("Failed to save configuration: %s", e)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value.

        Args:
            key: Setting name.
            default: Value to return if the key is not found.

        Returns:
            The setting value.
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value.

        Args:
            key: Setting name.
            value: New value.
        """
        self._config[key] = value

    def get_bg_color(self) -> Tuple[int, int, int]:
        """Return the background color as an RGB tuple."""
        color = self._config.get("bg_color", [240, 240, 240])
        return tuple(color)  # type: ignore[return-value]

    def set_bg_color(self, color: Tuple[int, int, int]) -> None:
        """Set the background color."""
        self._config["bg_color"] = list(color)

    # --- Recent Files ---

    def get_recent_files(self) -> List[str]:
        """Return the list of recently opened files."""
        files = self._config.get("recent_files", [])
        # Only return files that still exist on disk
        return [f for f in files if os.path.exists(f)]

    def add_recent_file(self, file_path: str) -> None:
        """Add a file to the recent files list.

        Args:
            file_path: Path to the file.
        """
        files = self._config.get("recent_files", [])
        # Remove duplicate
        if file_path in files:
            files.remove(file_path)
        files.insert(0, file_path)
        # Enforce limit
        max_files = self._config.get("max_recent_files", 10)
        self._config["recent_files"] = files[:max_files]

    def clear_recent_files(self) -> None:
        """Clear the recent files list."""
        self._config["recent_files"] = []

    # --- Validation ---

    def _validate(self) -> None:
        """Validate and correct configuration values."""
        # Format
        if self._config.get("format") not in ("png", "jpeg", "webp", "bmp"):
            self._config["format"] = "png"

        # Quality
        quality = self._config.get("quality", 90)
        if not isinstance(quality, int) or quality < 1 or quality > 100:
            self._config["quality"] = 90

        # Theme
        if self._config.get("theme") not in ("light", "dark"):
            self._config["theme"] = "light"

        # Output directory
        out_dir = self._config.get("output_directory", "")
        if not out_dir or not os.path.exists(out_dir):
            self._config["output_directory"] = os.path.join(
                os.path.expanduser("~"), "Pictures"
            )

        # Undo limit
        undo_limit = self._config.get("undo_limit", 20)
        if not isinstance(undo_limit, int) or undo_limit < 1:
            self._config["undo_limit"] = 20

    def to_dict(self) -> Dict[str, Any]:
        """Return all settings as a dictionary."""
        return self._config.copy()
