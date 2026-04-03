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

from ..config import AppConfig, RegionInput
from ..filter_service import process
from ..point_reader import find_preview_file, read_preview_lines
from ..region_loader import list_gpkg_layers, summarize_region_input
from ..validation import PointFilterError
from . import labels
from .help_window import HelpWindow
from .state import GuiRegionInput, GuiState
from .tooltip import ToolTip
from .view_model import build_app_config, default_state


class MainWindow:
    """GUI の 1 画面完結ウィンドウを構成する。"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(labels.WINDOW_TITLE)
        self.root.geometry(labels.WINDOW_GEOMETRY)

        self.message_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.run_button: ttk.Button | None = None
        self.region_listbox: tk.Listbox | None = None
        self.layer_combo: ttk.Combobox | None = None
        self.layer_var = tk.StringVar(value=labels.LAYER_EMPTY)
        self.region_summary_var = tk.StringVar(value=labels.REGION_SUMMARY_EMPTY)
        self._tooltips: list[ToolTip] = []
        self._help_window: HelpWindow | None = None
        self._region_inputs: list[GuiRegionInput] = list(default_state().region_inputs)

        default = default_state()
        self.input_dir_var = tk.StringVar(value=default.input_dir)
        self.output_dir_var = tk.StringVar(value=default.output_dir)
        self.org_x_col_var = tk.StringVar(value=default.org_x_col)
        self.org_y_col_var = tk.StringVar(value=default.org_y_col)
        self.org_z_col_var = tk.StringVar(value=default.org_z_col)
        self.grd_x_col_var = tk.StringVar(value=default.grd_x_col)
        self.grd_y_col_var = tk.StringVar(value=default.grd_y_col)
        self.grd_z_col_var = tk.StringVar(value=default.grd_z_col)
        self.org_preview: scrolledtext.ScrolledText | None = None
        self.grd_preview: scrolledtext.ScrolledText | None = None

        self._build_layout()
        self._build_menu()
        self._refresh_region_list()
        self._append_log(labels.STATUS_GUI_STARTED)
        self._refresh_preview(log_result=False)
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

        notice_frame = ttk.LabelFrame(container, text=labels.OPTIMIZATION_NOTICE_TITLE)
        notice_frame.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(
            notice_frame,
            text=labels.OPTIMIZATION_NOTICE,
            wraplength=780,
            justify=tk.LEFT,
        ).pack(fill=tk.X, padx=8, pady=8)

        region_frame = ttk.LabelFrame(container, text=labels.REGION_FRAME)
        region_frame.pack(fill=tk.X, pady=(0, 12))
        self._build_region_inputs(region_frame)

        form = ttk.Frame(container)
        form.pack(fill=tk.X)

        self._add_path_row(
            form, 0, labels.INPUT_DIR, self.input_dir_var, self._browse_input_dir
        )
        self._add_path_row(
            form, 1, labels.OUTPUT_DIR, self.output_dir_var, self._browse_output_dir
        )
        self._add_column_row(
            form,
            2,
            labels.ORG_COLS,
            labels.ORG_X_COL,
            labels.ORG_Y_COL,
            labels.ORG_Z_COL,
            self.org_x_col_var,
            self.org_y_col_var,
            self.org_z_col_var,
        )
        self._add_column_row(
            form,
            3,
            labels.GRD_COLS,
            labels.GRD_X_COL,
            labels.GRD_Y_COL,
            labels.GRD_Z_COL,
            self.grd_x_col_var,
            self.grd_y_col_var,
            self.grd_z_col_var,
        )

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

        refresh_button = ttk.Button(
            actions,
            text=labels.REFRESH_PREVIEW_BUTTON,
            command=self._on_refresh_preview,
        )
        refresh_button.pack(side=tk.LEFT, padx=(8, 0))
        self._tooltips.append(ToolTip(refresh_button, labels.REFRESH_PREVIEW_TOOLTIP))

        ttk.Separator(container).pack(fill=tk.X, pady=(8, 8))

        preview_frame = ttk.LabelFrame(container, text=labels.PREVIEW_FRAME)
        preview_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 8))
        preview_columns = ttk.Frame(preview_frame)
        preview_columns.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        preview_columns.columnconfigure(0, weight=1)
        preview_columns.columnconfigure(1, weight=1)

        self.org_preview = self._build_preview_panel(
            preview_columns, 0, labels.ORG_PREVIEW
        )
        self.grd_preview = self._build_preview_panel(
            preview_columns, 1, labels.GRD_PREVIEW
        )

        log_frame = ttk.LabelFrame(container, text=labels.LOG_FRAME)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log = scrolledtext.ScrolledText(log_frame, height=18, wrap=tk.WORD)
        self.log.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.log.configure(state="disabled")

    def _build_region_inputs(self, parent: ttk.LabelFrame) -> None:
        parent.columnconfigure(0, weight=1)

        list_frame = ttk.Frame(parent)
        list_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=8, pady=8)
        list_frame.columnconfigure(1, weight=1)

        label_widget = ttk.Label(list_frame, text=labels.REGION_FILE.label)
        label_widget.grid(row=0, column=0, sticky=tk.W)
        self._tooltips.append(ToolTip(label_widget, labels.REGION_FILE.tooltip))

        summary_label = tk.Label(
            list_frame,
            textvariable=self.region_summary_var,
            anchor="e",
            justify=tk.RIGHT,
            fg="gray40",
        )
        summary_label.grid(row=0, column=1, sticky=tk.E, padx=(12, 0))

        self.region_listbox = tk.Listbox(list_frame, height=5, exportselection=False)
        self.region_listbox.grid(row=1, column=0, columnspan=2, sticky=tk.EW)
        self.region_listbox.bind("<<ListboxSelect>>", self._on_region_select)

        button_frame = ttk.Frame(parent)
        button_frame.grid(row=0, column=1, sticky=tk.N, padx=(0, 8), pady=8)

        add_button = ttk.Button(
            button_frame, text=labels.ADD_REGION_BUTTON, command=self._add_region_files
        )
        add_button.pack(fill=tk.X)
        remove_button = ttk.Button(
            button_frame,
            text=labels.REMOVE_REGION_BUTTON,
            command=self._remove_selected_region,
        )
        remove_button.pack(fill=tk.X, pady=(6, 0))
        up_button = ttk.Button(
            button_frame, text=labels.MOVE_UP_BUTTON, command=self._move_region_up
        )
        up_button.pack(fill=tk.X, pady=(6, 0))
        down_button = ttk.Button(
            button_frame, text=labels.MOVE_DOWN_BUTTON, command=self._move_region_down
        )
        down_button.pack(fill=tk.X, pady=(6, 0))

        self._tooltips.extend(
            [
                ToolTip(add_button, labels.ADD_REGION_TOOLTIP),
                ToolTip(remove_button, labels.REMOVE_REGION_TOOLTIP),
                ToolTip(up_button, labels.MOVE_UP_TOOLTIP),
                ToolTip(down_button, labels.MOVE_DOWN_TOOLTIP),
            ]
        )

        layer_frame = ttk.Frame(parent)
        layer_frame.grid(
            row=1, column=0, columnspan=2, sticky=tk.EW, padx=8, pady=(0, 8)
        )
        layer_label = ttk.Label(layer_frame, text=labels.REGION_LAYER.label)
        layer_label.pack(side=tk.LEFT)
        self.layer_combo = ttk.Combobox(
            layer_frame,
            textvariable=self.layer_var,
            state="disabled",
            width=48,
        )
        self.layer_combo.pack(side=tk.LEFT, padx=(8, 0), fill=tk.X, expand=True)
        self.layer_combo.bind("<<ComboboxSelected>>", self._on_layer_selected)
        self._tooltips.append(ToolTip(layer_label, labels.REGION_LAYER.tooltip))
        self._tooltips.append(ToolTip(self.layer_combo, labels.REGION_LAYER.tooltip))

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

    def _add_column_row(
        self,
        parent: ttk.Frame,
        row: int,
        group_field: labels.LabeledText,
        x_field: labels.LabeledText,
        y_field: labels.LabeledText,
        z_field: labels.LabeledText,
        x_var: tk.StringVar,
        y_var: tk.StringVar,
        z_var: tk.StringVar,
    ) -> None:
        label_widget = ttk.Label(parent, text=group_field.label)
        label_widget.grid(row=row, column=0, sticky=tk.W, pady=4)
        columns = ttk.Frame(parent)
        columns.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=4)
        self._tooltips.append(ToolTip(label_widget, group_field.tooltip))

        self._add_small_entry(columns, x_field, x_var, 0)
        self._add_small_entry(columns, y_field, y_var, 1)
        self._add_small_entry(columns, z_field, z_var, 2)

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

    def _build_preview_panel(
        self, parent: ttk.Frame, column: int, title: str
    ) -> scrolledtext.ScrolledText:
        frame = ttk.LabelFrame(parent, text=title)
        frame.grid(
            row=0, column=column, sticky=tk.NSEW, padx=(0 if column == 0 else 8, 0)
        )
        text = scrolledtext.ScrolledText(frame, height=7, wrap=tk.NONE)
        text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        text.configure(state="disabled")
        return text

    def _add_region_files(self) -> None:
        paths = filedialog.askopenfilenames(
            parent=self.root,
            title=labels.FILE_DIALOG_REGION_FILE,
            filetypes=[
                ("Region files", "*.csv *.shp *.gpkg"),
                ("CSV files", "*.csv"),
                ("Shapefile", "*.shp"),
                ("GeoPackage", "*.gpkg"),
                ("All files", "*.*"),
            ],
        )
        for raw_path in paths:
            region_input = GuiRegionInput(path=raw_path)
            if raw_path.lower().endswith(".gpkg"):
                layers = self._safe_list_layers(Path(raw_path))
                if len(layers) == 1:
                    region_input.layer = layers[0]
                    self._append_log(
                        labels.STATUS_REGION_LAYER_SINGLE.format(
                            path=Path(raw_path).name,
                            layer=layers[0],
                        )
                    )
            self._region_inputs.append(region_input)
            self._append_log(
                labels.STATUS_REGION_FILE_ADDED.format(path=Path(raw_path).name)
            )
        self._refresh_region_list(select_index=len(self._region_inputs) - 1)

    def _remove_selected_region(self) -> None:
        index = self._selected_region_index()
        if index is None:
            return
        removed = self._region_inputs.pop(index)
        self._append_log(
            labels.STATUS_REGION_FILE_REMOVED.format(path=Path(removed.path).name)
        )
        self._refresh_region_list(select_index=max(0, index - 1))

    def _move_region_up(self) -> None:
        index = self._selected_region_index()
        if index is None or index == 0:
            return
        self._region_inputs[index - 1], self._region_inputs[index] = (
            self._region_inputs[index],
            self._region_inputs[index - 1],
        )
        self._refresh_region_list(select_index=index - 1)

    def _move_region_down(self) -> None:
        index = self._selected_region_index()
        if index is None or index >= len(self._region_inputs) - 1:
            return
        self._region_inputs[index + 1], self._region_inputs[index] = (
            self._region_inputs[index],
            self._region_inputs[index + 1],
        )
        self._refresh_region_list(select_index=index + 1)

    def _refresh_region_list(self, select_index: int | None = None) -> None:
        if self.region_listbox is None:
            return
        self.region_listbox.delete(0, tk.END)
        for region_input in self._region_inputs:
            suffix = ""
            if region_input.layer:
                suffix = f" [{region_input.layer}]"
            self.region_listbox.insert(tk.END, f"{region_input.path}{suffix}")

        if self._region_inputs:
            if select_index is None:
                select_index = 0
            select_index = min(max(select_index, 0), len(self._region_inputs) - 1)
            self.region_listbox.selection_clear(0, tk.END)
            self.region_listbox.selection_set(select_index)
        self._sync_layer_controls()

    def _selected_region_index(self) -> int | None:
        if self.region_listbox is None:
            return None
        selection = self.region_listbox.curselection()
        if not selection:
            return None
        return int(selection[0])

    def _sync_layer_controls(self) -> None:
        if self.layer_combo is None:
            return
        index = self._selected_region_index()
        if index is None:
            self.layer_var.set(labels.LAYER_EMPTY)
            self.layer_combo.configure(values=(), state="disabled")
            self.region_summary_var.set(labels.REGION_SUMMARY_EMPTY)
            return

        region_input = self._region_inputs[index]
        path = Path(region_input.path)
        if path.suffix.lower() != ".gpkg":
            self.layer_var.set(labels.LAYER_EMPTY)
            self.layer_combo.configure(values=(), state="disabled")
            self._update_region_summary(region_input)
            return

        layers = self._safe_list_layers(path)
        if not layers:
            self.layer_var.set(labels.LAYER_EMPTY)
            self.layer_combo.configure(values=(), state="disabled")
            self._update_region_summary(region_input)
            return
        if len(layers) == 1:
            region_input.layer = layers[0]
            self.layer_var.set(layers[0])
            self.layer_combo.configure(values=layers, state="disabled")
            self._update_region_summary(region_input)
            return

        if region_input.layer not in layers:
            region_input.layer = layers[0]
        self.layer_var.set(region_input.layer)
        self.layer_combo.configure(values=layers, state="readonly")
        self._update_region_summary(region_input)

    def _safe_list_layers(self, path: Path) -> list[str]:
        try:
            return list_gpkg_layers(path)
        except Exception as exc:
            self._append_log(labels.STATUS_REGION_LAYER_ERROR.format(error=exc))
            return []

    def _on_layer_selected(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        index = self._selected_region_index()
        if index is None:
            return
        region_input = self._region_inputs[index]
        region_input.layer = self.layer_var.get().strip()
        self._update_region_summary(region_input)
        self._append_log(
            labels.STATUS_REGION_LAYER_SELECTED.format(
                path=Path(region_input.path).name,
                layer=region_input.layer,
            )
        )
        self._refresh_region_list(select_index=index)

    def _on_region_select(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        self._sync_layer_controls()

    def _update_region_summary(self, region_input: GuiRegionInput) -> None:
        try:
            summary = summarize_region_input(
                RegionInput(
                    path=Path(region_input.path), layer=region_input.layer or None
                )
            )
        except Exception as exc:
            summary = labels.STATUS_REGION_SUMMARY_ERROR.format(error=exc)
        self.region_summary_var.set(summary)

    def _browse_input_dir(self) -> None:
        path = filedialog.askdirectory(
            parent=self.root, title=labels.FILE_DIALOG_INPUT_DIR
        )
        if path:
            self.input_dir_var.set(path)
            self._refresh_preview(log_result=True)

    def _browse_output_dir(self) -> None:
        path = filedialog.askdirectory(
            parent=self.root, title=labels.FILE_DIALOG_OUTPUT_DIR
        )
        if path:
            self.output_dir_var.set(path)

    def _set_preview_text(
        self, widget: scrolledtext.ScrolledText | None, lines: list[str]
    ) -> None:
        if widget is None:
            return
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, "\n".join(lines) if lines else labels.PREVIEW_EMPTY)
        widget.configure(state="disabled")

    def _refresh_preview(self, *, log_result: bool) -> None:
        try:
            input_dir = Path(self.input_dir_var.get().strip())
            if not input_dir.exists():
                self._set_preview_text(self.org_preview, [])
                self._set_preview_text(self.grd_preview, [])
                return

            org_file = find_preview_file(input_dir, "org")
            grd_file = find_preview_file(input_dir, "grd")
            self._set_preview_text(
                self.org_preview,
                read_preview_lines(org_file) if org_file is not None else [],
            )
            self._set_preview_text(
                self.grd_preview,
                read_preview_lines(grd_file) if grd_file is not None else [],
            )
            if log_result:
                self._append_log(labels.STATUS_PREVIEW_UPDATED)
        except Exception as exc:  # pragma: no cover - UI fallback
            self._set_preview_text(self.org_preview, [])
            self._set_preview_text(self.grd_preview, [])
            if log_result:
                self._append_log(labels.STATUS_PREVIEW_ERROR.format(error=exc))

    def _on_refresh_preview(self) -> None:
        self._refresh_preview(log_result=True)

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

    def _format_match_summary(self, matches: dict[str, int]) -> str:
        parts = [
            f"region{region_id}: {count} 件"
            for region_id, count in sorted(matches.items(), key=lambda item: item[0])
        ]
        return ", ".join(parts)

    def _format_user_error(self, exc: Exception) -> str:
        message = str(exc).strip()
        if "must be specified" in message:
            return "領域ファイルが指定されていません。抽出範囲を定義したファイルを1つ以上追加してください。"
        if "column index must be an integer" in message:
            return "列番号は数字で入力してください。"
        if "column index must be 1 or greater" in message:
            return "列番号は 1 以上で入力してください。"
        if "GPKG layer not found" in message:
            return "指定したレイヤが見つかりません。GeoPackage に含まれるレイヤ名を確認してください。"
        if "Region CSV header must be" in message:
            return "CSV の先頭行が正しくありません。`region_id,x,y` の順で見出しを付けてください。"
        if "Only Polygon is supported" in message:
            return "領域ファイルには Polygon だけを含めてください。MultiPolygon や線・点は使えません。"
        if "Failed to read GPKG layers" in message:
            return "GeoPackage のレイヤ一覧を読み取れませんでした。ファイルが壊れていないか確認してください。"
        return message or labels.STATUS_RUNTIME_ERROR

    def _handle_progress(self, event: str, payload: dict[str, object]) -> None:
        if event == "region_file_loaded":
            layer = cast(str | None, payload["layer"])
            geometry_type = cast(str | None, payload["geometry_type"])
            layer_suffix = "" if not layer else f" / レイヤ: {layer}"
            geometry_suffix = "" if not geometry_type else f" / 扱い: {geometry_type}"
            self.message_queue.put(
                (
                    "log",
                    labels.STATUS_REGION_FILE_LOADED.format(
                        path=cast(Path, payload["path"]).name,
                        format=cast(str, payload["format"]).upper(),
                        feature_count=cast(int, payload["feature_count"]),
                        region_count=cast(int, payload["region_count"]),
                        layer_suffix=layer_suffix,
                        geometry_suffix=geometry_suffix,
                    ),
                )
            )
            return

        if event == "warning":
            self.message_queue.put(
                (
                    "log",
                    labels.STATUS_WARNING.format(message=cast(str, payload["message"])),
                )
            )
            return

        if event == "regions_loaded":
            region_count = cast(int, payload["region_count"])
            self.message_queue.put(
                ("log", labels.STATUS_REGIONS_LOADED.format(region_count=region_count))
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

        if event == "file_group_skipped":
            self.message_queue.put(
                (
                    "log",
                    labels.STATUS_FILE_GROUP_SKIPPED.format(
                        system=cast(str, payload["system"]),
                        file_id=cast(str, payload["file_id"]),
                        path=cast(Path, payload["path"]).name,
                    ),
                )
            )
            return

        if event == "file_group_scan_start":
            self.message_queue.put(
                (
                    "log",
                    labels.STATUS_FILE_GROUP_SCAN_START.format(
                        system=cast(str, payload["system"]),
                        file_id=cast(str, payload["file_id"]),
                        path=cast(Path, payload["path"]).name,
                    ),
                )
            )
            return

        if event == "file_group_scan_progress":
            self.message_queue.put(
                (
                    "log",
                    labels.STATUS_FILE_GROUP_SCAN_PROGRESS.format(
                        system=cast(str, payload["system"]),
                        file_id=cast(str, payload["file_id"]),
                        path=cast(Path, payload["path"]).name,
                        records=cast(int, payload["records"]),
                    ),
                )
            )
            return

        if event == "file_group_scan_done":
            self.message_queue.put(
                (
                    "log",
                    labels.STATUS_FILE_GROUP_SCAN_DONE.format(
                        system=cast(str, payload["system"]),
                        file_id=cast(str, payload["file_id"]),
                        path=cast(Path, payload["path"]).name,
                    ),
                )
            )
            return

        if event == "file_start":
            self.message_queue.put(
                (
                    "log",
                    labels.STATUS_FILE_START.format(
                        system=cast(str, payload["system"]),
                        path=cast(Path, payload["path"]).name,
                        index=cast(int, payload["index"]),
                        total=cast(int, payload["total"]),
                    ),
                )
            )
            return

        if event == "file_progress":
            self.message_queue.put(
                (
                    "log",
                    labels.STATUS_FILE_PROGRESS.format(
                        system=cast(str, payload["system"]),
                        path=cast(Path, payload["path"]).name,
                        records=cast(int, payload["records"]),
                    ),
                )
            )
            return

        if event == "file_done":
            self.message_queue.put(
                (
                    "log",
                    labels.STATUS_FILE_DONE.format(
                        system=cast(str, payload["system"]),
                        path=cast(Path, payload["path"]).name,
                        index=cast(int, payload["index"]),
                        total=cast(int, payload["total"]),
                        records=cast(int, payload["records"]),
                        matches=self._format_match_summary(
                            cast(dict[str, int], payload["matches"])
                        ),
                    ),
                )
            )

    def _current_state(self) -> GuiState:
        return GuiState(
            region_inputs=[
                GuiRegionInput(path=item.path, layer=item.layer)
                for item in self._region_inputs
            ],
            input_dir=self.input_dir_var.get().strip(),
            output_dir=self.output_dir_var.get().strip(),
            org_x_col=self.org_x_col_var.get().strip(),
            org_y_col=self.org_y_col_var.get().strip(),
            org_z_col=self.org_z_col_var.get().strip(),
            grd_x_col=self.grd_x_col_var.get().strip(),
            grd_y_col=self.grd_y_col_var.get().strip(),
            grd_z_col=self.grd_z_col_var.get().strip(),
        )

    def _set_running(self, running: bool) -> None:
        if self.run_button is not None:
            self.run_button.configure(state=tk.DISABLED if running else tk.NORMAL)

    def _on_run(self) -> None:
        try:
            config = build_app_config(self._current_state())
        except PointFilterError as exc:
            friendly_message = self._format_user_error(exc)
            self._append_log(f"{labels.STATUS_CONFIG_ERROR} {friendly_message}")
            messagebox.showerror(labels.ERROR_TITLE, friendly_message, parent=self.root)
            return

        region_summary = ", ".join(
            (
                f"{region_input.path}"
                if region_input.layer is None
                else f"{region_input.path}[{region_input.layer}]"
            )
            for region_input in config.region_inputs
        )
        self._append_log(labels.STATUS_START)
        self._append_log(labels.STATUS_CONFIG_READY)
        self._append_log(
            labels.STATUS_CONFIG_SUMMARY.format(
                region_summary=region_summary,
                input_dir=config.input_dir,
                output_dir=config.output_dir,
                org_x=config.org_x_col,
                org_y=config.org_y_col,
                org_z=config.org_z_col,
                grd_x=config.grd_x_col,
                grd_y=config.grd_y_col,
                grd_z=config.grd_z_col,
            )
        )
        self._set_running(True)

        thread = threading.Thread(target=self._worker, args=(config,), daemon=True)
        thread.start()

    def _worker(self, config: AppConfig) -> None:
        try:
            report = process(config, progress_callback=self._handle_progress)
            self.message_queue.put(("log", labels.STATUS_OUTPUT_START))
            for system, region_map in report.output_counts.items():
                for region_id, count in region_map.items():
                    output_path = config.output_dir / f"{system}_region{region_id}.txt"
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
            friendly_message = self._format_user_error(exc)
            self.message_queue.put(
                (
                    "error",
                    f"{labels.STATUS_RUNTIME_ERROR}\n{friendly_message}\n\n{traceback.format_exc()}",
                )
            )
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
