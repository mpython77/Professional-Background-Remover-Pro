"""UI dialogs — Rotate, Flip, Crop, Compare, Watermark, Export, ImageInfo."""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, Any, Tuple

from PIL import Image, ImageTk

from core.export_manager import EXPORT_PRESETS
from utils.helpers import get_image_info
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RotateDialog:
    """Dialog for rotating an image."""

    def __init__(self, parent: tk.Tk, on_apply: Callable[[int], None]) -> None:
        self.window = tk.Toplevel(parent)
        self.window.title("Rotate Image")
        self.window.geometry("420x220")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.resizable(False, False)

        frame = ttk.Frame(self.window, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="🔄 Rotation Angle:", font=("Segoe UI", 12)).pack(anchor="w")

        self.angle_var = tk.IntVar(value=0)

        slider_frame = ttk.Frame(frame)
        slider_frame.pack(fill="x", pady=10)

        ttk.Scale(
            slider_frame, from_=0, to=360, orient="horizontal", variable=self.angle_var,
        ).pack(side="left", fill="x", expand=True)

        ttk.Label(slider_frame, textvariable=self.angle_var, width=4, font=("Segoe UI", 12, "bold")).pack(
            side="left", padx=10
        )
        ttk.Label(slider_frame, text="°").pack(side="left")

        # Quick buttons
        quick_frame = ttk.Frame(frame)
        quick_frame.pack(fill="x", pady=5)
        for angle in [90, 180, 270]:
            ttk.Button(
                quick_frame, text=f"{angle}°",
                command=lambda a=angle: self.angle_var.set(a),
            ).pack(side="left", padx=3)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(
            btn_frame, text="✅ Apply", style="Accent.TButton",
            command=lambda: self._apply(on_apply),
        ).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side="right")

    def _apply(self, callback: Callable[[int], None]) -> None:
        callback(self.angle_var.get())
        self.window.destroy()


class FlipDialog:
    """Dialog for flipping an image."""

    def __init__(
        self, parent: tk.Tk,
        on_flip_h: Callable,
        on_flip_v: Callable,
    ) -> None:
        self.window = tk.Toplevel(parent)
        self.window.title("Flip Image")
        self.window.geometry("320x180")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.resizable(False, False)

        frame = ttk.Frame(self.window, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="🔀 Flip Direction:", font=("Segoe UI", 12)).pack(anchor="w", pady=(0, 10))

        ttk.Button(
            frame, text="↔️ Flip Horizontal",
            command=lambda: (on_flip_h(), self.window.destroy()),
            style="Accent.TButton",
        ).pack(fill="x", pady=3)

        ttk.Button(
            frame, text="↕️ Flip Vertical",
            command=lambda: (on_flip_v(), self.window.destroy()),
            style="Accent.TButton",
        ).pack(fill="x", pady=3)

        ttk.Button(frame, text="Cancel", command=self.window.destroy).pack(fill="x", pady=(5, 0))


class CropDialog:
    """Interactive image cropping dialog with correct scaling."""

    def __init__(self, parent: tk.Tk, image: Image.Image, on_crop: Callable) -> None:
        self.window = tk.Toplevel(parent)
        self.window.title("Crop Image")
        self.window.geometry("700x550")
        self.window.transient(parent)
        self.window.grab_set()

        self.original_image = image
        self.on_crop = on_crop
        self.crop_rect = [0, 0, 0, 0]
        self.rect_id = None

        frame = ttk.Frame(self.window, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="✂️ Draw a rectangle to crop", style="Subheader.TLabel").pack(anchor="w")

        self.canvas = tk.Canvas(frame, bg="#333333", highlightthickness=1, highlightbackground="#555")
        self.canvas.pack(fill="both", expand=True, pady=5)

        # Fit the image to the canvas
        self.canvas.update_idletasks()
        self._display_image()

        self.canvas.bind("<Button-1>", self._start_crop)
        self.canvas.bind("<B1-Motion>", self._update_crop)
        self.canvas.bind("<ButtonRelease-1>", self._finish_crop)

    def _display_image(self) -> None:
        """Display the image scaled to the canvas size."""
        cw = max(self.canvas.winfo_width(), 600)
        ch = max(self.canvas.winfo_height(), 400)

        img = self.original_image.copy()
        img.thumbnail((cw, ch), Image.LANCZOS)
        self.displayed_img = img
        self.scale_x = self.original_image.width / img.width
        self.scale_y = self.original_image.height / img.height

        self.offset_x = (cw - img.width) // 2
        self.offset_y = (ch - img.height) // 2

        self._photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(self.offset_x, self.offset_y, anchor="nw", image=self._photo)

    def _start_crop(self, event: tk.Event) -> None:
        self.crop_rect[0] = event.x
        self.crop_rect[1] = event.y
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="#ff4444", width=2, dash=(6, 3),
        )

    def _update_crop(self, event: tk.Event) -> None:
        self.crop_rect[2] = event.x
        self.crop_rect[3] = event.y
        if self.rect_id:
            self.canvas.coords(self.rect_id, *self.crop_rect)

    def _finish_crop(self, event: tk.Event) -> None:
        self.crop_rect[2] = event.x
        self.crop_rect[3] = event.y

        # Convert canvas coordinates to image coordinates
        left = int((min(self.crop_rect[0], self.crop_rect[2]) - self.offset_x) * self.scale_x)
        top = int((min(self.crop_rect[1], self.crop_rect[3]) - self.offset_y) * self.scale_y)
        right = int((max(self.crop_rect[0], self.crop_rect[2]) - self.offset_x) * self.scale_x)
        bottom = int((max(self.crop_rect[1], self.crop_rect[3]) - self.offset_y) * self.scale_y)

        if right > left + 5 and bottom > top + 5:
            self.on_crop(left, top, right, bottom)
        self.window.destroy()


class CompareDialog:
    """Dialog for comparing original and processed images side by side."""

    def __init__(
        self, parent: tk.Tk,
        original: Image.Image,
        processed: Image.Image,
    ) -> None:
        self.window = tk.Toplevel(parent)
        self.window.title("Compare — Original vs Processed")
        self.window.geometry("1000x600")
        self.window.transient(parent)

        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Original
        left = ttk.LabelFrame(main_frame, text="🖼️ Original")
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.orig_canvas = tk.Canvas(left, bg="#eeeeee", highlightthickness=0)
        self.orig_canvas.pack(fill="both", expand=True, padx=5, pady=5)

        # Processed
        right = ttk.LabelFrame(main_frame, text="✨ Processed")
        right.pack(side="right", fill="both", expand=True, padx=(5, 0))

        self.proc_canvas = tk.Canvas(right, bg="#eeeeee", highlightthickness=0)
        self.proc_canvas.pack(fill="both", expand=True, padx=5, pady=5)

        self.original = original
        self.processed = processed

        self.window.after(100, self._render)
        self.orig_canvas.bind("<Configure>", lambda e: self._render())

    def _render(self) -> None:
        for canvas, image in [(self.orig_canvas, self.original), (self.proc_canvas, self.processed)]:
            w = max(canvas.winfo_width(), 1)
            h = max(canvas.winfo_height(), 1)

            img = image.copy()
            img.thumbnail((w, h), Image.LANCZOS)

            photo = ImageTk.PhotoImage(img)
            canvas.delete("all")
            canvas.create_image(w // 2, h // 2, image=photo)
            canvas._photo = photo  # Keep reference


class ExportDialog:
    """Dialog for selecting an export preset."""

    def __init__(
        self, parent: tk.Tk,
        on_export: Callable[[str], None],
    ) -> None:
        self.window = tk.Toplevel(parent)
        self.window.title("Export Presets")
        self.window.geometry("400x350")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.resizable(False, False)

        frame = ttk.Frame(self.window, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="📤 Export Preset:", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 10))

        self.selected_preset = tk.StringVar(value="web")

        for key, preset in EXPORT_PRESETS.items():
            rb = ttk.Radiobutton(frame, text=preset["label"], variable=self.selected_preset, value=key)
            rb.pack(anchor="w", padx=10, pady=3)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(15, 0))

        ttk.Button(
            btn_frame, text="✅ Export", style="Accent.TButton",
            command=lambda: self._export(on_export),
        ).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side="right")

    def _export(self, callback: Callable[[str], None]) -> None:
        callback(self.selected_preset.get())
        self.window.destroy()


class WatermarkDialog:
    """Dialog for adding a text watermark."""

    def __init__(
        self, parent: tk.Tk,
        on_apply: Callable[[str, str, int, int], None],
    ) -> None:
        self.window = tk.Toplevel(parent)
        self.window.title("Add Watermark")
        self.window.geometry("420x340")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.resizable(False, False)

        frame = ttk.Frame(self.window, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="💧 Watermark Text:", font=("Segoe UI", 12)).pack(anchor="w")

        self.text_var = tk.StringVar(value="© My Photo")
        ttk.Entry(frame, textvariable=self.text_var, font=("Segoe UI", 11)).pack(fill="x", pady=5)

        ttk.Label(frame, text="Position:").pack(anchor="w", pady=(10, 0))
        self.pos_var = tk.StringVar(value="bottom-right")
        positions = ["top-left", "top-right", "center", "bottom-left", "bottom-right"]
        pos_frame = ttk.Frame(frame)
        pos_frame.pack(fill="x", pady=3)
        for pos in positions:
            ttk.Radiobutton(pos_frame, text=pos.replace("-", " ").title(), variable=self.pos_var, value=pos).pack(
                anchor="w", padx=10
            )

        ttk.Label(frame, text="Opacity:").pack(anchor="w", pady=(10, 0))
        self.opacity_var = tk.IntVar(value=128)
        ttk.Scale(frame, from_=10, to=255, orient="horizontal", variable=self.opacity_var).pack(fill="x", pady=3)

        ttk.Label(frame, text="Font Size:").pack(anchor="w", pady=(5, 0))
        self.size_var = tk.IntVar(value=24)
        ttk.Scale(frame, from_=10, to=100, orient="horizontal", variable=self.size_var).pack(fill="x", pady=3)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(
            btn_frame, text="✅ Apply", style="Accent.TButton",
            command=lambda: self._apply(on_apply),
        ).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side="right")

    def _apply(self, callback: Callable) -> None:
        text = self.text_var.get().strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter watermark text.")
            return
        callback(text, self.pos_var.get(), self.opacity_var.get(), self.size_var.get())
        self.window.destroy()


class ImageInfoDialog:
    """Dialog displaying image information — EXIF, dimensions, format."""

    def __init__(self, parent: tk.Tk, image: Image.Image, file_path: Optional[str] = None) -> None:
        self.window = tk.Toplevel(parent)
        self.window.title("Image Information")
        self.window.geometry("450x500")
        self.window.transient(parent)
        self.window.resizable(False, True)

        frame = ttk.Frame(self.window, padding=15)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="📊 Image Information", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 10))

        info = get_image_info(image, file_path)

        # Basic information
        basic_frame = ttk.LabelFrame(frame, text="Basic")
        basic_frame.pack(fill="x", pady=5)

        items = [
            ("Width", f"{info['width']} px"),
            ("Height", f"{info['height']} px"),
            ("Pixels", f"{info['pixels']:,}"),
            ("Mode", info["mode"]),
            ("Format", info.get("format", "N/A")),
        ]
        if "file_size_kb" in info:
            items.append(("File Size", f"{info['file_size_kb']} KB ({info.get('file_size_mb', 0)} MB)"))

        for label, value in items:
            row = ttk.Frame(basic_frame)
            row.pack(fill="x", padx=10, pady=1)
            ttk.Label(row, text=f"{label}:", width=12, font=("Segoe UI", 9, "bold")).pack(side="left")
            ttk.Label(row, text=value, font=("Segoe UI", 9)).pack(side="left")

        # EXIF data
        exif = info.get("exif", {})
        if exif:
            exif_frame = ttk.LabelFrame(frame, text="EXIF Data")
            exif_frame.pack(fill="both", expand=True, pady=5)

            # Scrollable text
            text_widget = tk.Text(exif_frame, height=10, wrap="word", font=("Consolas", 9))
            scrollbar = ttk.Scrollbar(exif_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)

            scrollbar.pack(side="right", fill="y")
            text_widget.pack(fill="both", expand=True, padx=5, pady=5)

            for key, val in exif.items():
                text_widget.insert("end", f"{key}: {val}\n")
            text_widget.config(state="disabled")
        else:
            ttk.Label(frame, text="No EXIF data available", style="Status.TLabel").pack(pady=10)

        ttk.Button(frame, text="Close", command=self.window.destroy).pack(pady=(10, 0))
