"""GUI のメインウィンドウを構成する。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import queue
import threading
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import cast

from ..config import AppConfig
from ..filter_service import process
from ..validation import PointFilterError
from . import labels
from .help_window import HelpWindow
from .state import GuiState
from .view_model import build_app_config, default_state
from .tooltip import ToolTip


class MainWindow:
    """GUI の 1 画面完結ウィンドウを構成する。"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(labels.WINDOW_TITLE)
        self.root.geometry(labels.WINDOW_GEOMETRY)

        self.message_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.run_button: ttk.Button | None = None
        self._tooltips: list[ToolTip] = []
        self._help_window: HelpWindow | None = None

        default = default_state()
        self.region_csv_var = tk.StringVar(value=default.region_csv)
        self.input_dir_var = tk.StringVar(value=default.input_dir)
        self.output_dir_var = tk.StringVar(value=default.output_dir)
        self.x_col_var = tk.StringVar(value=default.x_col)
        self.y_col_var = tk.StringVar(value=default.y_col)
        self.z_col_var = tk.StringVar(value=default.z_col)

        self._build_layout()
        self._build_menu()
        self._append_log("GUI を起動しました。")
        self.root.after(100, self._poll_messages)

    def _build_menu(self) -> None:
        menu = tk.Menu(self.root)
        help_menu = tk.Menu(menu, tearoff=False)
        help_menu.add_command(label=labels.HELP_MENU_USAGE, command=self._open_help)
        help_menu.add_separator()
        help_menu.add_command(label=labels.HELP_MENU_EXIT, command=self.root.destroy)
        menu.add_cascade(label=labels.HELP_MENU, menu=help_menu)
        self.root.config(menu=menu)

    def _open_help(self) -> None:
        if self._help_window is not None and self._help_window.winfo_exists():
            self._help_window.lift()
            self._help_window.focus_force()
            return

        self._help_window = HelpWindow(self.root)
        self._help_window.protocol("WM_DELETE_WINDOW", self._close_help_window)

    def _close_help_window(self) -> None:
        if self._help_window is not None:
            self._help_window.destroy()
            self._help_window = None

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
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.configure(state="normal")
        self.log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log.see(tk.END)
        self.log.configure(state="disabled")

    def _format_match_summary(self, matches: dict[int, int]) -> str:
        parts = [
            f"region{ordinal}={count}" for ordinal, count in sorted(matches.items())
        ]
        return ", ".join(parts)

    def _handle_progress(self, event: str, payload: dict[str, object]) -> None:
        if event == "regions_loaded":
            region_count = cast(int, payload["region_count"])
            self.message_queue.put(
                (
                    "log",
                    labels.STATUS_REGIONS_LOADED.format(region_count=region_count),
                )
            )
            return

        if event == "input_scan":
            org_files = cast(int, payload["org_files"])
            grd_files = cast(int, payload["grd_files"])
            total_files = cast(int, payload["total_files"])
            self.message_queue.put(
                (
                    "log",
                    labels.STATUS_INPUT_SCAN.format(
                        org_count=org_files,
                        grd_count=grd_files,
                        total_count=total_files,
                    ),
                )
            )
            return

        if event == "file_start":
            system = cast(str, payload["system"])
            path = cast(Path, payload["path"])
            index = cast(int, payload["index"])
            total = cast(int, payload["total"])
            self.message_queue.put(
                (
                    "log",
                    labels.STATUS_FILE_START.format(
                        system=system,
                        path=path.name,
                        index=index,
                        total=total,
                    ),
                )
            )
            return

        if event == "file_progress":
            system = cast(str, payload["system"])
            path = cast(Path, payload["path"])
            records = cast(int, payload["records"])
            self.message_queue.put(
                (
                    "log",
                    labels.STATUS_FILE_PROGRESS.format(
                        system=system,
                        path=path.name,
                        records=records,
                    ),
                )
            )
            return

        if event == "file_skipped":
            system = cast(str, payload["system"])
            path = cast(Path, payload["path"])
            reason = cast(str, payload["reason"])
            self.message_queue.put(
                (
                    "log",
                    labels.STATUS_FILE_SKIPPED.format(
                        system=system,
                        path=path.name,
                        reason=reason,
                    ),
                )
            )
            return

        if event == "file_done":
            system = cast(str, payload["system"])
            path = cast(Path, payload["path"])
            index = cast(int, payload["index"])
            total = cast(int, payload["total"])
            records = cast(int, payload["records"])
            matches = cast(dict[int, int], payload["matches"])
            self.message_queue.put(
                (
                    "log",
                    labels.STATUS_FILE_DONE.format(
                        system=system,
                        path=path.name,
                        index=index,
                        total=total,
                        records=records,
                        matches=self._format_match_summary(matches),
                    ),
                )
            )

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
            self._append_log(f"設定エラー: {exc}")
            messagebox.showerror(labels.ERROR_TITLE, str(exc), parent=self.root)
            return

        self._append_log(labels.STATUS_START)
        self._append_log(labels.STATUS_CONFIG_READY)
        self._append_log(
            "設定: "
            f"領域CSV={config.region_csv}, "
            f"入力フォルダ={config.input_dir}, "
            f"出力フォルダ={config.output_dir}, "
            f"X={config.x_col}, Y={config.y_col}, Z={config.z_col}"
        )
        self._set_running(True)

        thread = threading.Thread(target=self._worker, args=(config,), daemon=True)
        thread.start()

    def _worker(self, config: AppConfig) -> None:
        try:
            report = process(config, progress_callback=self._handle_progress)
            self.message_queue.put(("log", labels.STATUS_OUTPUT_START))
            for system, region_map in report.output_counts.items():
                for ordinal, count in region_map.items():
                    output_path = config.output_dir / f"{system}_region{ordinal}.txt"
                    self.message_queue.put(
                        (
                            "log",
                            labels.STATUS_OUTPUT_FILE.format(
                                path=output_path,
                                count=count,
                            ),
                        )
                    )
            self.message_queue.put(("log", labels.STATUS_OUTPUT_DONE))
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
                if kind == "log":
                    self._append_log(payload)
                elif kind == "success":
                    self._set_running(False)
                    self._append_log(payload)
                    messagebox.showinfo(labels.INFO_TITLE, payload, parent=self.root)
                else:
                    self._set_running(False)
                    self._append_log(payload)
                    messagebox.showerror(labels.ERROR_TITLE, payload, parent=self.root)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._poll_messages)


def main() -> int:
    """GUI アプリケーションを起動する。"""
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()
    return 0
