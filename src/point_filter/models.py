from dataclasses import dataclass
from pathlib import Path
from typing import Literal


InputSystem = Literal["org", "grd"]


@dataclass(frozen=True, slots=True)
class Point2D:
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class Region:
    ordinal: int
    region_id: str
    vertices: tuple[Point2D, ...]


@dataclass(frozen=True, slots=True)
class PointRecord:
    raw_line: str
    fields: tuple[str, ...]
    x: float
    y: float
    z: float
    source_file: Path
    line_number: int
    system: InputSystem
