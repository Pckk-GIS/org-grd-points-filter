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
OPTIMIZATION_NOTICE_TITLE = "注意"
OPTIMIZATION_NOTICE = (
    "高速化のため、org/grd は同じ範囲前提で file_id 単位のスキップ判定を行います。"
    "前提が崩れたデータでは取りこぼしの可能性があります。"
)

REGION_CSV = LabeledText(
    label="領域CSV",
    tooltip="region_id,x,y 形式のCSVを指定します。ヘッダ行が必要で、複数領域を定義できます。",
)
INPUT_DIR = LabeledText(
    label="入力フォルダ",
    tooltip="org / grd の点群テキストを含むフォルダを指定します。",
)
OUTPUT_DIR = LabeledText(
    label="出力フォルダ",
    tooltip="抽出結果の出力先フォルダを指定します。",
)
ORG_COLS = LabeledText(
    label="org 列指定",
    tooltip="org 系ファイルの X列 / Y列 / Z列を1始まりで指定します。",
)
GRD_COLS = LabeledText(
    label="grd 列指定",
    tooltip="grd 系ファイルの X列 / Y列 / Z列を1始まりで指定します。",
)
ORG_X_COL = LabeledText(
    label="org X列",
    tooltip="org 系ファイルの X 座標列番号を1始まりで指定します。",
)
ORG_Y_COL = LabeledText(
    label="org Y列",
    tooltip="org 系ファイルの Y 座標列番号を1始まりで指定します。",
)
ORG_Z_COL = LabeledText(
    label="org Z列",
    tooltip="org 系ファイルの Z 座標列番号を1始まりで指定します。",
)
GRD_X_COL = LabeledText(
    label="grd X列",
    tooltip="grd 系ファイルの X 座標列番号を1始まりで指定します。",
)
GRD_Y_COL = LabeledText(
    label="grd Y列",
    tooltip="grd 系ファイルの Y 座標列番号を1始まりで指定します。",
)
GRD_Z_COL = LabeledText(
    label="grd Z列",
    tooltip="grd 系ファイルの Z 座標列番号を1始まりで指定します。",
)

RUN_BUTTON = "実行"
CLEAR_LOG_BUTTON = "ログ消去"
SELECT_BUTTON = "参照..."
REFRESH_PREVIEW_BUTTON = "プレビュー更新"
LOG_FRAME = "ログ"
PREVIEW_FRAME = "入力プレビュー"
ORG_PREVIEW = "org 先頭5行"
GRD_PREVIEW = "grd 先頭5行"
PREVIEW_EMPTY = "対象ファイルが見つかりません。"

RUN_BUTTON_TOOLTIP = "入力内容をもとに抽出処理を実行します。"
CLEAR_LOG_TOOLTIP = "画面下部のログ表示を消去します。"
SELECT_BUTTON_TOOLTIP = "ファイル選択ダイアログを開きます。"
REFRESH_PREVIEW_TOOLTIP = "入力フォルダから org / grd の先頭5行プレビューを更新します。"

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
STATUS_FILE_GROUP_SKIPPED = (
    "[{system}] スキップ: {file_id} ({path}) / 領域と交差しません"
)
STATUS_FILE_GROUP_SCAN_START = "[{system}] 事前確認開始: {file_id} ({path})"
STATUS_FILE_GROUP_SCAN_PROGRESS = (
    "[{system}] 事前確認中: {file_id} ({path}) ({records} 行処理済み)"
)
STATUS_FILE_GROUP_SCAN_DONE = "[{system}] 事前確認完了: {file_id} ({path})"
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
STATUS_PREVIEW_UPDATED = "入力プレビューを更新しました。"
STATUS_PREVIEW_ERROR = "入力プレビューを更新できませんでした: {error}"

INFO_TITLE = "点群抽出"
ERROR_TITLE = "点群抽出"
