"""コマンドライン実行の入口を提供する。"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .config import AppConfig, RegionInput
from .engine import EngineName, run_engine
from .validation import PointFilterError


def build_parser() -> argparse.ArgumentParser:
    """CLI 引数パーサーを構築する。"""
    parser = argparse.ArgumentParser(
        description="Extract points into configured regions."
    )
    parser.add_argument(
        "--region-file",
        type=Path,
        action="append",
        dest="region_files",
        default=[],
    )
    parser.add_argument("--region-csv", type=Path, dest="legacy_region_csv")
    parser.add_argument(
        "--region-layer",
        action="append",
        dest="region_layers",
        default=[],
        help="Use filename=layer_name for GPKG files.",
    )
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
    region_inputs = _build_region_inputs(
        args.region_files, args.legacy_region_csv, args.region_layers
    )
    config = AppConfig(
        region_inputs=tuple(region_inputs),
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


def _build_region_inputs(
    region_files: list[Path], legacy_region_csv: Path | None, region_layers: list[str]
) -> list[RegionInput]:
    combined_files = list(region_files)
    if legacy_region_csv is not None:
        combined_files.append(legacy_region_csv)
    if not combined_files:
        combined_files = [Path("data/sample_region/regions.csv")]

    layers_by_name: dict[str, str] = {}
    for layer_spec in region_layers:
        if "=" not in layer_spec:
            raise PointFilterError(
                f"region-layer must be filename=layer_name: {layer_spec!r}"
            )
        filename, layer_name = layer_spec.split("=", 1)
        filename = filename.strip()
        layer_name = layer_name.strip()
        if not filename or not layer_name:
            raise PointFilterError(
                f"region-layer must be filename=layer_name: {layer_spec!r}"
            )
        layers_by_name[filename] = layer_name

    return [
        RegionInput(path=path, layer=layers_by_name.get(path.name))
        for path in combined_files
    ]
