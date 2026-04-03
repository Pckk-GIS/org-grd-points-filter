# Rust 版アーキテクチャ

## 1. 目的

Python 版 `31_point_filter` と同じ入出力を Rust で再実装する。

維持したい振る舞い:

- `region_id,x,y` の CSV で領域を定義する
- 同じ `region_id` の点群から自動で凸包を作る
- 入力列は 1 始まりの列番号で指定する
- `org` / `grd` を別々に処理する
- `region_id` ごとに `org` / `grd` の出力ファイルを作る
- 境界上の点は含める
- 出力は逐次書き込みで行う
- 巨大ファイルでも動く

## 2. 推奨構成

Rust 版は workspace にする。

```text
point-filter-rs/
  Cargo.toml
  crates/
    point-filter-core/
      Cargo.toml
      src/
        lib.rs
        config.rs
        models.rs
        geometry.rs
        region_loader.rs
        point_reader.rs
        output_writer.rs
        filter_service.rs
        validation.rs
    point-filter-cli/
      Cargo.toml
      src/
        main.rs
        cli.rs
    point-filter-gui/
      Cargo.toml
      src/
        main.rs
        app.rs
```

### 2.1 `point-filter-core`

UI を持たない純粋な処理層。

責務:

- CSV から領域を読む
- 凸包を作る
- 点の内外判定を行う
- 入力テキストを列番号で読む
- 系統ごとに抽出する
- 出力ファイルへ書く
- 進捗イベントを返す

### 2.2 `point-filter-cli`

CLI 入口。

責務:

- `clap` で引数を受ける
- 設定を組み立てる
- `point-filter-core` を呼ぶ
- エラーを整形して終了コードに変換する

### 2.3 `point-filter-gui`

後から追加する GUI 入口。

責務:

- 入力欄とボタンを表示する
- 実行ログを表示する
- `point-filter-core` を呼ぶ
- ヘルプやツールチップを表示する

## 3. クレートの依存方針

### 3.1 必須候補

- `clap`
  - CLI 引数の解析
- `csv`
  - 領域 CSV の読み込み
- `thiserror`
  - 独自エラーの定義
- `anyhow`
  - CLI / GUI 側の上位エラー集約
- `rayon`
  - ファイル単位の並列処理
- `tempfile`
  - 一時ファイル管理
- `tracing`
  - ログ出力
- `tracing-subscriber`
  - ログ購読
- `serde`
  - 将来の設定ファイル化に備える場合に追加

### 3.2 方針

- コア層は `std` と軽量な依存でまとめる
- GUI は別 crate にして、UI ライブラリの依存を core へ波及させない
- 依存追加は最小限にする

## 4. ドメインモデル

### 4.1 `Point2D`

2 次元座標。

### 4.2 `BoundingBox`

軸平行矩形。

用途:

- 領域ごとの事前フィルタ
- 入力ファイルの粗い絞り込み

### 4.3 `Region`

抽出対象の領域。

持つもの:

- `ordinal`
- `region_id`
- `vertices`
- `bounding_box`

### 4.4 `PointRecord`

入力ファイルの 1 行。

持つもの:

- 元の 1 行
- `x`
- `y`
- `z`
- 元ファイル
- 行番号
- 系統

### 4.5 `AppConfig`

実行設定。

持つもの:

- 領域 CSV
- 入力フォルダ
- 出力フォルダ
- `X/Y/Z` 列番号

## 5. 処理フロー

### 5.1 領域読み込み

1. `region_id,x,y` の CSV を読む
2. `region_id` ごとに点をまとめる
3. 凸包を作る
4. 領域ごとの `BoundingBox` を作る
5. 領域数が 3 であることを確認する

### 5.2 入力処理

1. 入力フォルダ内の `*.txt` を列挙する
2. `org` / `grd` をファイル名末尾で判定する
3. 1 ファイルごとに独立したタスクを作る
4. 並列ワーカーで読み込みと判定を行う
5. 一時ファイルへ逐次追記する
6. 完了後に本番ファイルへ置き換える

### 5.3 並列化方針

Rust 版では process ではなく thread を使う。

理由:

- GIL がないので process 分割の利点が小さい
- ファイル I/O と判定処理のバランスがよい
- 共有状態を減らしやすい

推奨:

- `rayon` の bounded なスレッドプールを使う
- 既定値は `2`
- 必要なら CLI 引数で変更できるようにする

### 5.4 出力

出力ルールは Python 版と合わせる。

- `org_region4.txt`
- `org_region5.txt`
- `grd_region4.txt`
- `grd_region5.txt`

一時ファイルからの確定は原子的に行う。

## 6. 実装上のベストプラクティス

### 6.1 エラー設計

- `thiserror` でドメインエラーを定義する
- 入力不正、座標不正、領域不正を明示的に区別する
- `anyhow` はアプリケーション層でのみ使う

### 6.2 文字列とパス

- Windows を前提に `std::path::PathBuf` を使う
- CSV と入力は UTF-8 を前提にする
- BOM が混ざる可能性があるなら読み込み時に吸収する

### 6.3 テスト

優先度は次の順。

1. 幾何計算
2. 領域 CSV 読み込み
3. 入力列マッピング
4. 抽出結果
5. 並列実行

### 6.4 ログ

- `tracing` で進捗を出す
- ファイル開始、100000 行進捗、ファイル完了を出す
- GUI がある場合はイベントに変換して表示する

## 7. Python 版との対応

Rust 版でそのまま引き継ぐもの:

- CSV 仕様
- 領域数 3
- 系統 `org` / `grd`
- 列番号 1 始まり
- 境界含む判定
- 出力ファイル名
- 逐次書き込み

Rust 版で見直すもの:

- 並列化の単位
- ログの実装
- GUI ライブラリ
- 配布形式

## 8. 移行順

1. `point-filter-core` を作る
2. 単体テストを先に書く
3. CLI を作る
4. Python 版と同じ入力で比較する
5. 並列化を入れる
6. GUI を追加する

## 9. まず切るタスク

- Cargo workspace を作る
- `Point2D` / `BoundingBox` / `Region` を定義する
- 領域 CSV ローダーを書く
- 凸包生成を書く
- 点の内外判定を書く
- 1 ファイル抽出の最小実装を書く
- 既存 Python 版のサンプルデータで差分比較する
