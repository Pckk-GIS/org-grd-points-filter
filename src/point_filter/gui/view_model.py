"""GUI の入力状態をアプリ設定へ変換する。"""

from __future__ import annotations

from pathlib import Path

from ..config import AppConfig, RegionInput
from ..validation import ConfigurationError
from .state import GuiRegionInput, GuiState


DEFAULT_INPUT_DIR = "input"
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_ORG_X_COL = "2"
DEFAULT_ORG_Y_COL = "3"
DEFAULT_ORG_Z_COL = "4"
DEFAULT_GRD_X_COL = "2"
DEFAULT_GRD_Y_COL = "3"
DEFAULT_GRD_Z_COL = "4"


def default_state() -> GuiState:
    """GUI 起動時に使う既定値を返す。"""
    return GuiState(
        region_inputs=[GuiRegionInput(path="data/regions.csv")],
        input_dir=DEFAULT_INPUT_DIR,
        output_dir=DEFAULT_OUTPUT_DIR,
        org_x_col=DEFAULT_ORG_X_COL,
        org_y_col=DEFAULT_ORG_Y_COL,
        org_z_col=DEFAULT_ORG_Z_COL,
        grd_x_col=DEFAULT_GRD_X_COL,
        grd_y_col=DEFAULT_GRD_Y_COL,
        grd_z_col=DEFAULT_GRD_Z_COL,
    )


def _parse_positive_int(value: str, label: str) -> int:
    """1 以上の整数として列番号を解釈する。"""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigurationError(
            f"{label} column index must be an integer: {value!r}"
        ) from exc

    if parsed < 1:
        raise ConfigurationError(f"{label} column index must be 1 or greater: {parsed}")
    return parsed


def build_app_config(state: GuiState) -> AppConfig:
    """GUI の状態から共通設定オブジェクトを作る。"""
    region_inputs = tuple(_build_region_inputs(state.region_inputs))
    if not region_inputs:
        raise ConfigurationError("At least one region file must be specified")
    return AppConfig(
        region_inputs=region_inputs,
        input_dir=Path(state.input_dir),
        output_dir=Path(state.output_dir),
        org_x_col=_parse_positive_int(state.org_x_col, "org X"),
        org_y_col=_parse_positive_int(state.org_y_col, "org Y"),
        org_z_col=_parse_positive_int(state.org_z_col, "org Z"),
        grd_x_col=_parse_positive_int(state.grd_x_col, "grd X"),
        grd_y_col=_parse_positive_int(state.grd_y_col, "grd Y"),
        grd_z_col=_parse_positive_int(state.grd_z_col, "grd Z"),
    )


def _build_region_inputs(gui_inputs: list[GuiRegionInput]) -> list[RegionInput]:
    built: list[RegionInput] = []
    for gui_input in gui_inputs:
        path = gui_input.path.strip()
        if not path:
            continue
        built.append(
            RegionInput(path=Path(path), layer=gui_input.layer.strip() or None)
        )
    return built
