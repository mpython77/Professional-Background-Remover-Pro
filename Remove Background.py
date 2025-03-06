import os
import threading
import json
import sys
import subprocess
import platform
from pathlib import Path
import numpy as np
from rembg import remove
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageEnhance
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser

class EnhancedBackgroundRemover:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional Background Remover Pro")
        self.config_file = os.path.join(os.path.expanduser("~"), ".bgremover_config.json")
        
        self.setup_window_geometry()
        self.setup_theme()
        self.setup_variables()
        self.create_ui()
        self.load_config()
        self.setup_event_bindings()

    def setup_window_geometry(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        position_x = (screen_width - window_width) // 2
        position_y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
        self.root.minsize(1000, 700)
        
        try:
            if platform.system() == "Windows":
                self.root.iconbitmap(self.resource_path("icon.ico"))
            else:
                icon = tk.PhotoImage(file=self.resource_path("icon.png"))
                self.root.iconphoto(True, icon)
        except:
            pass

    def setup_theme(self):
        self.colors = {
            "primary": "#4361ee",
            "secondary": "#3a0ca3",
            "bg": "#f8f9fa",
            "light": "#e9ecef",
            "dark": "#495057",
            "success": "#06d6a0",
            "warning": "#ffd166",
            "danger": "#ef476f",
            "text": "#212529",
            "text_light": "#6c757d"
        }
        
        self.root.configure(bg=self.colors["bg"])
        self.theme_var = tk.StringVar(value="light")
        
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except:
            pass
            
        self.configure_styles()

    def configure_styles(self):
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("TButton", font=("Helvetica", 11))
        self.style.configure("Accent.TButton", font=("Helvetica", 12, "bold"), 
                           background=self.colors["primary"])
        self.style.configure("Success.TButton", font=("Helvetica", 11), 
                           background=self.colors["success"])
        self.style.configure("Warning.TButton", font=("Helvetica", 11), 
                           background=self.colors["warning"])
        self.style.configure("Danger.TButton", font=("Helvetica", 11), 
                           background=self.colors["danger"])
        self.style.configure("TLabel", font=("Helvetica", 11), 
                           background=self.colors["bg"])
        self.style.configure("Header.TLabel", font=("Helvetica", 20, "bold"), 
                           background=self.colors["bg"], foreground=self.colors["secondary"])
        self.style.configure("Subheader.TLabel", font=("Helvetica", 14), 
                           background=self.colors["bg"], foreground=self.colors["primary"])
        self.style.configure("Status.TLabel", font=("Helvetica", 10), 
                           background=self.colors["bg"], foreground=self.colors["text_light"])

    def setup_variables(self):
        self.input_path = tk.StringVar()
        self.output_directory = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Pictures"))
        self.status_text = tk.StringVar(value="Welcome! Please select an image.")
        self.processing = False
        self.recent_files = []
        self.max_recent_files = 5
        self.progress_var = tk.DoubleVar()
        self.zoom_factor = 1.0
        self.undo_stack = []  # For undo functionality
        
        self.input_image = None
        self.output_image = None
        self.displayed_original = None
        self.displayed_processed = None
        self.bg_color = (240, 240, 240)
        
        self.format_var = tk.StringVar(value="png")
        self.quality_var = tk.IntVar(value=90)
        self.alpha_var = tk.DoubleVar(value=0)
        self.smooth_var = tk.DoubleVar(value=0)
        self.edge_var = tk.DoubleVar(value=0.5)
        self.bg_var = tk.StringVar(value="transparent")
        self.blur_var = tk.IntVar(value=0)
        self.brightness_var = tk.DoubleVar(value=1.0)
        self.contrast_var = tk.DoubleVar(value=1.0)
        self.saturation_var = tk.DoubleVar(value=1.0)

    def create_ui(self):
        self.container = ttk.Frame(self.root, style="TFrame")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.create_menu()
        self.create_header()
        self.create_main_area()
        self.create_status_bar()

    def setup_event_bindings(self):
        self.root.bind("<Configure>", self.on_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind("<Control-o>", lambda e: self.select_image())
        self.root.bind("<Control-s>", lambda e: self.save_image())
        self.root.bind("<Control-p>", lambda e: self.process_image() 
                      if self.process_btn['state'] != 'disabled' else None)
        self.root.bind("<Control-z>", lambda e: self.undo())

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Image... (Ctrl+O)", command=self.select_image)
        file_menu.add_command(label="Select Output Directory...", command=self.select_output_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Save... (Ctrl+S)", command=self.save_image)
        file_menu.add_command(label="Save As...", command=self.save_as_different_format)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Remove Background (Ctrl+P)", command=self.process_image)
        edit_menu.add_command(label="Crop Image...", command=self.crop_image)
        edit_menu.add_command(label="Rotate Image...", command=self.rotate_image)
        edit_menu.add_command(label="Flip Image...", command=self.flip_image)
        edit_menu.add_command(label="Undo (Ctrl+Z)", command=self.undo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Select Background Color...", command=self.select_background_color)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=lambda: self.zoom_view(1.2))
        view_menu.add_command(label="Zoom Out", command=lambda: self.zoom_view(0.8))
        view_menu.add_command(label="Reset Zoom", command=lambda: self.zoom_view(1.0, reset=True))
        view_menu.add_command(label="Compare Mode", command=self.compare_images)
        
        batch_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Batch", menu=batch_menu)
        batch_menu.add_command(label="Process Multiple Images...", command=self.batch_process)

    def create_header(self):
        header_frame = ttk.Frame(self.container, style="TFrame")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(header_frame, text="🖼️", font=("Helvetica", 28), 
                 background=self.colors["bg"]).pack(side="left", padx=(0, 10))
        ttk.Label(header_frame, text="Professional Background Remover Pro", 
                 style="Header.TLabel").pack(side="left")
        
        quick_buttons_frame = ttk.Frame(header_frame, style="TFrame")
        quick_buttons_frame.pack(side="right")
        
        ttk.Button(quick_buttons_frame, text="❓", width=3, 
                  command=self.show_help).pack(side="right", padx=5)

    def create_main_area(self):
        main_content = ttk.Frame(self.container, style="TFrame")
        main_content.pack(fill="both", expand=True, pady=10)
        
        left_panel = ttk.Frame(main_content, style="TFrame")
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        
        self.create_input_panel(left_panel)
        self.create_settings_panel(left_panel)
        self.create_actions_panel(left_panel)
        
        right_panel = ttk.Frame(main_content, style="TFrame")
        right_panel.pack(side="right", fill="both", expand=True)
        
        self.create_image_displays(right_panel)

    def create_input_panel(self, parent):
        input_frame = ttk.LabelFrame(parent, text="Image Selection", style="TFrame")
        input_frame.pack(fill="x", pady=(0, 10), padx=5)
        
        btn_frame = ttk.Frame(input_frame, style="TFrame")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Select Image", command=self.select_image, 
                  style="TButton").pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Clipboard", command=self.paste_from_clipboard, 
                  style="TButton").pack(side="left")
        
        self.input_label = ttk.Label(input_frame, textvariable=self.input_path, 
                                   style="TLabel", wraplength=200)
        self.input_label.pack(fill="x", padx=10, pady=(0, 10))
        
        output_frame = ttk.Frame(input_frame, style="TFrame")
        output_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ttk.Label(output_frame, text="Save Location:", style="TLabel").pack(anchor="w")
        
        output_btn_frame = ttk.Frame(output_frame, style="TFrame")
        output_btn_frame.pack(fill="x", pady=(5, 0))
        
        ttk.Button(output_btn_frame, text="Select Location", 
                  command=self.select_output_directory, style="TButton").pack(side="left")
        ttk.Button(output_btn_frame, text="Open", 
                  command=lambda: self.open_file(self.output_directory.get()), 
                  style="TButton").pack(side="left", padx=(5, 0))
        
        self.output_label = ttk.Label(output_frame, textvariable=self.output_directory, 
                                    style="TLabel", wraplength=200)
        self.output_label.pack(fill="x", pady=(5, 0))

    def create_settings_panel(self, parent):
        settings_frame = ttk.LabelFrame(parent, text="Settings", style="TFrame")
        settings_frame.pack(fill="x", pady=(0, 10), padx=5)
        
        notebook = ttk.Notebook(settings_frame)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        basic_tab = ttk.Frame(notebook)
        notebook.add(basic_tab, text="Basic")
        
        format_frame = ttk.Frame(basic_tab, style="TFrame")
        format_frame.pack(fill="x", pady=5)
        ttk.Label(format_frame, text="Format:", style="TLabel").pack(anchor="w")
        
        format_radio_frame = ttk.Frame(format_frame, style="TFrame")
        format_radio_frame.pack(fill="x", pady=(5, 0))
        ttk.Radiobutton(format_radio_frame, text="PNG (transparent)", 
                       variable=self.format_var, value="png").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(format_radio_frame, text="JPEG", 
                       variable=self.format_var, value="jpeg").pack(side="left")
        
        quality_frame = ttk.Frame(basic_tab, style="TFrame")
        quality_frame.pack(fill="x", pady=10)
        ttk.Label(quality_frame, text="Quality:", style="TLabel").pack(anchor="w")
        
        quality_slider_frame = ttk.Frame(quality_frame, style="TFrame")
        quality_slider_frame.pack(fill="x", pady=(5, 0))
        self.quality_slider = ttk.Scale(quality_slider_frame, from_=1, to=100, 
                                      orient="horizontal", variable=self.quality_var)
        self.quality_slider.pack(side="left", fill="x", expand=True)
        ttk.Label(quality_slider_frame, textvariable=self.quality_var, 
                 style="TLabel", width=3).pack(side="left", padx=5)
        ttk.Label(quality_slider_frame, text="%", style="TLabel").pack(side="left")

    def create_actions_panel(self, parent):
        actions_frame = ttk.LabelFrame(parent, text="Actions", style="TFrame")
        actions_frame.pack(fill="x", pady=(0, 10), padx=5)
        
        main_actions_frame = ttk.Frame(actions_frame, style="TFrame")
        main_actions_frame.pack(fill="x", padx=10, pady=10)
        
        self.process_btn = ttk.Button(main_actions_frame, text="Remove Background", 
                                    command=self.process_image, style="Accent.TButton", 
                                    state="disabled")
        self.process_btn.pack(fill="x", pady=(0, 5))
        
        self.save_btn = ttk.Button(main_actions_frame, text="Save Image", 
                                 command=self.save_image, style="Success.TButton", 
                                 state="disabled")
        self.save_btn.pack(fill="x", pady=(0, 5))

    def create_image_displays(self, parent):
        display_frame = ttk.Frame(parent, style="TFrame")
        display_frame.pack(fill="both", expand=True)
        
        self.original_frame = ttk.LabelFrame(display_frame, text="Original Image", style="TFrame")
        self.original_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.original_canvas = tk.Canvas(self.original_frame, bg=self.colors["light"], 
                                       highlightthickness=0)
        self.original_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.original_info_var = tk.StringVar(value="")
        self.original_info = ttk.Label(self.original_frame, textvariable=self.original_info_var, 
                                     style="Status.TLabel", anchor="center")
        self.original_info.pack(fill="x", padx=5, pady=(0, 5))
        
        self.processed_frame = ttk.LabelFrame(display_frame, text="Processed Image", 
                                            style="TFrame")
        self.processed_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.processed_canvas = tk.Canvas(self.processed_frame, bg=self.colors["light"], 
                                        highlightthickness=0)
        self.processed_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.processed_info_var = tk.StringVar(value="")
        self.processed_info = ttk.Label(self.processed_frame, textvariable=self.processed_info_var, 
                                      style="Status.TLabel", anchor="center")
        self.processed_info.pack(fill="x", padx=5, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(self.processed_frame, variable=self.progress_var, 
                                          mode="determinate")
        self.progress_bar.pack(fill="x", padx=5, pady=(0, 5))
        self.progress_bar.pack_forget()

    def create_status_bar(self):
        status_frame = ttk.Frame(self.container, style="TFrame")
        status_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(status_frame, textvariable=self.status_text, 
                 style="Status.TLabel").pack(side="left")
        ttk.Label(status_frame, text="v1.2.0", style="Status.TLabel").pack(side="right")

    # New Functions Added:

    def rotate_image(self):
        """Rotate the image by a specified angle"""
        if not self.input_image:
            messagebox.showinfo("Info", "Please load an image first.")
            return
            
        rotate_window = tk.Toplevel(self.root)
        rotate_window.title("Rotate Image")
        rotate_window.geometry("400x200")
        rotate_window.transient(self.root)
        rotate_window.grab_set()
        
        frame = ttk.Frame(rotate_window, padding=20)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Rotation Angle:").pack(anchor="w")
        angle_var = tk.IntVar(value=0)
        ttk.Scale(frame, from_=0, to=360, orient="horizontal", 
                 variable=angle_var).pack(fill="x", pady=5)
        ttk.Label(frame, textvariable=angle_var, width=4).pack(pady=5)
        
        def apply_rotation():
            if self.input_image:
                self.undo_stack.append(self.input_image.copy())
                self.input_image = self.input_image.rotate(angle_var.get(), expand=True)
                self.display_original_image()
                self.output_image = None
                self.processed_canvas.delete("all")
                self.save_btn.config(state="disabled")
                self.status_text.set(f"Image rotated by {angle_var.get()}°")
            rotate_window.destroy()
        
        ttk.Button(frame, text="Apply", command=apply_rotation).pack(side="right", padx=5)
        ttk.Button(frame, text="Cancel", command=rotate_window.destroy).pack(side="right")

    def flip_image(self):
        """Flip the image horizontally or vertically"""
        if not self.input_image:
            messagebox.showinfo("Info", "Please load an image first.")
            return
            
        flip_window = tk.Toplevel(self.root)
        flip_window.title("Flip Image")
        flip_window.geometry("300x150")
        flip_window.transient(self.root)
        flip_window.grab_set()
        
        frame = ttk.Frame(flip_window, padding=20)
        frame.pack(fill="both", expand=True)
        
        def flip_horizontal():
            if self.input_image:
                self.undo_stack.append(self.input_image.copy())
                self.input_image = self.input_image.transpose(Image.FLIP_LEFT_RIGHT)
                self.display_original_image()
                self.output_image = None
                self.processed_canvas.delete("all")
                self.save_btn.config(state="disabled")
                self.status_text.set("Image flipped horizontally")
            flip_window.destroy()
        
        def flip_vertical():
            if self.input_image:
                self.undo_stack.append(self.input_image.copy())
                self.input_image = self.input_image.transpose(Image.FLIP_TOP_BOTTOM)
                self.display_original_image()
                self.output_image = None
                self.processed_canvas.delete("all")
                self.save_btn.config(state="disabled")
                self.status_text.set("Image flipped vertically")
            flip_window.destroy()
        
        ttk.Button(frame, text="Flip Horizontal", command=flip_horizontal).pack(pady=5)
        ttk.Button(frame, text="Flip Vertical", command=flip_vertical).pack(pady=5)
        ttk.Button(frame, text="Cancel", command=flip_window.destroy).pack(pady=5)

    def undo(self):
        """Revert to the previous image state"""
        if not self.undo_stack:
            messagebox.showinfo("Info", "No actions to undo.")
            return
            
        self.input_image = self.undo_stack.pop()
        self.display_original_image()
        self.output_image = None
        self.processed_canvas.delete("all")
        self.save_btn.config(state="disabled")
        self.status_text.set("Last action undone")

    def crop_image(self):
        if not self.input_image:
            messagebox.showinfo("Info", "Please load an image first.")
            return
            
        crop_window = tk.Toplevel(self.root)
        crop_window.title("Crop Image")
        crop_window.geometry("600x500")
        crop_window.transient(self.root)
        crop_window.grab_set()
        
        canvas = tk.Canvas(crop_window, bg="gray")
        canvas.pack(fill="both", expand=True)
        
        img = self.input_image.copy()
        img_tk = ImageTk.PhotoImage(img)
        canvas.create_image(0, 0, anchor="nw", image=img_tk)
        canvas.image = img_tk
        
        crop_rect = [0, 0, 0, 0]
        rect_id = None
        
        def start_crop(event):
            nonlocal rect_id
            crop_rect[0], crop_rect[1] = event.x, event.y
            if rect_id:
                canvas.delete(rect_id)
            rect_id = canvas.create_rectangle(crop_rect[0], crop_rect[1], 
                                            crop_rect[0], crop_rect[1], 
                                            outline="red", dash=(4, 2))
        
        def update_crop(event):
            nonlocal rect_id
            crop_rect[2], crop_rect[3] = event.x, event.y
            if rect_id:
                canvas.coords(rect_id, crop_rect[0], crop_rect[1], 
                            crop_rect[2], crop_rect[3])
        
        def finish_crop(event):
            nonlocal rect_id
            crop_rect[2], crop_rect[3] = event.x, event.y
            if rect_id:
                canvas.delete(rect_id)
            left = min(crop_rect[0], crop_rect[2])
            top = min(crop_rect[1], crop_rect[3])
            right = max(crop_rect[0], crop_rect[2])
            bottom = max(crop_rect[1], crop_rect[3])
            
            if left < right and top < bottom:
                self.undo_stack.append(self.input_image.copy())
                self.input_image = self.input_image.crop((left, top, right, bottom))
                self.display_original_image()
                self.output_image = None
                self.processed_canvas.delete("all")
                self.save_btn.config(state="disabled")
                self.status_text.set("Image cropped")
            crop_window.destroy()
        
        canvas.bind("<Button-1>", start_crop)
        canvas.bind("<B1-Motion>", update_crop)
        canvas.bind("<ButtonRelease-1>", finish_crop)

    def zoom_view(self, factor, reset=False):
        if not self.input_image:
            return
            
        if reset:
            self.zoom_factor = 1.0
        else:
            self.zoom_factor *= factor
            
        self.display_original_image()
        if self.output_image:
            self.display_processed_image()
        self.status_text.set(f"Zoom: {self.zoom_factor:.1f}x")

    def paste_from_clipboard(self):
        try:
            clipboard_img = ImageGrab.grabclipboard()
            if isinstance(clipboard_img, Image.Image):
                self.input_image = clipboard_img
                self.input_path.set("Loaded from clipboard")
                self.display_original_image()
                self.process_btn.config(state="normal")
                self.output_image = None
                self.processed_canvas.delete("all")
                self.save_btn.config(state="disabled")
                self.status_text.set("Image loaded from clipboard")
            else:
                messagebox.showinfo("Info", "No image found in clipboard")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load from clipboard: {str(e)}")

    def compare_images(self):
        if not self.input_image or not self.output_image:
            messagebox.showinfo("Info", "Both original and processed images are required for comparison")
            return
            
        compare_window = tk.Toplevel(self.root)
        compare_window.title("Compare Images")
        compare_window.geometry("800x600")
        compare_window.transient(self.root)
        
        frame = ttk.Frame(compare_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ttk.Label(frame, text="Original Image").pack(side="left", padx=(0, 5))
        orig_canvas = tk.Canvas(frame, bg="white")
        orig_canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        ttk.Label(frame, text="Processed Image").pack(side="left", padx=(5, 0))
        proc_canvas = tk.Canvas(frame, bg="white")
        proc_canvas.pack(side="left", fill="both", expand=True)
        
        def update_compare():
            width = max(orig_canvas.winfo_width(), 1)
            height = max(orig_canvas.winfo_height(), 1)
            
            orig_img = self.input_image.resize(
                (int(self.input_image.width * self.zoom_factor), 
                 int(self.input_image.height * self.zoom_factor)), 
                Image.LANCZOS)
            orig_tk = ImageTk.PhotoImage(orig_img)
            orig_canvas.delete("all")
            orig_canvas.create_image(width//2, height//2, image=orig_tk)
            orig_canvas.image = orig_tk
            
            proc_img = self.output_image.resize(
                (int(self.output_image.width * self.zoom_factor), 
                 int(self.output_image.height * self.zoom_factor)), 
                Image.LANCZOS)
            proc_tk = ImageTk.PhotoImage(proc_img)
            proc_canvas.delete("all")
            if proc_img.mode == 'RGBA':
                self.create_transparent_background(width, height)
            proc_canvas.create_image(width//2, height//2, image=proc_tk)
            proc_canvas.image = proc_tk
        
        compare_window.after(100, update_compare)
        orig_canvas.bind("<Configure>", lambda e: update_compare())

    def batch_process(self):
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif *.webp")],
            initialdir=os.path.expanduser("~")
        )
        
        if not files:
            return
            
        self.processing = True
        self.progress_var.set(0)
        self.progress_bar.pack(fill="x", padx=5, pady=(0, 5))
        self.status_text.set("Batch processing started...")
        
        def process_batch():
            total = len(files)
            for i, file_path in enumerate(files):
                try:
                    img = Image.open(file_path)
                    img_np = np.array(img.convert('RGB'))
                    output_np = remove(img_np)
                    output_img = Image.fromarray(output_np)
                    
                    filename = f"{os.path.splitext(os.path.basename(file_path))[0]}_nobg.png"
                    save_path = os.path.join(self.output_directory.get(), filename)
                    output_img.save(save_path, "PNG", optimize=True)
                    
                    self.update_progress((i + 1) * 100 / total)
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Error", f"Error processing file ({file_path}): {str(e)}"))
            
            self.processing = False
            self.root.after(0, lambda: self.progress_bar.pack_forget())
            self.root.after(0, lambda: self.status_text.set("Batch processing completed"))
        
        threading.Thread(target=process_batch, daemon=True).start()

    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif *.webp"), 
                      ("All files", "*.*")],
            initialdir=os.path.expanduser("~")
        )
        if file_path:
            self.input_path.set(file_path)
            self.load_image(file_path)
            self.status_text.set(f"Image loaded: {os.path.basename(file_path)}")

    def load_image(self, file_path):
        try:
            self.input_image = Image.open(file_path)
            self.undo_stack = []  # Reset undo stack on new image load
            self.display_original_image()
            self.process_btn.config(state="normal")
            width, height = self.input_image.size
            size_kb = os.path.getsize(file_path) / 1024
            self.original_info_var.set(f"{width}x{height} pixels • {size_kb:.1f} KB")
            self.output_image = None
            self.processed_info_var.set("")
            self.processed_canvas.delete("all")
            self.save_btn.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def display_original_image(self):
        if not self.input_image:
            return
        canvas_width = max(self.original_canvas.winfo_width(), 1)
        canvas_height = max(self.original_canvas.winfo_height(), 1)
        self.original_canvas.delete("all")
        img_width = int(self.input_image.width * self.zoom_factor)
        img_height = int(self.input_image.height * self.zoom_factor)
        resized_img = self.input_image.resize((img_width, img_height), Image.LANCZOS)
        self.displayed_original = ImageTk.PhotoImage(resized_img)
        self.original_canvas.create_image(canvas_width//2, canvas_height//2, 
                                        image=self.displayed_original)

    def process_image(self):
        if not self.input_image or self.processing:
            return
        self.processing = True
        self.progress_var.set(0)
        self.progress_bar.pack(fill="x", padx=5, pady=(0, 5))
        self.status_text.set("Processing...")
        threading.Thread(target=self._process_thread, daemon=True).start()

    def _process_thread(self):
        try:
            img_np = np.array(self.input_image.convert('RGBA' if self.input_image.mode == 'RGBA' else 'RGB'))
            self.update_progress(20)
            output_np = remove(img_np)
            self.update_progress(60)
            output_img = Image.fromarray(output_np)
            self.update_progress(80)
            self.output_image = output_img
            self.root.after(0, self._update_ui_after_processing)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Processing error: {str(e)}"))
        finally:
            self.processing = False
            self.root.after(0, lambda: self.progress_bar.pack_forget())

    def _update_ui_after_processing(self):
        self.display_processed_image()
        self.save_btn.config(state="normal")
        if self.output_image:
            width, height = self.output_image.size
            self.processed_info_var.set(f"{width}x{height} pixels • {self.output_image.mode}")
        self.status_text.set("Processing completed")
        self.update_progress(100)

    def update_progress(self, value):
        self.progress_var.set(value)
        self.root.update_idletasks()

    def save_image(self):
        if not self.output_image:
            return
        file_format = self.format_var.get().upper()
        filename = f"{os.path.splitext(os.path.basename(self.input_path.get()))[0]}_nobg.{file_format.lower()}"
        save_path = os.path.join(self.output_directory.get(), filename)
        try:
            if file_format == 'PNG':
                self.output_image.save(save_path, format=file_format, optimize=True)
            else:
                bg = Image.new('RGB', self.output_image.size, self.bg_color)
                if self.output_image.mode in ('RGBA', 'LA'):
                    bg.paste(self.output_image, mask=self.output_image.split()[3 if self.output_image.mode == 'RGBA' else 1])
                else:
                    bg = self.output_image.convert('RGB')
                bg.save(save_path, format=file_format, quality=self.quality_var.get(), optimize=True)
            self.status_text.set(f"Image saved: {filename}")
            if messagebox.askyesno("Saved", "Image saved successfully.\nOpen it now?"):
                self.open_file(save_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {str(e)}")

    def display_processed_image(self):
        if not self.output_image:
            return
        canvas_width = max(self.processed_canvas.winfo_width(), 1)
        canvas_height = max(self.processed_canvas.winfo_height(), 1)
        self.processed_canvas.delete("all")
        img_width = int(self.output_image.width * self.zoom_factor)
        img_height = int(self.output_image.height * self.zoom_factor)
        resized_img = self.output_image.resize((img_width, img_height), Image.LANCZOS)
        if self.bg_var.get() == "transparent" and self.output_image.mode == 'RGBA':
            self.create_transparent_background(canvas_width, canvas_height)
            self.displayed_processed = ImageTk.PhotoImage(resized_img)
            self.processed_canvas.create_image(canvas_width//2, canvas_height//2, 
                                             image=self.displayed_processed)
        else:
            bg = Image.new("RGB", (canvas_width, canvas_height), self.rgb_to_hex(self.bg_color))
            bg.paste(resized_img, (canvas_width//2 - img_width//2, canvas_height//2 - img_height//2),
                    resized_img if resized_img.mode == 'RGBA' else None)
            self.displayed_processed = ImageTk.PhotoImage(bg)
            self.processed_canvas.create_image(0, 0, anchor="nw", image=self.displayed_processed)

    def create_transparent_background(self, width, height):
        self.processed_canvas.delete("checkerboard")
        square_size = 10
        for y in range(0, height, square_size):
            for x in range(0, width, square_size):
                color = "#EEEEEE" if ((x // square_size) + (y // square_size)) % 2 == 0 else "#CCCCCC"
                self.processed_canvas.create_rectangle(x, y, x + square_size, y + square_size,
                                                     fill=color, outline="", tags="checkerboard")

    def on_resize(self, event):
        if self.input_image:
            self.display_original_image()
        if self.output_image:
            self.display_processed_image()

    def on_closing(self):
        self.save_config()
        self.root.destroy()

    def rgb_to_hex(self, rgb):
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    def resource_path(self, relative_path):
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    def open_file(self, file_path):
        try:
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":
                subprocess.call(["open", file_path])
            else:
                subprocess.call(["xdg-open", file_path])
        except:
            messagebox.showerror("Error", "Failed to open file")

    def save_config(self):
        config = {
            'output_directory': self.output_directory.get(),
            'bg_color': self.bg_color,
            'format': self.format_var.get(),
            'quality': self.quality_var.get()
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except:
            pass

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                if 'output_directory' in config and os.path.exists(config['output_directory']):
                    self.output_directory.set(config['output_directory'])
                if 'bg_color' in config:
                    self.bg_color = tuple(config['bg_color'])
                if 'format' in config and config['format'] in ['png', 'jpg']:
                    self.format_var.set(config['format'])
                if 'quality' in config and 1 <= config['quality'] <= 100:
                    self.quality_var.set(config['quality'])
        except:
            pass

    def select_output_directory(self):
        directory = filedialog.askdirectory(
            title="Select Save Location",
            initialdir=self.output_directory.get()
        )
        if directory:
            self.output_directory.set(directory)
            self.status_text.set(f"Save location selected: {directory}")

    def save_as_different_format(self):
        if not self.output_image:
            return
        save_path = filedialog.asksaveasfilename(
            title="Save Image",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp")],
            initialdir=self.output_directory.get(),
            defaultextension=".png"
        )
        if save_path:
            try:
                self.output_image.save(save_path)
                self.status_text.set(f"Image saved: {os.path.basename(save_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")

    def select_background_color(self):
        color = colorchooser.askcolor(title="Select Background Color")
        if color[1]:
            self.bg_color = tuple(map(int, color[0]))
            if self.output_image:
                self.display_processed_image()
            self.status_text.set("Background color changed")

    def show_help(self):
        messagebox.showinfo("Help", "Select an image and click 'Remove Background' to start.")

if __name__ == "__main__":
    try:
        from PIL import ImageGrab
    except ImportError:
        ImageGrab = None
    root = tk.Tk()
    app = EnhancedBackgroundRemover(root)
    root.mainloop()
