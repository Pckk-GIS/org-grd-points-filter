"""GUI の詳細ヘルプを表示するウィンドウ。"""

from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext, ttk

from . import labels
from .help_text import HELP_TEXT


class HelpWindow(tk.Toplevel):
    """使い方を表示する別ウィンドウ。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.title(labels.HELP_WINDOW_TITLE)
        self.geometry("780x640")
        self.minsize(720, 560)

        container = ttk.Frame(self, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        text = scrolledtext.ScrolledText(container, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert("1.0", HELP_TEXT)
        text.configure(state="disabled")
