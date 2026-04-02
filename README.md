# point-filter

3 つの領域定義に基づいて、`input/` 配下の点群テキストを `org` / `grd` ごとに抽出するツールです。

## 実行例

```bash
uv run python main.py --region-csv data/regions.csv --input-dir input --output-dir output --x-col 2 --y-col 3 --z-col 4
```

## 開発コマンド

```bash
uv run pytest -q
uv run ruff check .
uv run pyright
uv run pre-commit run --all-files
```
