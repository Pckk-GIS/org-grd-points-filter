from dataclasses import dataclass


@dataclass(slots=True)
class GuiState:
    region_csv: str
    input_dir: str
    output_dir: str
    x_col: str
    y_col: str
    z_col: str
