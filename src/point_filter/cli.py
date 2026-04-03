"""コマンドライン実行の入口を提供する。"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .config import AppConfig
from .engine import EngineName, run_engine
from .validation import PointFilterError


def build_parser() -> argparse.ArgumentParser:
    """CLI 引数パーサーを構築する。"""
    parser = argparse.ArgumentParser(
        description="Extract points into configured regions."
    )
    parser.add_argument("--region-csv", type=Path, default=Path("data/regions.csv"))
    parser.add_argument("--input-dir", type=Path, default=Path("input"))
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--engine", choices=("python", "rust"), default="python")
    parser.add_argument("--x-col", type=int, default=2)
    parser.add_argument("--y-col", type=int, default=3)
    parser.add_argument("--z-col", type=int, default=4)
    parser.add_argument("--org-x-col", type=int)
    parser.add_argument("--org-y-col", type=int)
    parser.add_argument("--org-z-col", type=int)
    parser.add_argument("--grd-x-col", type=int)
    parser.add_argument("--grd-y-col", type=int)
    parser.add_argument("--grd-z-col", type=int)
    return parser


def run(config: AppConfig, *, engine: EngineName = "python") -> int:
    """設定を受け取り、抽出から出力までを実行する。"""
    run_engine(engine, config)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI のエントリポイントとして引数を解釈する。"""
    parser = build_parser()
    args = parser.parse_args(argv)
    config = AppConfig(
        region_csv=args.region_csv,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        org_x_col=args.org_x_col or args.x_col,
        org_y_col=args.org_y_col or args.y_col,
        org_z_col=args.org_z_col or args.z_col,
        grd_x_col=args.grd_x_col or args.x_col,
        grd_y_col=args.grd_y_col or args.y_col,
        grd_z_col=args.grd_z_col or args.z_col,
    )

    try:
        return run(config, engine=args.engine)
    except PointFilterError as exc:
        parser.exit(status=1, message=f"error: {exc}\n")
