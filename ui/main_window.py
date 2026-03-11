"""Main window — the MainWindow class that integrates all components."""

import os
import time
import platform
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from typing import Optional

from PIL import Image, ImageTk

from core.image_processor import ImageProcessor
from core.image_editor import ImageEditor
from core.export_manager import ExportManager
from config.config_manager import ConfigManager
from ui.themes import ThemeManager
from ui.panels import InputPanel, SettingsPanel, FilterPanel, ActionsPanel, ImageDisplay
from ui.history_panel import HistoryPanel, ShortcutsPanel
from ui.dialogs import (
    RotateDialog, FlipDialog, CropDialog, CompareDialog,
    ExportDialog, WatermarkDialog, ImageInfoDialog,
)
from utils.helpers import open_file, get_image_info
from utils.logger import setup_logger

logger = setup_logger(__name__)

# ImageGrab (clipboard support)
try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None


class MainWindow:
    """Main application window — v2.1.

    Integrates all modules: ImageProcessor, ImageEditor,
    ExportManager, ConfigManager, ThemeManager.

    Attributes:
        root: Tkinter root window.
    """

    VERSION = "2.1.0"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Professional Background Remover Pro")
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Core components
        self.config = ConfigManager()
        self.processor = ImageProcessor()
        self.editor = ImageEditor(undo_limit=self.config.get("undo_limit", 20))
        self.exporter = ExportManager()

        # Tkinter variables
        self.input_path = tk.StringVar()
        self._full_input_path: Optional[str] = None
        self.output_directory = tk.StringVar(value=self.config.get("output_directory"))
        self.status_text = tk.StringVar(value="Welcome! Open an image to start.")
        self.format_var = tk.StringVar(value=self.config.get("format", "png"))
        self.quality_var = tk.IntVar(value=self.config.get("quality", 90))
        self.zoom_factor = 1.0

        # Filter variables
        self.brightness_var = tk.DoubleVar(value=1.0)
        self.contrast_var = tk.DoubleVar(value=1.0)
        self.saturation_var = tk.DoubleVar(value=1.0)
        self.sharpness_var = tk.DoubleVar(value=1.0)

        # Image states
        self.output_image: Optional[Image.Image] = None
        self._displayed_original = None
        self._displayed_processed = None
        self._resize_timer: Optional[str] = None
        self._checkerboard_cache: Optional[ImageTk.PhotoImage] = None
        self._checkerboard_size: tuple = (0, 0)

        # Theme and UI
        self._setup_window()
        self.theme = ThemeManager(self.root, self.config.get("theme", "light"))
        self._create_ui()
        self._setup_bindings()
        self._setup_dnd()

        logger.info("MainWindow started (v%s)", self.VERSION)

    def _setup_window(self) -> None:
        """Set up the window size and position."""
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = int(sw * 0.85)
        h = int(sh * 0.85)
        x = (sw - w) // 2
        y = (sh - h) // 2

        saved_geom = self.config.get("window_geometry")
        if saved_geom:
            self.root.geometry(saved_geom)
        else:
            self.root.geometry(f"{w}x{h}+{x}+{y}")

        self.root.minsize(1100, 700)

        try:
            if platform.system() == "Windows":
                icon_path = os.path.join(os.path.dirname(__file__), "..", "icon.ico")
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
        except (tk.TclError, OSError):
            pass

    def _create_ui(self) -> None:
        """Create the UI components."""
        self.container = ttk.Frame(self.root)
        self.container.pack(fill="both", expand=True, padx=15, pady=15)

        self._create_menu()
        self._create_header()
        self._create_main_area()
        self._create_status_bar()

    def _create_menu(self) -> None:
        """Create the professional menu system."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # ===== File =====
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Image     Ctrl+O", command=self._select_image)
        file_menu.add_command(label="Select Output Directory", command=self._select_output_dir)
        file_menu.add_separator()

        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        self._update_recent_menu()

        file_menu.add_separator()
        file_menu.add_command(label="Save             Ctrl+S", command=self._save_image)
        file_menu.add_command(label="Save As...", command=self._save_as)
        file_menu.add_command(label="Export with Preset...", command=self._show_export_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)

        # ===== Edit =====
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo              Ctrl+Z", command=self._undo)
        edit_menu.add_command(label="Redo              Ctrl+Y", command=self._redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Remove Background       Ctrl+P", command=self._process_image)
        edit_menu.add_command(label="Cancel Processing       Esc", command=self._cancel_processing)
        edit_menu.add_separator()
        edit_menu.add_command(label="Crop Image...", command=self._show_crop_dialog)
        edit_menu.add_command(label="Rotate Image...", command=self._show_rotate_dialog)
        edit_menu.add_command(label="Flip Image...", command=self._show_flip_dialog)
        edit_menu.add_separator()
        edit_menu.add_command(label="Add Watermark...", command=self._show_watermark_dialog)
        edit_menu.add_command(label="Select Background Color...", command=self._select_bg_color)

        # ===== Filters =====
        filter_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Filters", menu=filter_menu)
        filter_menu.add_command(label="Blur", command=self._apply_blur)
        filter_menu.add_command(label="Sharpen", command=self._apply_sharpen)
        filter_menu.add_command(label="Edge Enhance", command=self._apply_edge_enhance)
        filter_menu.add_command(label="Emboss", command=self._apply_emboss)
        filter_menu.add_separator()
        filter_menu.add_command(label="🎨 Grayscale", command=self._apply_grayscale)
        filter_menu.add_command(label="🔄 Invert Colors", command=self._apply_invert)
        filter_menu.add_command(label="✨ Auto Enhance", command=self._apply_auto_enhance)

        # ===== View =====
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In          Ctrl++", command=lambda: self._zoom(1.2))
        view_menu.add_command(label="Zoom Out         Ctrl+-", command=lambda: self._zoom(0.8))
        view_menu.add_command(label="Reset Zoom       Ctrl+0", command=lambda: self._zoom(1.0, reset=True))
        view_menu.add_separator()
        view_menu.add_command(label="Compare Mode", command=self._show_compare_dialog)
        view_menu.add_command(label="Image Info...", command=self._show_image_info)

        # ===== Batch =====
        batch_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Batch", menu=batch_menu)
        batch_menu.add_command(label="Process Multiple Images...", command=self._batch_process)

    def _create_header(self) -> None:
        """Create the header bar."""
        header = ttk.Frame(self.container)
        header.pack(fill="x", pady=(0, 12))

        ttk.Label(header, text="🖼️", font=("Segoe UI", 22)).pack(side="left", padx=(0, 8))
        ttk.Label(header, text="Professional Background Remover Pro", style="Header.TLabel").pack(side="left")

        right_frame = ttk.Frame(header)
        right_frame.pack(side="right")

        ttk.Button(right_frame, text="🌓", width=3, command=self._toggle_theme).pack(side="right", padx=3)
        ttk.Button(right_frame, text="❓", width=3, command=self._show_help).pack(side="right", padx=3)

    def _create_main_area(self) -> None:
        """Create the main work area — 3 sections: left panel, images, right panel."""
        main = ttk.Frame(self.container)
        main.pack(fill="both", expand=True, pady=5)

        # --- Left panel (280px) ---
        left = ttk.Frame(main, width=280)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        # Scrollable canvas for the left panel
        left_canvas = tk.Canvas(left, highlightthickness=0)
        left_scrollbar = ttk.Scrollbar(left, orient="vertical", command=left_canvas.yview)
        left_scrollable = ttk.Frame(left_canvas)

        left_scrollable.bind("<Configure>", lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all")))
        left_canvas.create_window((0, 0), window=left_scrollable, anchor="nw", width=268)
        left_canvas.configure(yscrollcommand=left_scrollbar.set)

        left_canvas.pack(side="left", fill="both", expand=True)
        left_scrollbar.pack(side="right", fill="y")

        # Mousewheel scroll
        def _on_mousewheel(event):
            left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        left_canvas.bind_all("<MouseWheel>", _on_mousewheel, add="+")

        self.input_panel = InputPanel(
            left_scrollable,
            on_select_image=self._select_image,
            on_paste_clipboard=self._paste_clipboard,
            on_select_output=self._select_output_dir,
            on_open_output=lambda: open_file(self.output_directory.get()),
            output_directory=self.output_directory,
            input_path=self.input_path,
        )
        self.input_panel.pack(fill="x", pady=(0, 6))

        self.settings_panel = SettingsPanel(
            left_scrollable,
            format_var=self.format_var,
            quality_var=self.quality_var,
            on_theme_toggle=self._toggle_theme,
        )
        self.settings_panel.pack(fill="x", pady=(0, 6))

        self.filter_panel = FilterPanel(
            left_scrollable,
            brightness_var=self.brightness_var,
            contrast_var=self.contrast_var,
            saturation_var=self.saturation_var,
            sharpness_var=self.sharpness_var,
            on_apply_filters=self._apply_filters,
            on_reset_filters=self._reset_filters,
        )
        self.filter_panel.pack(fill="x", pady=(0, 6))

        self.actions_panel = ActionsPanel(
            left_scrollable,
            on_process=self._process_image,
            on_save=self._save_image,
            on_undo=self._undo,
            on_batch=self._batch_process,
        )
        self.actions_panel.pack(fill="x", pady=(0, 6))

        self.history_panel = HistoryPanel(
            left_scrollable,
            on_undo=self._undo,
            on_redo=self._redo,
        )
        self.history_panel.pack(fill="x", pady=(0, 6))

        self.shortcuts_panel = ShortcutsPanel(left_scrollable)
        self.shortcuts_panel.pack(fill="x")

        # --- Center (images) ---
        center = ttk.Frame(main)
        center.pack(side="left", fill="both", expand=True)

        self.original_display = ImageDisplay(
            center, title="🖼️ Original Image",
            canvas_bg=self.theme.get_color("canvas_bg"),
        )
        self.original_display.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.processed_display = ImageDisplay(
            center, title="✨ Processed Image",
            canvas_bg=self.theme.get_color("canvas_bg"),
        )
        self.processed_display.pack(side="right", fill="both", expand=True, padx=(5, 0))

    def _create_status_bar(self) -> None:
        """Create the enhanced status bar — time, size, zoom."""
        status = ttk.Frame(self.container)
        status.pack(fill="x", pady=(10, 0))

        ttk.Label(status, textvariable=self.status_text, style="Status.TLabel").pack(side="left")

        self.time_label = ttk.Label(status, text="", style="Status.TLabel")
        self.time_label.pack(side="right", padx=10)

        self.zoom_label = ttk.Label(status, text="Zoom: 1.0x", style="Status.TLabel")
        self.zoom_label.pack(side="right", padx=10)

        self.size_label = ttk.Label(status, text="", style="Status.TLabel")
        self.size_label.pack(side="right", padx=10)

        ttk.Label(status, text=f"v{self.VERSION}", style="Status.TLabel").pack(side="right")

    def _setup_bindings(self) -> None:
        """Set up keyboard shortcuts."""
        self.root.bind("<Control-o>", lambda e: self._select_image())
        self.root.bind("<Control-s>", lambda e: self._save_image())
        self.root.bind("<Control-p>", lambda e: self._process_image())
        self.root.bind("<Control-z>", lambda e: self._undo())
        self.root.bind("<Control-y>", lambda e: self._redo())
        self.root.bind("<Control-plus>", lambda e: self._zoom(1.2))
        self.root.bind("<Control-minus>", lambda e: self._zoom(0.8))
        self.root.bind("<Control-0>", lambda e: self._zoom(1.0, reset=True))
        self.root.bind("<Escape>", lambda e: self._cancel_processing())
        self.root.bind("<Configure>", self._on_resize)

    def _setup_dnd(self) -> None:
        """Set up Drag & Drop support."""
        try:
            self.root.drop_target_register("DND_Files")  # type: ignore[attr-defined]
            self.root.dnd_bind("<<Drop>>", self._on_drop)  # type: ignore[attr-defined]
        except (AttributeError, tk.TclError):
            pass

    def _on_drop(self, event) -> None:
        try:
            file_path = event.data.strip("{}")
            if os.path.isfile(file_path):
                self._load_image(file_path)
        except (AttributeError, Exception) as e:
            logger.error("Drag & drop error: %s", e)

    # ==================== IMAGE OPERATIONS ====================

    def _select_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif *.webp"),
                ("All files", "*.*"),
            ],
            initialdir=os.path.expanduser("~"),
        )
        if file_path:
            self._load_image(file_path)

    def _load_image(self, file_path: str) -> None:
        try:
            image = Image.open(file_path)
            self.editor.image = image
            self.output_image = None
            self._full_input_path = file_path
            self.input_path.set(os.path.basename(file_path))

            self.config.add_recent_file(file_path)
            self._update_recent_menu()

            self._display_original()
            self.processed_display.clear()
            self.actions_panel.process_btn.config(state="normal")
            self.actions_panel.save_btn.config(state="disabled")

            info = get_image_info(image, file_path)
            self.original_display.info_var.set(
                f"{info['width']}×{info['height']} • {info['mode']} • {info.get('file_size_kb', '?')} KB"
            )
            self.processed_display.info_var.set("")
            self.size_label.config(text=f"Size: {info.get('file_size_kb', '?')} KB")
            self.time_label.config(text="")
            self.status_text.set(f"Image loaded: {os.path.basename(file_path)}")
            self._update_history_panel()
            logger.info("Image loaded: %s", file_path)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{e}")
            logger.error("Failed to load image: %s", e)

    def _paste_clipboard(self) -> None:
        if ImageGrab is None:
            messagebox.showinfo("Info", "Clipboard support is not available on this system.")
            return
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                self.editor.image = img
                self.output_image = None
                self._full_input_path = None
                self.input_path.set("From Clipboard")
                self._display_original()
                self.processed_display.clear()
                self.actions_panel.process_btn.config(state="normal")
                self.actions_panel.save_btn.config(state="disabled")
                self.original_display.info_var.set(f"{img.width}×{img.height} • {img.mode}")
                self.status_text.set("Image loaded from clipboard")
                self._update_history_panel()
            else:
                messagebox.showinfo("Info", "No image found in clipboard.")
        except Exception as e:
            messagebox.showerror("Error", f"Clipboard error:\n{e}")

    def _process_image(self) -> None:
        if self.editor.image is None or self.processor.is_processing:
            return

        self.processed_display.show_progress()
        self.status_text.set("Processing... please wait (Esc to cancel)")

        def on_progress(value: float) -> None:
            self.root.after(0, lambda: self.processed_display.set_progress(value * 100))

        def on_complete(result: Optional[Image.Image]) -> None:
            self.output_image = result
            self.root.after(0, self._after_processing)

        def on_error(msg: str) -> None:
            self.root.after(0, lambda: self.processed_display.hide_progress())
            self.root.after(0, lambda: self.status_text.set(f"❌ {msg}"))

        self.processor.remove_background_async(
            self.editor.image, on_complete, on_progress, on_error,
        )

    def _cancel_processing(self) -> None:
        """Cancel the current processing job."""
        if self.processor.is_processing:
            self.processor.cancel()
            self.status_text.set("⏹️ Processing cancelled")

    def _after_processing(self) -> None:
        self.processed_display.hide_progress()
        if self.output_image:
            self._display_processed()
            self.actions_panel.save_btn.config(state="normal")
            info = get_image_info(self.output_image)
            self.processed_display.info_var.set(
                f"{info['width']}×{info['height']} • {info['mode']}"
            )
            elapsed = self.processor.last_processing_time
            self.time_label.config(text=f"⏱ {elapsed:.1f}s")
            self.status_text.set(f"✅ Background removed! ({elapsed:.1f}s)")
        else:
            self.status_text.set("❌ Processing failed")

    # ==================== DISPLAY ====================

    def _display_original(self) -> None:
        if self.editor.image is None:
            return
        canvas = self.original_display.canvas
        cw = max(canvas.winfo_width(), 1)
        ch = max(canvas.winfo_height(), 1)

        img = self.editor.image.copy()
        w = int(img.width * self.zoom_factor)
        h = int(img.height * self.zoom_factor)

        if w > cw or h > ch:
            img.thumbnail((cw, ch), Image.LANCZOS)
        else:
            img = img.resize((w, h), Image.LANCZOS)

        canvas.delete("all")
        self._displayed_original = ImageTk.PhotoImage(img)
        canvas.create_image(cw // 2, ch // 2, image=self._displayed_original)

    def _display_processed(self) -> None:
        if self.output_image is None:
            return
        canvas = self.processed_display.canvas
        cw = max(canvas.winfo_width(), 1)
        ch = max(canvas.winfo_height(), 1)

        img = self.output_image.copy()
        w = int(img.width * self.zoom_factor)
        h = int(img.height * self.zoom_factor)

        if w > cw or h > ch:
            img.thumbnail((cw, ch), Image.LANCZOS)
        else:
            img = img.resize((w, h), Image.LANCZOS)

        canvas.delete("all")

        if img.mode == "RGBA":
            self._draw_checkerboard(canvas, cw, ch)

        self._displayed_processed = ImageTk.PhotoImage(img)
        canvas.create_image(cw // 2, ch // 2, image=self._displayed_processed)

    def _draw_checkerboard(self, canvas: tk.Canvas, width: int, height: int) -> None:
        """Draw a cached checkerboard pattern for transparent images."""
        if self._checkerboard_size == (width, height) and self._checkerboard_cache:
            canvas.create_image(0, 0, anchor="nw", image=self._checkerboard_cache)
            return

        c1 = self.theme.get_color("checkerboard_1")
        c2 = self.theme.get_color("checkerboard_2")
        size = 12

        cb_img = Image.new("RGB", (width, height))
        for y in range(0, height, size):
            for x in range(0, width, size):
                color = c1 if ((x // size) + (y // size)) % 2 == 0 else c2
                r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                for dy in range(min(size, height - y)):
                    for dx in range(min(size, width - x)):
                        cb_img.putpixel((x + dx, y + dy), (r, g, b))

        self._checkerboard_cache = ImageTk.PhotoImage(cb_img)
        self._checkerboard_size = (width, height)
        canvas.create_image(0, 0, anchor="nw", image=self._checkerboard_cache)

    # ==================== UNDO / REDO ====================

    def _undo(self) -> None:
        if self.editor.undo():
            self._display_original()
            self.output_image = None
            self.processed_display.clear()
            self.actions_panel.save_btn.config(state="disabled")
            self._update_history_panel()
            self.status_text.set("↩️ Undo successful")
        else:
            self.status_text.set("No actions to undo")

    def _redo(self) -> None:
        if self.editor.redo():
            self._display_original()
            self.output_image = None
            self.processed_display.clear()
            self.actions_panel.save_btn.config(state="disabled")
            self._update_history_panel()
            self.status_text.set("↪️ Redo successful")
        else:
            self.status_text.set("No actions to redo")

    def _update_history_panel(self) -> None:
        """Synchronize the history panel with the editor state."""
        self.history_panel.update_history(
            actions=self.editor.history,
            undo_count=self.editor.undo_count,
            redo_count=self.editor.redo_count,
        )

    # ==================== EDIT COMMANDS ====================

    def _after_edit(self, msg: str) -> None:
        """Common UI update after an editing operation."""
        self._display_original()
        self.output_image = None
        self.processed_display.clear()
        self.actions_panel.save_btn.config(state="disabled")
        self._update_history_panel()
        self.status_text.set(msg)

    def _show_rotate_dialog(self) -> None:
        if self.editor.image is None:
            messagebox.showinfo("Info", "Please load an image first.")
            return
        RotateDialog(self.root, self._apply_rotate)

    def _apply_rotate(self, angle: int) -> None:
        if self.editor.rotate(angle):
            self._after_edit(f"Rotated {angle}°")

    def _show_flip_dialog(self) -> None:
        if self.editor.image is None:
            messagebox.showinfo("Info", "Please load an image first.")
            return
        FlipDialog(self.root, self._apply_flip_h, self._apply_flip_v)

    def _apply_flip_h(self) -> None:
        if self.editor.flip_horizontal():
            self._after_edit("Flipped horizontally")

    def _apply_flip_v(self) -> None:
        if self.editor.flip_vertical():
            self._after_edit("Flipped vertically")

    def _show_crop_dialog(self) -> None:
        if self.editor.image is None:
            messagebox.showinfo("Info", "Please load an image first.")
            return
        CropDialog(self.root, self.editor.image, self._apply_crop)

    def _apply_crop(self, left: int, top: int, right: int, bottom: int) -> None:
        if self.editor.crop(left, top, right, bottom):
            self._after_edit("Image cropped")

    def _show_watermark_dialog(self) -> None:
        if self.editor.image is None:
            messagebox.showinfo("Info", "Please load an image first.")
            return
        WatermarkDialog(self.root, self._apply_watermark)

    def _apply_watermark(self, text: str, position: str, opacity: int, font_size: int) -> None:
        if self.editor.add_watermark(text, position, opacity, font_size):
            self._display_original()
            self._update_history_panel()
            self.status_text.set(f"Watermark added: '{text}'")

    def _select_bg_color(self) -> None:
        color = colorchooser.askcolor(title="Select Background Color")
        if color[1]:
            new_color = tuple(map(int, color[0]))
            self.config.set_bg_color(new_color)
            self.exporter.default_bg_color = new_color
            if self.output_image:
                self._display_processed()
            self.status_text.set("Background color changed")

    # ==================== FILTERS ====================

    def _apply_filters(self) -> None:
        if self.editor.image is None:
            return

        b = self.brightness_var.get()
        c = self.contrast_var.get()
        s = self.saturation_var.get()
        sh = self.sharpness_var.get()

        applied = []
        if abs(b - 1.0) > 0.01:
            self.editor.adjust_brightness(b)
            applied.append("brightness")
        if abs(c - 1.0) > 0.01:
            self.editor.adjust_contrast(c)
            applied.append("contrast")
        if abs(s - 1.0) > 0.01:
            self.editor.adjust_saturation(s)
            applied.append("saturation")
        if abs(sh - 1.0) > 0.01:
            self.editor.adjust_sharpness(sh)
            applied.append("sharpness")

        if applied:
            self._after_edit(f"Filters applied: {', '.join(applied)}")
        else:
            self.status_text.set("No filter changes to apply")

    def _reset_filters(self) -> None:
        self.brightness_var.set(1.0)
        self.contrast_var.set(1.0)
        self.saturation_var.set(1.0)
        self.sharpness_var.set(1.0)
        self.status_text.set("Filters reset")

    def _apply_blur(self) -> None:
        if self.editor.image and self.editor.apply_blur(3):
            self._after_edit("Blur applied")

    def _apply_sharpen(self) -> None:
        if self.editor.image and self.editor.apply_sharpen():
            self._after_edit("Sharpen applied")

    def _apply_edge_enhance(self) -> None:
        if self.editor.image and self.editor.apply_edge_enhance():
            self._after_edit("Edge enhance applied")

    def _apply_emboss(self) -> None:
        if self.editor.image and self.editor.apply_emboss():
            self._after_edit("Emboss applied")

    def _apply_grayscale(self) -> None:
        if self.editor.image and self.editor.apply_grayscale():
            self._after_edit("🎨 Grayscale applied")

    def _apply_invert(self) -> None:
        if self.editor.image and self.editor.apply_invert():
            self._after_edit("🔄 Colors inverted")

    def _apply_auto_enhance(self) -> None:
        if self.editor.image and self.editor.apply_auto_enhance():
            self._after_edit("✨ Auto enhance applied")

    # ==================== SAVE ====================

    def _save_image(self) -> None:
        if self.output_image is None:
            return

        fmt = self.format_var.get()
        filename = ExportManager.generate_output_filename(
            self.input_path.get(), file_format=fmt,
        )
        save_path = os.path.join(self.output_directory.get(), filename)

        success = self.exporter.save(
            self.output_image, save_path,
            file_format=fmt,
            quality=self.quality_var.get(),
            bg_color=self.config.get_bg_color(),
        )

        if success:
            self.status_text.set(f"💾 Saved: {filename}")
            if messagebox.askyesno("Saved", "Image saved successfully.\nOpen it now?"):
                open_file(save_path)
        else:
            messagebox.showerror("Error", "Failed to save image.")

    def _save_as(self) -> None:
        if self.output_image is None:
            return

        save_path = filedialog.asksaveasfilename(
            title="Save Image As",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("WEBP", "*.webp"), ("BMP", "*.bmp")],
            initialdir=self.output_directory.get(),
            defaultextension=".png",
        )
        if save_path:
            ext = os.path.splitext(save_path)[1].lstrip(".").lower()
            if ext == "jpg":
                ext = "jpeg"
            success = self.exporter.save(
                self.output_image, save_path,
                file_format=ext,
                quality=self.quality_var.get(),
                bg_color=self.config.get_bg_color(),
            )
            if success:
                self.status_text.set(f"💾 Saved: {os.path.basename(save_path)}")
            else:
                messagebox.showerror("Error", "Failed to save image.")

    def _show_export_dialog(self) -> None:
        if self.output_image is None:
            messagebox.showinfo("Info", "Process an image first.")
            return
        ExportDialog(self.root, self._export_with_preset)

    def _export_with_preset(self, preset_name: str) -> None:
        save_path = filedialog.asksaveasfilename(
            title=f"Export ({preset_name})",
            initialdir=self.output_directory.get(),
            defaultextension=".png",
        )
        if save_path:
            success = self.exporter.save_with_preset(
                self.output_image, save_path, preset_name,
                bg_color=self.config.get_bg_color(),
            )
            if success:
                self.config.set("last_export_preset", preset_name)
                self.status_text.set(f"📤 Exported ({preset_name}): {os.path.basename(save_path)}")
            else:
                messagebox.showerror("Error", "Export failed.")

    # ==================== BATCH ====================

    def _batch_process(self) -> None:
        files = filedialog.askopenfilenames(
            title="Select Images for Batch Processing",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif *.webp")],
            initialdir=os.path.expanduser("~"),
        )
        if not files:
            return

        self.processed_display.show_progress()
        self.status_text.set(f"Batch processing {len(files)} images... (Esc to cancel)")

        def on_progress(current: int, total: int, filename: str) -> None:
            self.root.after(0, lambda: self.processed_display.set_progress(current * 100 / total))
            self.root.after(0, lambda: self.status_text.set(f"Batch: {current}/{total} — {filename}"))

        def on_complete(success: int, total: int) -> None:
            self.root.after(0, self.processed_display.hide_progress)
            self.root.after(0, lambda: self.status_text.set(
                f"✅ Batch complete: {success}/{total} images processed"
            ))
            self.root.after(0, lambda: messagebox.showinfo(
                "Batch Complete", f"{success} of {total} images processed successfully."
            ))

        def on_error(filename: str, error: str) -> None:
            logger.error("Batch error [%s]: %s", filename, error)

        self.processor.batch_process(
            list(files), self.output_directory.get(),
            on_progress, on_complete, on_error,
        )

    # ==================== VIEW ====================

    def _zoom(self, factor: float, reset: bool = False) -> None:
        if self.editor.image is None:
            return
        if reset:
            self.zoom_factor = 1.0
        else:
            self.zoom_factor = max(0.1, min(self.zoom_factor * factor, 5.0))

        self._display_original()
        if self.output_image:
            self._display_processed()

        self.zoom_label.config(text=f"Zoom: {self.zoom_factor:.1f}x")

    def _show_compare_dialog(self) -> None:
        if self.editor.image is None or self.output_image is None:
            messagebox.showinfo("Info", "Both original and processed images are required.")
            return
        CompareDialog(self.root, self.editor.image, self.output_image)

    def _show_image_info(self) -> None:
        if self.editor.image is None:
            messagebox.showinfo("Info", "Please load an image first.")
            return
        ImageInfoDialog(self.root, self.editor.image, self._full_input_path)

    # ==================== MISC ====================

    def _toggle_theme(self) -> None:
        new_theme = self.theme.toggle_theme()
        self.config.set("theme", new_theme)

        canvas_bg = self.theme.get_color("canvas_bg")
        self.original_display.update_canvas_bg(canvas_bg)
        self.processed_display.update_canvas_bg(canvas_bg)

        # Update history panel theme
        self.history_panel.update_theme(
            bg=self.theme.get_color("bg_alt"),
            fg=self.theme.get_color("text"),
            select_bg=self.theme.get_color("primary"),
        )

        # Clear checkerboard cache (colors changed)
        self._checkerboard_cache = None

        if self.editor.image:
            self._display_original()
        if self.output_image:
            self._display_processed()

        self.status_text.set(f"Theme: {new_theme.title()}")

    def _on_resize(self, event: tk.Event) -> None:
        if self._resize_timer:
            self.root.after_cancel(self._resize_timer)
        self._resize_timer = self.root.after(200, self._do_resize)

    def _do_resize(self) -> None:
        self._resize_timer = None
        # Clear checkerboard cache (size changed)
        self._checkerboard_cache = None
        if self.editor.image:
            self._display_original()
        if self.output_image:
            self._display_processed()

    def _select_output_dir(self) -> None:
        directory = filedialog.askdirectory(
            title="Select Save Location",
            initialdir=self.output_directory.get(),
        )
        if directory:
            self.output_directory.set(directory)
            self.config.set("output_directory", directory)
            self.status_text.set(f"Save location: {directory}")

    def _update_recent_menu(self) -> None:
        self.recent_menu.delete(0, "end")
        recent = self.config.get_recent_files()
        if not recent:
            self.recent_menu.add_command(label="(empty)", state="disabled")
        else:
            for path in recent[:10]:
                name = os.path.basename(path)
                self.recent_menu.add_command(
                    label=name, command=lambda p=path: self._load_image(p),
                )
            self.recent_menu.add_separator()
            self.recent_menu.add_command(label="Clear Recent", command=self._clear_recent)

    def _clear_recent(self) -> None:
        self.config.clear_recent_files()
        self._update_recent_menu()

    def _show_help(self) -> None:
        messagebox.showinfo(
            f"Help — Background Remover Pro v{self.VERSION}",
            "🖼️ Professional Background Remover Pro\n\n"
            "Shortcuts:\n"
            "  Ctrl+O — Open image\n"
            "  Ctrl+S — Save image\n"
            "  Ctrl+P — Remove background\n"
            "  Ctrl+Z — Undo\n"
            "  Ctrl+Y — Redo\n"
            "  Ctrl+/- — Zoom in/out\n"
            "  Esc — Cancel processing\n\n"
            "Features:\n"
            "  • AI-powered background removal\n"
            "  • Undo/Redo with history\n"
            "  • Filters (brightness, contrast, saturation, sharpness)\n"
            "  • Blur, Sharpen, Edge Enhance, Emboss\n"
            "  • Grayscale, Invert, Auto-Enhance\n"
            "  • Crop, Rotate, Flip\n"
            "  • Watermark support\n"
            "  • Batch processing with cancel\n"
            "  • Export presets (Web, Print, Social)\n"
            "  • Dark/Light theme\n"
            "  • Recent files\n"
        )

    def _on_closing(self) -> None:
        self.config.set("output_directory", self.output_directory.get())
        self.config.set("format", self.format_var.get())
        self.config.set("quality", self.quality_var.get())
        self.config.set("window_geometry", self.root.geometry())
        self.config.save()
        logger.info("Application closed.")
        self.root.destroy()
