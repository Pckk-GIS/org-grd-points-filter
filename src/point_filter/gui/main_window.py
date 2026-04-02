from __future__ import annotations

import queue
import threading
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from ..config import AppConfig
from ..filter_service import process
from ..output_writer import write_outputs
from ..validation import PointFilterError
from . import labels
from .state import GuiState
from .view_model import build_app_config, default_state
from .tooltip import ToolTip


class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(labels.WINDOW_TITLE)
        self.root.geometry(labels.WINDOW_GEOMETRY)

        self.message_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.run_button: ttk.Button | None = None
        self._tooltips: list[ToolTip] = []

        default = default_state()
        self.region_csv_var = tk.StringVar(value=default.region_csv)
        self.input_dir_var = tk.StringVar(value=default.input_dir)
        self.output_dir_var = tk.StringVar(value=default.output_dir)
        self.x_col_var = tk.StringVar(value=default.x_col)
        self.y_col_var = tk.StringVar(value=default.y_col)
        self.z_col_var = tk.StringVar(value=default.z_col)

        self._build_layout()
        self.root.after(100, self._poll_messages)

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        form = ttk.Frame(container)
        form.pack(fill=tk.X)

        self._add_path_row(
            form, 0, labels.REGION_CSV, self.region_csv_var, self._browse_region_csv
        )
        self._add_path_row(
            form, 1, labels.INPUT_DIR, self.input_dir_var, self._browse_input_dir
        )
        self._add_path_row(
            form, 2, labels.OUTPUT_DIR, self.output_dir_var, self._browse_output_dir
        )
        self._add_column_row(form, 3)

        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, pady=(12, 8))

        self.run_button = ttk.Button(
            actions, text=labels.RUN_BUTTON, command=self._on_run
        )
        self.run_button.pack(side=tk.LEFT)
        self._tooltips.append(ToolTip(self.run_button, labels.RUN_BUTTON_TOOLTIP))

        clear_button = ttk.Button(
            actions, text=labels.CLEAR_LOG_BUTTON, command=self._clear_log
        )
        clear_button.pack(side=tk.LEFT, padx=(8, 0))
        self._tooltips.append(ToolTip(clear_button, labels.CLEAR_LOG_TOOLTIP))

        ttk.Separator(container).pack(fill=tk.X, pady=(8, 8))

        log_frame = ttk.LabelFrame(container, text=labels.LOG_FRAME)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log = scrolledtext.ScrolledText(log_frame, height=18, wrap=tk.WORD)
        self.log.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.log.configure(state="disabled")

    def _add_path_row(
        self,
        parent: ttk.Frame,
        row: int,
        field: labels.LabeledText,
        variable: tk.StringVar,
        browse_command,
    ) -> None:
        label_widget = ttk.Label(parent, text=field.label)
        label_widget.grid(row=row, column=0, sticky=tk.W, pady=4)
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky=tk.EW, padx=(8, 8), pady=4)
        browse_button = ttk.Button(
            parent, text=labels.SELECT_BUTTON, command=browse_command
        )
        browse_button.grid(row=row, column=2, sticky=tk.E, pady=4)
        self._tooltips.append(ToolTip(label_widget, field.tooltip))
        self._tooltips.append(ToolTip(entry, field.tooltip))
        self._tooltips.append(ToolTip(browse_button, labels.SELECT_BUTTON_TOOLTIP))
        parent.columnconfigure(1, weight=1)

    def _add_column_row(self, parent: ttk.Frame, row: int) -> None:
        label_widget = ttk.Label(parent, text=labels.COLS.label)
        label_widget.grid(row=row, column=0, sticky=tk.W, pady=4)
        columns = ttk.Frame(parent)
        columns.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=4)
        self._tooltips.append(ToolTip(label_widget, labels.COLS.tooltip))

        self._add_small_entry(columns, labels.X_COL, self.x_col_var, 0)
        self._add_small_entry(columns, labels.Y_COL, self.y_col_var, 1)
        self._add_small_entry(columns, labels.Z_COL, self.z_col_var, 2)

    def _add_small_entry(
        self,
        parent: ttk.Frame,
        field: labels.LabeledText,
        variable: tk.StringVar,
        column: int,
    ) -> None:
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, padx=(0, 12))
        label_widget = ttk.Label(frame, text=field.label)
        label_widget.pack(side=tk.LEFT)
        entry = ttk.Entry(frame, textvariable=variable, width=8)
        entry.pack(side=tk.LEFT, padx=(6, 0))
        self._tooltips.append(ToolTip(label_widget, field.tooltip))
        self._tooltips.append(ToolTip(entry, field.tooltip))

    def _browse_region_csv(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root,
            title=labels.FILE_DIALOG_REGION_CSV,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.region_csv_var.set(path)

    def _browse_input_dir(self) -> None:
        path = filedialog.askdirectory(
            parent=self.root, title=labels.FILE_DIALOG_INPUT_DIR
        )
        if path:
            self.input_dir_var.set(path)

    def _browse_output_dir(self) -> None:
        path = filedialog.askdirectory(
            parent=self.root, title=labels.FILE_DIALOG_OUTPUT_DIR
        )
        if path:
            self.output_dir_var.set(path)

    def _clear_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", tk.END)
        self.log.configure(state="disabled")

    def _append_log(self, message: str) -> None:
        self.log.configure(state="normal")
        self.log.insert(tk.END, f"{message}\n")
        self.log.see(tk.END)
        self.log.configure(state="disabled")

    def _current_state(self) -> GuiState:
        return GuiState(
            region_csv=self.region_csv_var.get().strip(),
            input_dir=self.input_dir_var.get().strip(),
            output_dir=self.output_dir_var.get().strip(),
            x_col=self.x_col_var.get().strip(),
            y_col=self.y_col_var.get().strip(),
            z_col=self.z_col_var.get().strip(),
        )

    def _set_running(self, running: bool) -> None:
        if self.run_button is not None:
            self.run_button.configure(state=tk.DISABLED if running else tk.NORMAL)

    def _on_run(self) -> None:
        try:
            config = build_app_config(self._current_state())
        except PointFilterError as exc:
            messagebox.showerror(labels.ERROR_TITLE, str(exc), parent=self.root)
            return

        self._append_log(labels.STATUS_START)
        self._set_running(True)

        thread = threading.Thread(target=self._worker, args=(config,), daemon=True)
        thread.start()

    def _worker(self, config: AppConfig) -> None:
        try:
            buckets = process(config)
            write_outputs(config.output_dir, buckets)
        except Exception as exc:  # pragma: no cover - forwarded to UI
            self.message_queue.put(("error", f"{exc}\n{traceback.format_exc()}"))
        else:
            self.message_queue.put(
                (
                    "success",
                    "\n".join(
                        [
                            labels.STATUS_SUCCESS,
                            labels.STATUS_OUTPUT_WRITTEN.format(path=config.output_dir),
                        ]
                    ),
                )
            )

    def _poll_messages(self) -> None:
        try:
            while True:
                kind, payload = self.message_queue.get_nowait()
                self._set_running(False)
                if kind == "success":
                    self._append_log(payload)
                    messagebox.showinfo(labels.INFO_TITLE, payload, parent=self.root)
                else:
                    self._append_log(payload)
                    messagebox.showerror(labels.ERROR_TITLE, payload, parent=self.root)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._poll_messages)


def main() -> int:
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()
    return 0
