"""GUI で入力欄に保持する状態を定義する。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class GuiRegionInput:
    """GUI 上の 1 件の領域入力を表す。"""

    path: str
    layer: str = ""


@dataclass(slots=True)
class GuiState:
    """画面の入力値を文字列のまま保持する。"""

    region_inputs: list[GuiRegionInput]
    input_dir: str
    output_dir: str
    org_x_col: str
    org_y_col: str
    org_z_col: str
    grd_x_col: str
    grd_y_col: str
    grd_z_col: str
