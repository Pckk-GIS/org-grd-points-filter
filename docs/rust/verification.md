# Rust 版の検証

Rust 版では、Python 版と同じ入力に対して同じ出力を得ることを確認する。

検証方法:

1. 代表的な小規模データで Python 版を実行する
2. 同じ入力で Rust 版を実行する
3. `region_id` ごとの出力を byte 単位で比較する

比較テストは `point-filter-core` の integration test に置く。
