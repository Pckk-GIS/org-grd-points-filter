"""GUI の表示文言をまとめる。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LabeledText:
    """画面ラベルとツールチップをひとまとめにした値。"""

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
STATUS_CONFIG_READY = "設定を確認しました。"
STATUS_REGIONS_LOADED = "領域CSVを読み込みました: {region_count} 領域"
STATUS_INPUT_SCAN = (
    "入力ファイルを確認しました: org={org_count} 件, grd={grd_count} 件, "
    "合計={total_count} 件"
)
STATUS_FILE_START = "[{system}] 読み込み開始: {path} ({index}/{total})"
STATUS_FILE_PROGRESS = "[{system}] 読み込み中: {path} ({records} 行処理済み)"
STATUS_FILE_DONE = (
    "[{system}] 読み込み完了: {path} ({index}/{total}, {records} 行, {matches} 件抽出)"
)
STATUS_OUTPUT_START = "出力ファイルを書き出します。"
STATUS_OUTPUT_FILE = "出力: {path} ({count} 行)"
STATUS_OUTPUT_DONE = "出力ファイルの書き出しが完了しました。"
STATUS_SUCCESS = "処理が完了しました。"
STATUS_OUTPUT_WRITTEN = "出力先: {path}"

INFO_TITLE = "点群抽出"
ERROR_TITLE = "点群抽出"
