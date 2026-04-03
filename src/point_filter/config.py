"""CLI と GUI で共有する設定値を定義する。"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    """点群抽出に必要な設定をまとめた値オブジェクト。"""

    region_csv: Path
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
