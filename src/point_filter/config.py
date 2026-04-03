"""CLI と GUI で共有する設定値を定義する。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RegionInput:
    """1 件の領域定義入力を表す。"""

    path: Path
    layer: str | None = None


@dataclass(frozen=True, slots=True)
class AppConfig:
    """点群抽出に必要な設定をまとめた値オブジェクト。"""

    region_inputs: tuple[RegionInput, ...]
    input_dir: Path
    output_dir: Path
    org_x_col: int
    org_y_col: int
    org_z_col: int
    grd_x_col: int
    grd_y_col: int
    grd_z_col: int

    def columns_for(self, system: str) -> tuple[int, int, int]:
        """系統ごとの X / Y / Z 列を返す。"""
        if system == "org":
            return self.org_x_col, self.org_y_col, self.org_z_col
        if system == "grd":
            return self.grd_x_col, self.grd_y_col, self.grd_z_col
        raise ValueError(f"unknown system: {system}")

    @property
    def primary_region_input(self) -> RegionInput:
        """先頭の領域入力を返す。"""
        return self.region_inputs[0]
