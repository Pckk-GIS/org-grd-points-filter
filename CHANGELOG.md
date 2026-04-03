# Changelog

このファイルには、このプロジェクトの主な変更を記録する。

形式は Keep a Changelog を参考にし、
バージョン番号は Semantic Versioning に従う。

## [Unreleased]

## [0.4.1] - 2026-04-03

### Fixed
- PyInstaller 配布物で `pyogrio` のネイティブ拡張モジュールが欠落し、ベクタ領域ファイル読込時に起動直後に失敗する問題を修正
- `pyogrio.libs` 配下の GDAL DLL と `gdal_data` / `proj_data` を配布物へ同梱するように変更し、SHP / GPKG を使う GUI 成果物が起動できるように修正

## [0.4.0] - 2026-04-03

### Added
- `point-filter-rs/` 配下に Rust workspace、CLI、GUI、ベンチマークの土台を追加
- Python 側から Rust エンジンを呼び出す仕組みとベンチマークコマンドを追加
- 日本語ラベル、ツールチップ、詳細ヘルプ、プレビューを備えた Tkinter GUI を追加
- GUI の PyInstaller パッケージング手順と、`pyproject.toml` の version に連動した成果物名を追加
- ファイル単位の並列処理と、一時ファイルを使った逐次書き込みを追加
- バウンディングボックスによる事前判定と、file_id 単位のスキップ最適化を追加
- `org` / `grd` で別々に列番号を指定できる仕組みを追加
- 1 回の実行で複数の領域定義ファイルを扱えるように対応
- 領域定義入力として CSV / SHP / GPKG を追加
- GPKG のレイヤ自動検出と GUI でのレイヤ選択を追加
- ベクタ領域入力に関する要件ドキュメントと関連テストを追加

### Changed
- 領域数の扱いを 3 固定から可変に変更
- 出力ファイル名を連番基準から `region_id` 基準へ変更
- ベクタ入力時の `region_id` をファイル名とレイヤ名に基づいて自動生成するよう変更
- CLI の主引数を `--region-file` 基準に寄せ、`--region-csv` は互換 alias として維持
- GUI の領域入力を単一 CSV 指定から、複数の領域ファイル管理方式へ変更
- GUI の実行エンジンは Python 固定とし、Rust エンジンは CLI のみで扱うよう整理

### Fixed
- 大きなファイルの事前確認や長時間読み込み時の進捗ログ不足を改善
- ファイル完了イベント時の GUI payload 不整合を修正
- Rust GUI で日本語フォントが崩れる問題を、Windows フォント明示登録で改善
