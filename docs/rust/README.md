# Rust 版移行メモ

このディレクトリは、`31_point_filter` の Rust 版を作るときの設計メモを置く場所です。

Python 版と同じ出力を目指しつつ、Rust では次の方針で組みます。

- コア処理はライブラリ crate に分離する
- CLI は薄い入口にする
- GUI は後段で追加する
- ファイル単位の並列処理は Rust の thread pool で行う
- 出力は逐次書き込みにして、巨大ファイルでもメモリ保持を避ける

## 参照順

1. [architecture.md](./architecture.md)
2. [verification.md](./verification.md)
