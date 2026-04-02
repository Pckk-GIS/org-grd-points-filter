from __future__ import annotations

import tkinter as tk


class ToolTip:
    def __init__(self, widget: tk.Widget, text: str, delay_ms: int = 450) -> None:
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self.tipwindow: tk.Toplevel | None = None
        self._after_id: str | None = None
        self._visible = False

        widget.bind("<Enter>", self._schedule_show, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule_show(self, _event: tk.Event[tk.Misc]) -> None:
        self._cancel_schedule()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel_schedule(self) -> None:
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self) -> None:
        if self.tipwindow is not None or self._visible:
            return

        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8

        self.tipwindow = tk.Toplevel(self.widget)
        self.tipwindow.wm_overrideredirect(True)
        self.tipwindow.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tipwindow,
            text=self.text,
            justify=tk.LEFT,
            background="#fff8d6",
            relief=tk.SOLID,
            borderwidth=1,
            padx=8,
            pady=4,
            font=("Yu Gothic UI", 9),
        )
        label.pack()
        self._visible = True

    def _hide(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        self._cancel_schedule()
        if self.tipwindow is not None:
            self.tipwindow.destroy()
            self.tipwindow = None
        self._visible = False
