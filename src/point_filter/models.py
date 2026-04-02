"""ドメインモデルを定義する。"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


InputSystem = Literal["org", "grd"]


@dataclass(frozen=True, slots=True)
class Point2D:
    """2 次元座標を表す。"""

    x: float
    y: float


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """軸平行な矩形範囲を表す。"""

    min_x: float
    max_x: float
    min_y: float
    max_y: float


@dataclass(frozen=True, slots=True)
class Region:
    """抽出対象の領域を表す。"""

    ordinal: int
    region_id: str
    vertices: tuple[Point2D, ...]
    bounding_box: BoundingBox


@dataclass(frozen=True, slots=True)
class PointRecord:
    """入力ファイルの 1 行分を表す。"""

    raw_line: str
    fields: tuple[str, ...]
    x: float
    y: float
    z: float
    source_file: Path
    line_number: int
    system: InputSystem
