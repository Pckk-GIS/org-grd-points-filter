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
from .state import GuiState
from .view_model import build_app_config, default_state


class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("point-filter")
        self.root.geometry("840x560")

        self.message_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.run_button: ttk.Button | None = None

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
            form, 0, "Region CSV", self.region_csv_var, self._browse_region_csv
        )
        self._add_path_row(
            form, 1, "Input dir", self.input_dir_var, self._browse_input_dir
        )
        self._add_path_row(
            form, 2, "Output dir", self.output_dir_var, self._browse_output_dir
        )
        self._add_column_row(form, 3)

        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, pady=(12, 8))

        self.run_button = ttk.Button(actions, text="Run", command=self._on_run)
        self.run_button.pack(side=tk.LEFT)

        ttk.Button(actions, text="Clear log", command=self._clear_log).pack(
            side=tk.LEFT, padx=(8, 0)
        )

        ttk.Separator(container).pack(fill=tk.X, pady=(8, 8))

        log_frame = ttk.LabelFrame(container, text="Log")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log = scrolledtext.ScrolledText(log_frame, height=18, wrap=tk.WORD)
        self.log.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.log.configure(state="disabled")

    def _add_path_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        browse_command,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=4)
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky=tk.EW, padx=(8, 8), pady=4)
        ttk.Button(parent, text="Browse...", command=browse_command).grid(
            row=row, column=2, sticky=tk.E, pady=4
        )
        parent.columnconfigure(1, weight=1)

    def _add_column_row(self, parent: ttk.Frame, row: int) -> None:
        ttk.Label(parent, text="Columns").grid(row=row, column=0, sticky=tk.W, pady=4)
        columns = ttk.Frame(parent)
        columns.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=4)

        self._add_small_entry(columns, "X", self.x_col_var, 0)
        self._add_small_entry(columns, "Y", self.y_col_var, 1)
        self._add_small_entry(columns, "Z", self.z_col_var, 2)

    def _add_small_entry(
        self, parent: ttk.Frame, label: str, variable: tk.StringVar, column: int
    ) -> None:
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, padx=(0, 12))
        ttk.Label(frame, text=label).pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=variable, width=8).pack(side=tk.LEFT, padx=(6, 0))

    def _browse_region_csv(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Select region CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.region_csv_var.set(path)

    def _browse_input_dir(self) -> None:
        path = filedialog.askdirectory(parent=self.root, title="Select input directory")
        if path:
            self.input_dir_var.set(path)

    def _browse_output_dir(self) -> None:
        path = filedialog.askdirectory(
            parent=self.root, title="Select output directory"
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
            messagebox.showerror("point-filter", str(exc), parent=self.root)
            return

        self._append_log("Starting processing...")
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
                ("success", f"Finished. Output written to {config.output_dir}")
            )

    def _poll_messages(self) -> None:
        try:
            while True:
                kind, payload = self.message_queue.get_nowait()
                self._set_running(False)
                if kind == "success":
                    self._append_log(payload)
                    messagebox.showinfo("point-filter", payload, parent=self.root)
                else:
                    self._append_log(payload)
                    messagebox.showerror("point-filter", payload, parent=self.root)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._poll_messages)


def main() -> int:
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()
    return 0
