"""CLI と GUI で共有する設定値を定義する。"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    """点群抽出に必要な設定をまとめた値オブジェクト。"""

    region_csv: Path
    input_dir: Path
    output_dir: Path
    x_col: int
    y_col: int
    z_col: int
