"""GUI の表示文言をまとめる。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LabeledText:
    """画面ラベルとツールチップをひとまとめにした値。"""

    label: str
    tooltip: str


WINDOW_TITLE = "点群抽出"
WINDOW_GEOMETRY = "840x700"
HELP_WINDOW_TITLE = "使い方"
HELP_MENU = "ヘルプ"
HELP_MENU_USAGE = "使い方"
HELP_MENU_EXIT = "終了"
OPTIMIZATION_NOTICE_TITLE = "注意"
OPTIMIZATION_NOTICE = (
    "処理を速くするため、org と grd は同じ範囲を持つ前提で一部の判定を省略しています。"
    "前提が成り立たないデータでは、抽出漏れが起こる可能性があります。"
)

REGION_FILE = LabeledText(
    label="領域ファイル",
    tooltip="抽出したい範囲を定義したファイルを追加します。CSV、SHP、GPKG を複数追加できます。SHP と GPKG は 1 地物を 1 領域として扱います。",
)
REGION_LAYER = LabeledText(
    label="GPKG レイヤ",
    tooltip="GPKG を選んだときに使うレイヤです。レイヤが1つなら自動で決まり、複数ある場合だけ選択します。",
)
INPUT_DIR = LabeledText(
    label="入力フォルダ",
    tooltip="抽出元の点群テキストが入っているフォルダを指定します。`*_org.txt` と `*_grd.txt` を探します。",
)
OUTPUT_DIR = LabeledText(
    label="出力フォルダ",
    tooltip="抽出結果を書き出すフォルダです。実行時に自動で作成されます。",
)
ORG_COLS = LabeledText(
    label="org 列指定",
    tooltip="org ファイルで、X・Y・Z が入っている列番号を指定します。左から 1, 2, 3... と数えます。",
)
GRD_COLS = LabeledText(
    label="grd 列指定",
    tooltip="grd ファイルで、X・Y・Z が入っている列番号を指定します。左から 1, 2, 3... と数えます。",
)
ORG_X_COL = LabeledText(
    label="org X列",
    tooltip="org ファイルで X 座標が入っている列番号を指定します。",
)
ORG_Y_COL = LabeledText(
    label="org Y列",
    tooltip="org ファイルで Y 座標が入っている列番号を指定します。",
)
ORG_Z_COL = LabeledText(
    label="org Z列",
    tooltip="org ファイルで Z 値が入っている列番号を指定します。",
)
GRD_X_COL = LabeledText(
    label="grd X列",
    tooltip="grd ファイルで X 座標が入っている列番号を指定します。",
)
GRD_Y_COL = LabeledText(
    label="grd Y列",
    tooltip="grd ファイルで Y 座標が入っている列番号を指定します。",
)
GRD_Z_COL = LabeledText(
    label="grd Z列",
    tooltip="grd ファイルで Z 値が入っている列番号を指定します。",
)

RUN_BUTTON = "実行"
CLEAR_LOG_BUTTON = "ログ消去"
SELECT_BUTTON = "参照..."
ADD_REGION_BUTTON = "追加..."
REMOVE_REGION_BUTTON = "削除"
MOVE_UP_BUTTON = "上へ"
MOVE_DOWN_BUTTON = "下へ"
REFRESH_PREVIEW_BUTTON = "プレビュー更新"
LOG_FRAME = "ログ"
PREVIEW_FRAME = "入力プレビュー"
REGION_FRAME = "領域定義"
ORG_PREVIEW = "org 先頭5行"
GRD_PREVIEW = "grd 先頭5行"
PREVIEW_EMPTY = "対象ファイルが見つかりません。"
LAYER_EMPTY = "(レイヤなし)"
REGION_NOTE = (
    "CSV は region_id ごとに 1 領域として扱います。"
    "SHP / GPKG は 1 地物を 1 領域として扱い、Polygon のみ対応です。"
)
REGION_SUMMARY_EMPTY = (
    "CSV は region_id ごと、SHP / GPKG は 1 地物ごとに 1 領域として扱います。"
)

RUN_BUTTON_TOOLTIP = "入力内容をもとに抽出処理を実行します。"
CLEAR_LOG_TOOLTIP = "下のログ表示を消します。"
SELECT_BUTTON_TOOLTIP = "参照ダイアログを開きます。"
ADD_REGION_TOOLTIP = "領域ファイルを追加します。複数追加できます。"
REMOVE_REGION_TOOLTIP = "選択中の領域ファイルを一覧から外します。"
MOVE_UP_TOOLTIP = "選択中の領域ファイルを上へ移動します。"
MOVE_DOWN_TOOLTIP = "選択中の領域ファイルを下へ移動します。"
REFRESH_PREVIEW_TOOLTIP = "入力フォルダ内の org と grd の先頭5行を読み直します。"

FILE_DIALOG_REGION_FILE = "領域ファイルを選択"
FILE_DIALOG_INPUT_DIR = "入力フォルダを選択"
FILE_DIALOG_OUTPUT_DIR = "出力フォルダを選択"

STATUS_START = "抽出処理を開始します。"
STATUS_CONFIG_READY = "入力内容を確認しました。"
STATUS_REGIONS_LOADED = (
    "抽出範囲を読み込みました。{region_count} 個の領域を使用します。"
)
STATUS_REGION_FILE_LOADED = (
    "領域ファイルを読み込みました: {path} / 形式: {format} / 地物数: {feature_count} / "
    "領域数: {region_count}{layer_suffix}{geometry_suffix}"
)
STATUS_WARNING = "警告: {message}"
STATUS_REGION_FILE_ADDED = "領域ファイルを追加しました: {path}"
STATUS_REGION_FILE_REMOVED = "領域ファイルを一覧から外しました: {path}"
STATUS_REGION_LAYER_SELECTED = "使用するレイヤを選択しました: {path} -> {layer}"
STATUS_REGION_LAYER_SINGLE = "使用するレイヤを自動で決定しました: {path} -> {layer}"
STATUS_REGION_LAYER_ERROR = "レイヤ一覧を読み取れませんでした: {error}"
STATUS_REGION_SUMMARY_ERROR = "領域ファイルの内容を確認できませんでした: {error}"
STATUS_INPUT_SCAN = "入力ファイルを確認しました。org {org_count} 件、grd {grd_count} 件、合計 {total_count} 件です。"
STATUS_FILE_GROUP_SKIPPED = (
    "[{system}] {path} は抽出範囲にかからないため、処理を省略しました。"
)
STATUS_FILE_GROUP_SCAN_START = "[{system}] 処理前の確認を始めます: {path}"
STATUS_FILE_GROUP_SCAN_PROGRESS = (
    "[{system}] 処理前の確認中: {path}（{records} 行読み取り済み）"
)
STATUS_FILE_GROUP_SCAN_DONE = "[{system}] 処理前の確認が終わりました: {path}"
STATUS_FILE_START = "[{system}] {index} / {total} ファイル目を処理しています: {path}"
STATUS_FILE_PROGRESS = "[{system}] {path} を処理中です（{records} 行読み取り済み）"
STATUS_FILE_DONE = "[{system}] {path} の処理が終わりました（{index} / {total}、{records} 行、{matches}）"
STATUS_OUTPUT_START = "抽出結果を書き出しています。"
STATUS_OUTPUT_FILE = "出力しました: {path}（{count} 行）"
STATUS_OUTPUT_DONE = "抽出結果の書き出しが完了しました。"
STATUS_SUCCESS = "抽出処理が完了しました。"
STATUS_OUTPUT_WRITTEN = "出力先フォルダ: {path}"
STATUS_PREVIEW_UPDATED = "プレビューを更新しました。"
STATUS_PREVIEW_ERROR = "プレビューを更新できませんでした: {error}"
STATUS_GUI_STARTED = "画面を起動しました。"
STATUS_CONFIG_ERROR = "入力内容に問題があります。"
STATUS_CONFIG_SUMMARY = (
    "設定内容: 領域ファイル={region_summary}, 入力フォルダ={input_dir}, 出力フォルダ={output_dir}, "
    "org(X={org_x}, Y={org_y}, Z={org_z}), grd(X={grd_x}, Y={grd_y}, Z={grd_z})"
)
STATUS_RUNTIME_ERROR = "処理中にエラーが発生しました。"

INFO_TITLE = "点群抽出"
ERROR_TITLE = "点群抽出"
