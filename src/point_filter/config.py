from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    region_csv: Path
    input_dir: Path
    output_dir: Path
    x_col: int
    y_col: int
    z_col: int
