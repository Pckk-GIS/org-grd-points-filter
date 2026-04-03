"""Python / Rust エンジンのベンチマークを実行する。"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from time import perf_counter
from typing import Sequence

from .config import AppConfig
from .engine import EngineName, run_engine
from .region_loader import load_regions


def build_parser() -> argparse.ArgumentParser:
    """ベンチマーク用の CLI 引数パーサーを構築する。"""
    parser = argparse.ArgumentParser(description="Benchmark Python and Rust engines.")
    parser.add_argument("--region-csv", type=Path, default=Path("data/regions.csv"))
    parser.add_argument("--input-dir", type=Path, default=Path("input"))
    parser.add_argument("--output-root", type=Path, default=Path("output-bench"))
    parser.add_argument("--x-col", type=int, default=2)
    parser.add_argument("--y-col", type=int, default=3)
    parser.add_argument("--z-col", type=int, default=4)
    parser.add_argument("--org-x-col", type=int)
    parser.add_argument("--org-y-col", type=int)
    parser.add_argument("--org-z-col", type=int)
    parser.add_argument("--grd-x-col", type=int)
    parser.add_argument("--grd-y-col", type=int)
    parser.add_argument("--grd-z-col", type=int)
    parser.add_argument("--repeat", type=int, default=1)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """ベンチマークを実行して結果を標準出力へ表示する。"""
    parser = build_parser()
    args = parser.parse_args(argv)
    config = AppConfig(
        region_csv=args.region_csv,
        input_dir=args.input_dir,
        output_dir=args.output_root / "python",
        org_x_col=args.org_x_col or args.x_col,
        org_y_col=args.org_y_col or args.y_col,
        org_z_col=args.org_z_col or args.z_col,
        grd_x_col=args.grd_x_col or args.x_col,
        grd_y_col=args.grd_y_col or args.y_col,
        grd_z_col=args.grd_z_col or args.z_col,
    )

    python_durations: list[float] = []
    rust_durations: list[float] = []
    rust_config = AppConfig(
        region_csv=config.region_csv,
        input_dir=config.input_dir,
        output_dir=args.output_root / "rust",
        org_x_col=config.org_x_col,
        org_y_col=config.org_y_col,
        org_z_col=config.org_z_col,
        grd_x_col=config.grd_x_col,
        grd_y_col=config.grd_y_col,
        grd_z_col=config.grd_z_col,
    )

    for index in range(args.repeat):
        _reset_output_dir(config.output_dir)
        _reset_output_dir(rust_config.output_dir)

        python_durations.append(_measure("python", config))
        rust_durations.append(_measure("rust", rust_config))
        print(f"round {index + 1} complete")

    _compare_outputs(config.region_csv, config.output_dir, rust_config.output_dir)
    python_avg = sum(python_durations) / len(python_durations)
    rust_avg = sum(rust_durations) / len(rust_durations)
    print(f"python avg: {python_avg:.3f}s")
    print(f"rust avg:   {rust_avg:.3f}s")
    if rust_avg > 0:
        print(f"speedup:    {python_avg / rust_avg:.2f}x")
    return 0


def _measure(engine: EngineName, config: AppConfig) -> float:
    started_at = perf_counter()
    run_engine(engine, config)
    return perf_counter() - started_at


def _reset_output_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _compare_outputs(region_csv: Path, left_dir: Path, right_dir: Path) -> None:
    for region in load_regions(region_csv):
        for system in ("org", "grd"):
            name = f"{system}_region{region.region_id}.txt"
            left = (left_dir / name).read_bytes()
            right = (right_dir / name).read_bytes()
            if left != right:
                raise RuntimeError(f"output mismatch: {name}")
