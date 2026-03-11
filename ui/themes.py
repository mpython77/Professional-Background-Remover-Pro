"""Theme manager — Dark/Light mode, colors, styles."""

from typing import Dict, Any
import tkinter as tk
from tkinter import ttk

from utils.logger import setup_logger

logger = setup_logger(__name__)


# Color palettes
THEMES: Dict[str, Dict[str, str]] = {
    "light": {
        "primary": "#4361ee",
        "primary_hover": "#3a56d4",
        "secondary": "#3a0ca3",
        "bg": "#f8f9fa",
        "bg_alt": "#ffffff",
        "surface": "#ffffff",
        "light": "#e9ecef",
        "dark": "#495057",
        "success": "#06d6a0",
        "success_hover": "#05b888",
        "warning": "#ffd166",
        "danger": "#ef476f",
        "danger_hover": "#d63d63",
        "text": "#212529",
        "text_secondary": "#6c757d",
        "text_light": "#adb5bd",
        "border": "#dee2e6",
        "canvas_bg": "#e9ecef",
        "checkerboard_1": "#EEEEEE",
        "checkerboard_2": "#CCCCCC",
        "accent": "#7209b7",
        "info": "#4cc9f0",
    },
    "dark": {
        "primary": "#5a7cff",
        "primary_hover": "#4a6aee",
        "secondary": "#7c4dff",
        "bg": "#1a1a2e",
        "bg_alt": "#16213e",
        "surface": "#0f3460",
        "light": "#2a2a4a",
        "dark": "#e0e0e0",
        "success": "#00e676",
        "success_hover": "#00c965",
        "warning": "#ffab40",
        "danger": "#ff5252",
        "danger_hover": "#ff3838",
        "text": "#e8e8e8",
        "text_secondary": "#a0a0b8",
        "text_light": "#6c6c8a",
        "border": "#2a2a4a",
        "canvas_bg": "#12122a",
        "checkerboard_1": "#252540",
        "checkerboard_2": "#1e1e35",
        "accent": "#b388ff",
        "info": "#64b5f6",
    },
}


class ThemeManager:
    """Theme manager — handles dark/light mode switching and styling.

    Attributes:
        current_theme: Current theme name ('light' or 'dark').
        colors: Current theme color dictionary.
    """

    def __init__(self, root: tk.Tk, initial_theme: str = "light") -> None:
        self.root = root
        self.current_theme = initial_theme if initial_theme in THEMES else "light"
        self.colors = THEMES[self.current_theme].copy()
        self.style = ttk.Style()

        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.apply_theme()

    def toggle_theme(self) -> str:
        """Toggle between light and dark themes.

        Returns:
            The new theme name.
        """
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.colors = THEMES[self.current_theme].copy()
        self.apply_theme()
        logger.info("Theme changed to: %s", self.current_theme)
        return self.current_theme

    def set_theme(self, theme_name: str) -> None:
        """Set a specific theme.

        Args:
            theme_name: Theme name ('light' or 'dark').
        """
        if theme_name not in THEMES:
            logger.warning("Unknown theme: %s", theme_name)
            return
        self.current_theme = theme_name
        self.colors = THEMES[theme_name].copy()
        self.apply_theme()

    def apply_theme(self) -> None:
        """Apply the theme to all components."""
        c = self.colors

        self.root.configure(bg=c["bg"])

        # Frame styles
        self.style.configure("TFrame", background=c["bg"])
        self.style.configure("Surface.TFrame", background=c["surface"])
        self.style.configure("Alt.TFrame", background=c["bg_alt"])

        # Button styles
        self.style.configure(
            "TButton",
            font=("Segoe UI", 10),
            background=c["light"],
            foreground=c["text"],
        )
        self.style.map("TButton",
            background=[("active", c["border"]), ("disabled", c["light"])],
        )

        self.style.configure(
            "Accent.TButton",
            font=("Segoe UI", 11, "bold"),
            background=c["primary"],
            foreground="#ffffff",
        )
        self.style.map("Accent.TButton",
            background=[("active", c["primary_hover"]), ("disabled", c["light"])],
        )

        self.style.configure(
            "Success.TButton",
            font=("Segoe UI", 10),
            background=c["success"],
            foreground="#ffffff",
        )
        self.style.map("Success.TButton",
            background=[("active", c["success_hover"])],
        )

        self.style.configure(
            "Danger.TButton",
            font=("Segoe UI", 10),
            background=c["danger"],
            foreground="#ffffff",
        )
        self.style.map("Danger.TButton",
            background=[("active", c["danger_hover"])],
        )

        # Label styles
        self.style.configure(
            "TLabel",
            font=("Segoe UI", 10),
            background=c["bg"],
            foreground=c["text"],
        )
        self.style.configure(
            "Header.TLabel",
            font=("Segoe UI", 20, "bold"),
            background=c["bg"],
            foreground=c["secondary"],
        )
        self.style.configure(
            "Subheader.TLabel",
            font=("Segoe UI", 13),
            background=c["bg"],
            foreground=c["primary"],
        )
        self.style.configure(
            "Status.TLabel",
            font=("Segoe UI", 9),
            background=c["bg"],
            foreground=c["text_secondary"],
        )
        self.style.configure(
            "Info.TLabel",
            font=("Segoe UI", 9),
            background=c["bg"],
            foreground=c["info"],
        )

        # LabelFrame
        self.style.configure(
            "TLabelframe",
            background=c["bg"],
            foreground=c["text"],
        )
        self.style.configure(
            "TLabelframe.Label",
            font=("Segoe UI", 10, "bold"),
            background=c["bg"],
            foreground=c["primary"],
        )

        # Notebook
        self.style.configure(
            "TNotebook",
            background=c["bg"],
        )
        self.style.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 9),
            background=c["light"],
            foreground=c["text"],
            padding=[10, 4],
        )
        self.style.map("TNotebook.Tab",
            background=[("selected", c["bg_alt"])],
            foreground=[("selected", c["primary"])],
        )

        # Scale
        self.style.configure(
            "TScale",
            background=c["bg"],
            troughcolor=c["light"],
        )

        # Progressbar
        self.style.configure(
            "TProgressbar",
            background=c["primary"],
            troughcolor=c["light"],
        )

        # Radiobutton / Checkbutton
        self.style.configure(
            "TRadiobutton",
            background=c["bg"],
            foreground=c["text"],
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "TCheckbutton",
            background=c["bg"],
            foreground=c["text"],
            font=("Segoe UI", 10),
        )

    def get_color(self, name: str) -> str:
        """Get a color value by name.

        Args:
            name: Color name.

        Returns:
            Hex color value.
        """
        return self.colors.get(name, "#000000")
