# 31_point_filter 詳細設計

## 1. 方針

- リポジトリ名は `31_point_filter` のまま維持する。
- Python パッケージ名は `point_filter` とする。
- `main.py` は最小のエントリポイントにして、実処理は `point_filter` 配下へ寄せる。
- CLI を先に完成させ、CLI のテストが安定して通る段階で GUI 実装に着手する。
- GUI は CLI と同じコアロジックを再利用し、処理本体を持たない。

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
- `region_loader.py`
  - CSV から領域定義を読む
- `point_reader.py`
  - 入力テキストを読む
  - `X/Y/Z` 列番号に応じて点を取り出す
- `filter_service.py`
  - 3 領域への振り分け処理の中核
- `output_writer.py`
  - 6 ファイルの書き出し
- `validation.py`
  - 頂点順の異常、座標欠損、列番号不正などの検証
- `gui/`
  - CLI 完了後に追加する UI 層

## 3. モジュール命名

### 3.1 使う名前

- パッケージ名: `point_filter`
- CLI 実装: `point_filter.cli`
- 実行入口: `point_filter.__main__`
- GUI 実装: `point_filter.gui`

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

- 頂点列は同じ `region_id` の行順で構成する。
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
3. 入力フォルダの `*.txt` を列挙する
4. ファイル名末尾の `_org` / `_grd` で系統を判定する
5. `X/Y/Z` 列番号で点を抽出する
6. 領域ごとの内外判定を行う
7. 該当結果を 6 ファイルへ出力する
8. 異常があればエラー終了する

### 5.2 GUI 実装時の考え方

- GUI は処理本体を直接持たず、`filter_service` を呼ぶだけにする。
- GUI で変更するのは入力パス、CSV パス、列番号などの設定のみ。
- CLI と GUI の両方が同じ `config` と `service` を使う。

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
- 頂点順に異常があれば即座に失敗
- 境界点は含める
- 重なりは全領域へ出力

## 7. GUI 導入条件

GUI は次の条件を満たしたら着手する。

- CLI の基本機能が実装済み
- CLI の単体テストが通る
- CLI の結合テストが通る
- 主要な異常系の挙動が固まっている

GUI 着手時の制約:

- コアロジックは変更しない
- 必要なら UI 層だけ追加する
- CLI と GUI の差分は入出力の見せ方に限定する

## 8. テスト方針

### 8.1 単体テスト

- CSV 読み込み
- 列番号の解釈
- 頂点順の妥当性確認
- 凸性判定
- 内外判定

### 8.2 結合テスト

- 1 つの入力フォルダに対して 6 ファイルが出ること
- 境界点が含まれること
- 重なり点が両方に出ること
- 頂点順異常で失敗すること

### 8.3 GUI 着手前の判定

CLI のテストが安定して通る状態を、GUI 着手の合図とする。

## 9. 実装順

1. `point_filter.models`
2. `point_filter.validation`
3. `point_filter.geometry`
4. `point_filter.region_loader`
5. `point_filter.point_reader`
6. `point_filter.filter_service`
7. `point_filter.output_writer`
8. `point_filter.cli`
9. `point_filter.gui`
