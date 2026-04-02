"""コマンドライン実行の入口を提供する。"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .config import AppConfig
from .filter_service import process
from .validation import PointFilterError


def build_parser() -> argparse.ArgumentParser:
    """CLI 引数パーサーを構築する。"""
    parser = argparse.ArgumentParser(description="Extract points into 3 regions.")
    parser.add_argument("--region-csv", type=Path, default=Path("data/regions.csv"))
    parser.add_argument("--input-dir", type=Path, default=Path("input"))
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--x-col", type=int, default=2)
    parser.add_argument("--y-col", type=int, default=3)
    parser.add_argument("--z-col", type=int, default=4)
    return parser


def run(config: AppConfig) -> int:
    """設定を受け取り、抽出から出力までを実行する。"""
    process(config)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI のエントリポイントとして引数を解釈する。"""
    parser = build_parser()
    args = parser.parse_args(argv)
    config = AppConfig(
        region_csv=args.region_csv,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        x_col=args.x_col,
        y_col=args.y_col,
        z_col=args.z_col,
    )

    try:
        return run(config)
    except PointFilterError as exc:
        parser.exit(status=1, message=f"error: {exc}\n")
