# point-filter

複数の領域定義ファイルに基づいて、`input/` 配下の点群テキストを `org` / `grd` ごとに抽出するツールです。領域定義は `CSV / SHP / GPKG` を受け付け、出力ファイル名は自動生成された `region_id` ベースです。

## 実行例

```bash
uv run python main.py --region-file data/regions.csv --input-dir input --output-dir output --x-col 2 --y-col 3 --z-col 4
uv run python main.py --region-file data/regions.csv --region-file data/areas.shp --input-dir input --output-dir output --org-x-col 2 --org-y-col 3 --org-z-col 4 --grd-x-col 1 --grd-y-col 2 --grd-z-col 3
uv run python main.py --region-file data/zones.gpkg --region-layer zones.gpkg=target_layer --input-dir input --output-dir output
uv run python main.py --engine rust --region-file data/regions.csv --input-dir input --output-dir output
```

`--region-csv` は旧引数として互換用に残しています。Rust エンジンは現在 CSV 1 ファイルのみ対応です。

## GUI

```bash
uv run point-filter-gui
```

GUI にはメニューバーの `ヘルプ > 使い方` があり、単体で渡しても使える程度の詳細ヘルプを参照できます。
GUI では複数の領域ファイルを追加でき、GPKG はレイヤ一覧を自動読込します。選択中の領域ファイルについては、`1 地物 = 1 領域` の扱いになることを画面上に表示します。`org` / `grd` それぞれの列番号を別々に指定でき、入力フォルダ内の先頭 5 行プレビューも確認できます。Rust エンジンの切り替えは CLI 側だけに残しています。

## ベンチ

```bash
uv run point-filter-bench --region-file data/regions.csv --input-dir input --repeat 3
```

Rust 側は既定で `point-filter-rs/` の `cargo run -p point-filter-cli` を呼びます。別コマンドを使う場合は `POINT_FILTER_RUST_COMMAND` を設定してください。

## GUI の入口

PyInstaller 向けの GUI 起動入口は `gui_main.py` です。配布ビルドではこの入口を参照します。

## exe 化

```bash
uv run pyinstaller -y point-filter-gui.spec
```

## 開発コマンド

```bash
uv run pytest -q
uv run ruff check .
uv run pyright
uv run pre-commit run --all-files
```
