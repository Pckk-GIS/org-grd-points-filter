from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LabeledText:
    label: str
    tooltip: str


WINDOW_TITLE = "点群抽出"
WINDOW_GEOMETRY = "840x560"
HELP_WINDOW_TITLE = "使い方"
HELP_MENU = "ヘルプ"
HELP_MENU_USAGE = "使い方"
HELP_MENU_EXIT = "終了"

REGION_CSV = LabeledText(
    label="領域CSV",
    tooltip="region_id,x,y 形式のCSVを指定します。ヘッダ行が必要で、3 領域分の定義を入れます。",
)
INPUT_DIR = LabeledText(
    label="入力フォルダ",
    tooltip="org / grd の点群テキストを含むフォルダを指定します。",
)
OUTPUT_DIR = LabeledText(
    label="出力フォルダ",
    tooltip="抽出結果の出力先フォルダを指定します。",
)
COLS = LabeledText(
    label="列指定",
    tooltip="X列 / Y列 / Z列を1始まりで指定します。ヘッダ行は不要です。",
)
X_COL = LabeledText(
    label="X列",
    tooltip="X座標の列番号を1始まりで指定します。",
)
Y_COL = LabeledText(
    label="Y列",
    tooltip="Y座標の列番号を1始まりで指定します。",
)
Z_COL = LabeledText(
    label="Z列",
    tooltip="Z座標の列番号を1始まりで指定します。",
)

RUN_BUTTON = "実行"
CLEAR_LOG_BUTTON = "ログ消去"
SELECT_BUTTON = "参照..."
LOG_FRAME = "ログ"

RUN_BUTTON_TOOLTIP = "入力内容をもとに抽出処理を実行します。"
CLEAR_LOG_TOOLTIP = "画面下部のログ表示を消去します。"
SELECT_BUTTON_TOOLTIP = "ファイル選択ダイアログを開きます。"

FILE_DIALOG_REGION_CSV = "領域CSVを選択"
FILE_DIALOG_INPUT_DIR = "入力フォルダを選択"
FILE_DIALOG_OUTPUT_DIR = "出力フォルダを選択"

STATUS_START = "処理を開始します。"
STATUS_SUCCESS = "処理が完了しました。"
STATUS_OUTPUT_WRITTEN = "出力先: {path}"

INFO_TITLE = "点群抽出"
ERROR_TITLE = "点群抽出"
