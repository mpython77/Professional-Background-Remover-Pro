"""UI panels — InputPanel, SettingsPanel, ActionsPanel, ImageDisplay, FilterPanel."""

import os
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ui.themes import ThemeManager

from utils.logger import setup_logger

logger = setup_logger(__name__)


class InputPanel(ttk.LabelFrame):
    """Image selection and output directory panel.

    Attributes:
        input_path: Selected input file path.
        output_directory: Output directory path.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_select_image: Callable,
        on_paste_clipboard: Callable,
        on_select_output: Callable,
        on_open_output: Callable,
        output_directory: tk.StringVar,
        input_path: tk.StringVar,
        **kwargs,
    ) -> None:
        super().__init__(parent, text="📁 Image Selection", **kwargs)

        self.input_path = input_path
        self.output_directory = output_directory

        # Image selection buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Button(btn_frame, text="📂 Open Image", command=on_select_image).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(btn_frame, text="📋 Clipboard", command=on_paste_clipboard).pack(
            side="left"
        )

        # Drag & Drop label
        self.dnd_label = ttk.Label(
            self,
            text="🖱️ Drag & Drop image here",
            style="Info.TLabel",
            anchor="center",
        )
        self.dnd_label.pack(fill="x", padx=10, pady=2)

        # Input file name display
        ttk.Label(self, textvariable=self.input_path, wraplength=220).pack(
            fill="x", padx=10, pady=(0, 5)
        )

        # Output directory section
        out_frame = ttk.LabelFrame(self, text="Save Location")
        out_frame.pack(fill="x", padx=10, pady=(0, 10))

        btn_frame2 = ttk.Frame(out_frame)
        btn_frame2.pack(fill="x", padx=5, pady=5)

        ttk.Button(btn_frame2, text="📁 Browse", command=on_select_output).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(btn_frame2, text="📂 Open", command=on_open_output).pack(side="left")

        ttk.Label(out_frame, textvariable=self.output_directory, wraplength=220).pack(
            fill="x", padx=5, pady=(0, 5)
        )


class SettingsPanel(ttk.LabelFrame):
    """Settings panel — format, quality, theme."""

    def __init__(
        self,
        parent: tk.Widget,
        format_var: tk.StringVar,
        quality_var: tk.IntVar,
        on_theme_toggle: Callable,
        **kwargs,
    ) -> None:
        super().__init__(parent, text="⚙️ Settings", **kwargs)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        # --- Basic Tab ---
        basic_tab = ttk.Frame(notebook)
        notebook.add(basic_tab, text="Basic")

        # Format
        fmt_frame = ttk.Frame(basic_tab)
        fmt_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(fmt_frame, text="Format:").pack(anchor="w")

        fmt_radio = ttk.Frame(fmt_frame)
        fmt_radio.pack(fill="x", pady=2)
        ttk.Radiobutton(fmt_radio, text="PNG", variable=format_var, value="png").pack(
            side="left", padx=(0, 8)
        )
        ttk.Radiobutton(fmt_radio, text="JPEG", variable=format_var, value="jpeg").pack(
            side="left", padx=(0, 8)
        )
        ttk.Radiobutton(fmt_radio, text="WEBP", variable=format_var, value="webp").pack(
            side="left"
        )

        # Quality
        q_frame = ttk.Frame(basic_tab)
        q_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(q_frame, text="Quality:").pack(anchor="w")

        q_slider = ttk.Frame(q_frame)
        q_slider.pack(fill="x", pady=2)
        ttk.Scale(q_slider, from_=1, to=100, orient="horizontal", variable=quality_var).pack(
            side="left", fill="x", expand=True
        )
        ttk.Label(q_slider, textvariable=quality_var, width=3).pack(side="left", padx=5)
        ttk.Label(q_slider, text="%").pack(side="left")

        # Theme toggle
        ttk.Button(basic_tab, text="🌓 Toggle Dark/Light", command=on_theme_toggle).pack(
            fill="x", padx=5, pady=8
        )


class FilterPanel(ttk.LabelFrame):
    """Filter panel — brightness, contrast, saturation, sharpness."""

    def __init__(
        self,
        parent: tk.Widget,
        brightness_var: tk.DoubleVar,
        contrast_var: tk.DoubleVar,
        saturation_var: tk.DoubleVar,
        sharpness_var: tk.DoubleVar,
        on_apply_filters: Callable,
        on_reset_filters: Callable,
        **kwargs,
    ) -> None:
        super().__init__(parent, text="🎨 Filters", **kwargs)

        sliders = [
            ("☀️ Brightness", brightness_var, 0.0, 3.0),
            ("🔲 Contrast", contrast_var, 0.0, 3.0),
            ("🎭 Saturation", saturation_var, 0.0, 3.0),
            ("🔍 Sharpness", sharpness_var, 0.0, 3.0),
        ]

        for label_text, var, from_val, to_val in sliders:
            frame = ttk.Frame(self)
            frame.pack(fill="x", padx=8, pady=3)
            ttk.Label(frame, text=label_text, width=14).pack(side="left")
            ttk.Scale(frame, from_=from_val, to=to_val, orient="horizontal", variable=var).pack(
                side="left", fill="x", expand=True, padx=(5, 5)
            )
            lbl = ttk.Label(frame, text="1.0", width=4)
            lbl.pack(side="left")
            var.trace_add("write", lambda *_, v=var, l=lbl: l.config(text=f"{v.get():.1f}"))

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=8, pady=5)
        ttk.Button(btn_frame, text="✅ Apply", command=on_apply_filters, style="Accent.TButton").pack(
            side="left", fill="x", expand=True, padx=(0, 3)
        )
        ttk.Button(btn_frame, text="🔄 Reset", command=on_reset_filters).pack(
            side="left", fill="x", expand=True, padx=(3, 0)
        )


class ActionsPanel(ttk.LabelFrame):
    """Actions panel — process, save, undo buttons."""

    def __init__(
        self,
        parent: tk.Widget,
        on_process: Callable,
        on_save: Callable,
        on_undo: Callable,
        on_batch: Callable,
        **kwargs,
    ) -> None:
        super().__init__(parent, text="🚀 Actions", **kwargs)

        frame = ttk.Frame(self)
        frame.pack(fill="x", padx=8, pady=8)

        self.process_btn = ttk.Button(
            frame, text="✨ Remove Background", command=on_process,
            style="Accent.TButton", state="disabled",
        )
        self.process_btn.pack(fill="x", pady=(0, 4))

        self.save_btn = ttk.Button(
            frame, text="💾 Save Image", command=on_save,
            style="Success.TButton", state="disabled",
        )
        self.save_btn.pack(fill="x", pady=(0, 4))

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill="x")

        self.undo_btn = ttk.Button(btn_row, text="↩️ Undo", command=on_undo)
        self.undo_btn.pack(side="left", fill="x", expand=True, padx=(0, 3))

        ttk.Button(btn_row, text="📦 Batch", command=on_batch).pack(
            side="left", fill="x", expand=True, padx=(3, 0)
        )


class ImageDisplay(ttk.LabelFrame):
    """Image display panel — canvas, zoom, and information."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str = "Image",
        canvas_bg: str = "#e9ecef",
        **kwargs,
    ) -> None:
        super().__init__(parent, text=title, **kwargs)

        self.canvas = tk.Canvas(self, bg=canvas_bg, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)

        self.info_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.info_var, style="Status.TLabel", anchor="center").pack(
            fill="x", padx=5, pady=(0, 3)
        )

        self.progress_bar = ttk.Progressbar(self, mode="determinate")
        self._progress_visible = False

    @property
    def photo_image(self) -> Optional[tk.PhotoImage]:
        """Return the stored PhotoImage reference."""
        return getattr(self, "_photo", None)

    @photo_image.setter
    def photo_image(self, value) -> None:
        self._photo = value

    def show_progress(self) -> None:
        """Show the progress bar."""
        if not self._progress_visible:
            self.progress_bar.pack(fill="x", padx=5, pady=(0, 5))
            self._progress_visible = True

    def hide_progress(self) -> None:
        """Hide the progress bar."""
        if self._progress_visible:
            self.progress_bar.pack_forget()
            self._progress_visible = False

    def set_progress(self, value: float) -> None:
        """Set the progress bar value (0-100)."""
        self.progress_bar["value"] = value

    def update_canvas_bg(self, color: str) -> None:
        """Update the canvas background color."""
        self.canvas.configure(bg=color)

    def clear(self) -> None:
        """Clear the canvas."""
        self.canvas.delete("all")
        self.info_var.set("")
