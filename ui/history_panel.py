"""History panel — action history and Shortcuts panel."""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional

from utils.logger import setup_logger

logger = setup_logger(__name__)


class HistoryPanel(ttk.LabelFrame):
    """Action history panel — undo/redo stack visualization.

    Attributes:
        history_list: Tkinter Listbox displaying the list of actions.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_undo: Callable,
        on_redo: Callable,
        **kwargs,
    ) -> None:
        super().__init__(parent, text="📜 History", **kwargs)

        # Undo/Redo buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=8, pady=(8, 3))

        self.undo_btn = ttk.Button(btn_frame, text="↩ Undo", command=on_undo, width=8)
        self.undo_btn.pack(side="left", padx=(0, 3))

        self.redo_btn = ttk.Button(btn_frame, text="↪ Redo", command=on_redo, width=8)
        self.redo_btn.pack(side="left", padx=(3, 0))

        # Clear button
        self.clear_btn = ttk.Button(btn_frame, text="🗑", width=3)
        self.clear_btn.pack(side="right")

        # Action list
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.history_list = tk.Listbox(
            list_frame,
            height=6,
            font=("Consolas", 9),
            selectmode="single",
            bg="#f8f9fa",
            fg="#333",
            selectbackground="#4361ee",
            selectforeground="#fff",
            relief="flat",
            borderwidth=1,
        )
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.history_list.yview)
        self.history_list.configure(yscrollcommand=scrollbar.set)

        self.history_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Undo/Redo counter
        self.counter_var = tk.StringVar(value="Undo: 0 | Redo: 0")
        ttk.Label(self, textvariable=self.counter_var, style="Status.TLabel").pack(
            fill="x", padx=8, pady=(0, 5)
        )

    def update_history(
        self,
        actions: List[str],
        undo_count: int = 0,
        redo_count: int = 0,
    ) -> None:
        """Update the action list display.

        Args:
            actions: List of action names.
            undo_count: Number of entries in the undo stack.
            redo_count: Number of entries in the redo stack.
        """
        self.history_list.delete(0, "end")
        for i, action in enumerate(actions):
            self.history_list.insert("end", f"  {i + 1}. {action}")

        # Scroll to the latest entry
        if actions:
            self.history_list.see("end")

        self.counter_var.set(f"Undo: {undo_count} | Redo: {redo_count}")

        # Update button states
        self.undo_btn.config(state="normal" if undo_count > 0 else "disabled")
        self.redo_btn.config(state="normal" if redo_count > 0 else "disabled")

    def update_theme(self, bg: str, fg: str, select_bg: str) -> None:
        """Update colors to match the theme."""
        self.history_list.configure(bg=bg, fg=fg, selectbackground=select_bg)


class ShortcutsPanel(ttk.LabelFrame):
    """Keyboard shortcuts panel."""

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        super().__init__(parent, text="⌨️ Shortcuts", **kwargs)

        shortcuts = [
            ("Ctrl+O", "Open Image"),
            ("Ctrl+S", "Save"),
            ("Ctrl+P", "Remove BG"),
            ("Ctrl+Z", "Undo"),
            ("Ctrl+Y", "Redo"),
            ("Ctrl+±", "Zoom"),
            ("Ctrl+0", "Reset Zoom"),
        ]

        for key, action in shortcuts:
            row = ttk.Frame(self)
            row.pack(fill="x", padx=8, pady=1)
            ttk.Label(row, text=key, font=("Consolas", 8, "bold"), width=8).pack(side="left")
            ttk.Label(row, text=action, font=("Segoe UI", 8), style="Status.TLabel").pack(side="left", padx=(5, 0))
