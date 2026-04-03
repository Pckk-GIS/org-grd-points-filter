# point-filter

`region_id,x,y` の領域定義に基づいて、`input/` 配下の点群テキストを `org` / `grd` ごとに抽出するツールです。領域数は可変で、出力ファイル名は `region_id` ベースです。

## 実行例

```bash
uv run python main.py --region-csv data/regions.csv --input-dir input --output-dir output --x-col 2 --y-col 3 --z-col 4
uv run python main.py --region-csv data/regions.csv --input-dir input --output-dir output --org-x-col 2 --org-y-col 3 --org-z-col 4 --grd-x-col 1 --grd-y-col 2 --grd-z-col 3
uv run python main.py --engine rust --region-csv data/regions.csv --input-dir input --output-dir output
```

## GUI

```bash
uv run point-filter-gui
```

GUI にはメニューバーの `ヘルプ > 使い方` があり、単体で渡しても使える程度の詳細ヘルプを参照できます。
GUI では `org` / `grd` それぞれの列番号を別々に指定でき、入力フォルダ内の先頭 5 行プレビューも確認できます。Rust エンジンの切り替えは CLI 側だけに残しています。

## ベンチ

```bash
uv run point-filter-bench --region-csv data/regions.csv --input-dir input --repeat 3
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
