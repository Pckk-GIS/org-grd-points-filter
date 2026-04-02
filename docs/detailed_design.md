# 31_point_filter 詳細設計

## 1. 方針

- リポジトリ名は `31_point_filter` のまま維持する。
- Python パッケージ名は `point_filter` とする。
- `main.py` は最小のエントリポイントにして、実処理は `point_filter` 配下へ寄せる。
- CLI を先に完成させ、CLI のテストが安定して通る段階で GUI 実装に着手する。
- GUI は CLI と同じコアロジックを再利用し、処理本体を持たない。
- PyInstaller で exe 化できるよう、GUI は単独起動できるエントリポイントを持つ。
- GUI にはメニューバーを設け、`ヘルプ > 使い方` から詳細ヘルプを開けるようにする。
- GUI 文言、ツールチップ、ヘルプ本文は共通定義にまとめる。

## 2. レイヤ構成

### 2.1 推奨構成

```text
src/
  point_filter/
    __init__.py
    __main__.py
    cli.py
    config.py
    models.py
    geometry.py
    region_loader.py
    point_reader.py
    filter_service.py
    output_writer.py
    validation.py
    gui/
      __init__.py
      __main__.py
      main_window.py
      state.py
      view_model.py
```

### 2.2 レイヤの責務

- `cli.py`
  - CLI 引数の解釈
  - 設定の組み立て
  - サービス呼び出し
- `config.py`
  - CLI / GUI 共通の設定値を保持するデータ構造
- `models.py`
  - 領域、点、抽出結果などのドメインモデル
- `geometry.py`
  - 点の内外判定
  - 凸多角形の妥当性確認
  - 領域ごとの矩形範囲計算
  - 点ごとの矩形による事前判定
- `region_loader.py`
  - CSV から点群を読む
  - `region_id` ごとに点を集める
  - 点群から凸包を作って領域順を決める
  - 領域ごとの矩形範囲を作る
- `point_reader.py`
  - 入力テキストを読む
  - `X/Y/Z` 列番号に応じて点を取り出す
- `filter_service.py`
  - 3 領域への振り分け処理の中核
  - 出力先へ逐次書き込む
  - ファイル単位で並列処理する
  - 領域矩形で点判定を絞り込む
- `output_writer.py`
  - 6 ファイルの逐次書き出し
  - 一時ファイルから本番ファイルへの確定
- `validation.py`
  - 頂点順の異常、座標欠損、列番号不正などの検証
- `gui/`
  - CLI 完了後に追加する UI 層
  - ラベル、ツールチップ、ヘルプ画面を含む

## 3. モジュール命名

### 3.1 使う名前

- パッケージ名: `point_filter`
- CLI 実装: `point_filter.cli`
- 実行入口: `point_filter.__main__`
- GUI 実装: `point_filter.gui`
- GUI 実行入口: `point_filter.gui.__main__`
- PyInstaller 用 GUI 入口: `gui_main.py`

### 3.2 命名の意図

- `point_filter` は用途がそのまま分かる。
- `31_point_filter` は Python の import 名として扱いにくいので使わない。
- CLI と GUI を同じパッケージに置くことで、共通ロジックを再利用しやすい。

## 4. ドメインモデル

### 4.1 `Region`

領域を表すモデル。

持つ情報:

- `region_id`
- 頂点列

前提:

- 頂点列は同じ `region_id` の点群から自動生成する。
- 現時点では凸多角形のみを許可する。

### 4.2 `PointRecord`

入力点を表すモデル。

持つ情報:

- 元データの1行
- `x`
- `y`
- `z`
- 元ファイル名
- 行番号

### 4.3 `FilterResult`

抽出結果を表すモデル。

持つ情報:

- 領域ごとの出力行
- エラー情報
- 処理対象ファイル情報

## 5. 処理フロー

### 5.1 CLI 実行フロー

1. CLI 引数を受け取る
2. 領域 CSV を読む
3. `region_id` ごとに点群を集める
4. 点群から凸包を作り、領域順を確定する
5. 入力フォルダの `*.txt` を列挙する
6. ファイル名末尾の `_org` / `_grd` で系統を判定する
7. `X/Y/Z` 列番号で点を抽出する
8. 領域ごとの内外判定を行う
9. 該当結果を 6 ファイルへ出力する
10. 異常があればエラー終了する

### 5.2 GUI 実装時の考え方

- GUI は処理本体を直接持たず、`filter_service` を呼ぶだけにする。
- GUI で変更するのは入力パス、CSV パス、列番号などの設定のみ。
- CLI と GUI の両方が同じ `config` と `service` を使う。
- GUI のラベルは `gui/labels.py` に集約する。
- 詳細ヘルプ本文は `gui/help_text.py` に集約する。
- ヘルプ画面は `gui/help_window.py` で開く。
- 出力はメモリに全件保持せず、逐次書き込みで処理する。

## 6. CLI 設計

### 6.1 入力

CLI で最低限必要な引数は以下。

- 領域 CSV のパス
- 入力フォルダ
- `X` 列番号
- `Y` 列番号
- `Z` 列番号
- 出力先フォルダ

### 6.2 振る舞い

- 列番号は 1 始まり
- ヘッダはない前提
- `region_id` ごとの点群から凸包を作れなければ即座に失敗
- 境界点は含める
- 重なりは全領域へ出力

## 7. GUI 設計

### 7.1 画面構成

GUI は 1 画面完結とする。

主な入力項目:

- 領域 CSV
- 入力フォルダ
- 出力フォルダ
- `X` 列番号
- `Y` 列番号
- `Z` 列番号

主な操作:

- CSV 選択
- 入力フォルダ選択
- 出力フォルダ選択
- 実行

表示領域:

- 実行ログ
- 成功 / 失敗メッセージ

補足:

- メニューバーの `ヘルプ` から使い方を開ける。
- ツールチップで各入力欄の意味を補足する。

### 7.2 実装方針

- Tkinter を使う。
- GUI は `AppConfig` を組み立てて `filter_service` を呼ぶだけにする。
- 重い処理は別スレッドで実行する。
- 画面更新は `after()` で行う。
- 成功時は完了メッセージを表示する。
- 失敗時はエラーメッセージとログを表示する。
- 長時間処理では 10000 行ごとの進捗ログを表示する。
- 進捗ログはファイル単位の開始・進捗・完了を追えるようにする。

### 7.3 PyInstaller 方針

- PyInstaller で `onedir` 形式の exe を作れるようにする。
- GUI 用のエントリポイントは `point_filter.gui.__main__` とする。
- GUI 実装は標準ライブラリ中心にし、配布時の依存を最小化する。
- `point-filter-gui.spec` を配布用ビルド定義として保持する。
- spec は root の `gui_main.py` をエントリポイントとして参照する。
- root の `gui_main.py` は配布用の薄いラッパーとする。
- 再ビルド時は `-y` を付けて既存 `dist` を更新する。

## 8. GUI 導入条件

GUI は次の条件を満たしたら着手する。

- CLI の基本機能が実装済み
- CLI の単体テストが通る
- CLI の結合テストが通る
- 主要な異常系の挙動が固まっている

GUI 着手時の制約:

- コアロジックは変更しない
- 必要なら UI 層だけ追加する
- CLI と GUI の差分は入出力の見せ方に限定する

## 9. テスト方針

### 9.1 単体テスト

- CSV 読み込み
- 列番号の解釈
- 凸包生成
- 頂点順の妥当性確認
- 凸性判定
- 内外判定

### 9.2 結合テスト

- 1 つの入力フォルダに対して 6 ファイルが出ること
- CSV の行順がランダムでも正しく処理できること
- 境界点が含まれること
- 重なり点が両方に出ること
- 凸包を作れない入力で失敗すること

### 9.3 GUI 着手前の判定

CLI のテストが安定して通る状態を、GUI 着手の合図とする。

## 10. 実装順

1. `point_filter.models`
2. `point_filter.validation`
3. `point_filter.geometry`
4. `point_filter.region_loader`
5. `point_filter.point_reader`
6. `point_filter.filter_service`
7. `point_filter.output_writer`
8. `point_filter.cli`
9. `point_filter.gui`
10. `point-filter-gui.spec` の整備
