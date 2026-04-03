# point-filter

点群テキストから、指定した領域ごとに `org` / `grd` を抽出する GUI ツールです。  
社内利用を前提に、まず GUI で使いやすいことを重視しています。

## 1. このツールでできること

- 複数の領域ファイルを同時に読み込む
- `org` と `grd` で別々の列番号を指定して抽出する
- CSV / SHP / GPKG を領域定義として使う
- 抽出結果を `region_id` ごとのテキストファイルに出力する
- GUI から操作する

## 2. まず使う人向けの前提

- このリポジトリには、実際の点群テキストそのものは含めません
- 利用者は、自分の手元または共有フォルダ上の入力点群フォルダを GUI から選択して使います
- GUI で使うのが基本です
- CLI は補助用途です

## 3. サンプル領域ファイル

動作確認用のサンプル領域ファイルは `data/sample_region/` にあります。

- [regions.csv](C:/Users/yuuta.ochiai/Documents/31_point_filter/data/sample_region/regions.csv)
- [regions_sample.shp](C:/Users/yuuta.ochiai/Documents/31_point_filter/data/sample_region/regions_sample.shp)
- [regions_sample.gpkg](C:/Users/yuuta.ochiai/Documents/31_point_filter/data/sample_region/regions_sample.gpkg)

この 3 つは同じ領域を別形式で持っています。  
まずはこれらを使えば、GUI 上で挙動を確認できます。

## 4. 入力点群テキストの想定

入力フォルダには、次のようなテキストファイルを置きます。

- `*_org.txt`
- `*_grd.txt`

例:

- `09ld331_org.txt`
- `09ld331_grd.txt`

### 形式

- ヘッダ行なし
- 1 行 = 1 点
- 列は区切られていればよい
- X / Y / Z の列番号は GUI で指定する
- 列番号は 1 始まり

このツールは Python の `csv` 読み取りで 1 行ずつ処理するため、基本的には **カンマ区切り** のテキストを想定しています。

例:

```text
1,123.45,456.78,9.10
2,124.00,457.20,9.05
```

この例で `X=2, Y=3, Z=4` を指定すると、

- 2 列目を X
- 3 列目を Y
- 4 列目を Z

として読み込みます。

## 5. 領域ファイルの考え方

### CSV

- 形式は `region_id,x,y`
- 1 行 = 1 頂点
- 同じ `region_id` の点群から自動で凸包を作ります

### SHP / GPKG

- `Polygon` のみ対応
- `1 地物 = 1 領域`
- `MultiPolygon` は非対応
- `region_id` は自動生成

自動生成ルール:

- CSV: `ファイル名_region_id`
- SHP: `ファイル名_連番`
- GPKG: `ファイル名_レイヤ名_連番`

## 6. GUI の使い方

GUI を起動します。

```bash
uv run point-filter-gui
```

操作の流れ:

1. `領域ファイル` に CSV / SHP / GPKG を追加する
2. GPKG の場合は必要に応じてレイヤを選ぶ
3. `入力フォルダ` を選ぶ
4. `出力フォルダ` を選ぶ
5. `org` と `grd` の列番号を入力する
6. プレビューで先頭 5 行を確認する
7. `実行` を押す

補足:

- 選択中の領域ファイルは、画面上で「何地物を何領域として扱うか」を表示します
- メニューバーの `ヘルプ > 使い方` から、GUI 内で詳細説明を確認できます

## 7. GUI 画面キャプチャ

後で GUI の画面キャプチャを README に載せる想定です。  
配置先は次を想定しています。

- `docs/images/gui-main.png`

画像を追加するときは、このファイル名に合わせれば README 側の修正が最小で済みます。

## 8. CLI の基本例

GUI が基本ですが、CLI でも実行できます。

```bash
uv run point-filter --region-file data/sample_region/regions.csv --input-dir input --output-dir output --x-col 2 --y-col 3 --z-col 4
uv run point-filter --region-file data/sample_region/regions.csv --region-file data/sample_region/regions_sample.shp --input-dir input --output-dir output
uv run point-filter --region-file data/sample_region/regions_sample.gpkg --region-layer regions_sample.gpkg=regions --input-dir input --output-dir output
```

互換用:

- `--region-csv` も引き続き使えます

制約:

- Rust エンジンは現在 CSV 1 ファイルのみ対応です
- SHP / GPKG や複数領域ファイルでは Python エンジンを使います

## 9. 出力

出力は `region_id` ごとに作成されます。

例:

- `org_regionregions_1.txt`
- `org_regionregions_sample_1.txt`
- `grd_regionregions_regions_2.txt`

## 10. 配布とバージョン

このツールは GUI をビルドして配布する前提で管理しています。

- バージョンは [pyproject.toml](C:/Users/yuuta.ochiai/Documents/31_point_filter/pyproject.toml) で管理します
- `CHANGELOG.md` で変更内容を管理します
- PyInstaller の成果物名にも version を反映します

GUI のビルド:

```bash
uv run pyinstaller -y point-filter-gui.spec
```

成果物は `dist/point-filter-gui-vX.Y.Z/` のような形になります。

## 11. 開発コマンド

```bash
uv run pytest -q
uv run ruff check .
uv run pyright
uv run pre-commit run --all-files
```
