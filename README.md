# point-filter

3 つの領域定義に基づいて、`input/` 配下の点群テキストを `org` / `grd` ごとに抽出するツールです。

## 実行例

```bash
uv run python main.py --region-csv data/regions.csv --input-dir input --output-dir output --x-col 2 --y-col 3 --z-col 4
```

## GUI

```bash
uv run point-filter-gui
```

GUI にはメニューバーの `ヘルプ > 使い方` があり、単体で渡しても使える程度の詳細ヘルプを参照できます。

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
