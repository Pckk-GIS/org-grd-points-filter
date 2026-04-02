"""GUI で入力欄に保持する状態を定義する。"""

from dataclasses import dataclass


@dataclass(slots=True)
class GuiState:
    """画面の入力値を文字列のまま保持する。"""

    region_csv: str
    input_dir: str
    output_dir: str
    x_col: str
    y_col: str
    z_col: str
