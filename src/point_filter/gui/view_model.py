from __future__ import annotations

from pathlib import Path

from ..config import AppConfig
from ..validation import ConfigurationError
from .state import GuiState


DEFAULT_REGION_CSV = "data/regions.csv"
DEFAULT_INPUT_DIR = "input"
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_X_COL = "2"
DEFAULT_Y_COL = "3"
DEFAULT_Z_COL = "4"


def default_state() -> GuiState:
    return GuiState(
        region_csv=DEFAULT_REGION_CSV,
        input_dir=DEFAULT_INPUT_DIR,
        output_dir=DEFAULT_OUTPUT_DIR,
        x_col=DEFAULT_X_COL,
        y_col=DEFAULT_Y_COL,
        z_col=DEFAULT_Z_COL,
    )


def _parse_positive_int(value: str, label: str) -> int:
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
    return AppConfig(
        region_csv=Path(state.region_csv),
        input_dir=Path(state.input_dir),
        output_dir=Path(state.output_dir),
        x_col=_parse_positive_int(state.x_col, "X"),
        y_col=_parse_positive_int(state.y_col, "Y"),
        z_col=_parse_positive_int(state.z_col, "Z"),
    )
