"""Python と Rust の実行エンジンを切り替える。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import shlex
import subprocess
from time import perf_counter
from typing import Literal, Sequence

from .config import AppConfig
from .filter_service import ProcessingReport, process
from .models import InputSystem
from .region_loader import load_regions
from .validation import ConfigurationError, PointFilterError


EngineName = Literal["python", "rust"]
REPO_ROOT = Path(__file__).resolve().parents[2]
RUST_WORKSPACE = REPO_ROOT / "point-filter-rs"
ResolvedRustCommand = tuple[list[str], Path]


def run_engine(
    engine: EngineName,
    config: AppConfig,
    *,
    progress_callback=None,
    rust_command: Sequence[str] | None = None,
) -> ProcessingReport:
    """指定されたエンジンで抽出処理を実行する。"""
    if engine == "python":
        return process(config, progress_callback=progress_callback)
    if engine == "rust":
        return run_rust_engine(config, rust_command=rust_command)
    raise ConfigurationError(f"Unsupported engine: {engine}")


def run_rust_engine(
    config: AppConfig, *, rust_command: Sequence[str] | None = None
) -> ProcessingReport:
    """Rust CLI を subprocess で呼び出して処理を実行する。"""
    resolved_command, command_cwd = _resolve_rust_command(rust_command)
    command = [
        *resolved_command,
        "--region-csv",
        str(config.region_csv),
        "--input-dir",
        str(config.input_dir),
        "--output-dir",
        str(config.output_dir),
        "--org-x-col",
        str(config.org_x_col),
        "--org-y-col",
        str(config.org_y_col),
        "--org-z-col",
        str(config.org_z_col),
        "--grd-x-col",
        str(config.grd_x_col),
        "--grd-y-col",
        str(config.grd_y_col),
        "--grd-z-col",
        str(config.grd_z_col),
    ]
    started_at = perf_counter()
    completed = subprocess.run(
        command,
        cwd=command_cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    _ = perf_counter() - started_at
    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip()
        message = "Rust engine failed"
        if details:
            message = f"{message}: {details}"
        raise PointFilterError(message)
    return _build_report_from_outputs(config)


def _find_bundled_rust_command() -> ResolvedRustCommand | None:
    if not getattr(sys, "frozen", False):
        return None

    executable_dir = Path(sys.executable).resolve().parent
    candidates = [
        executable_dir / "point-filter-cli.exe",
        executable_dir / "_internal" / "point-filter-cli.exe",
    ]
    for bundled_cli in candidates:
        if bundled_cli.exists():
            return [str(bundled_cli)], bundled_cli.parent

    return None


def _resolve_rust_command(override: Sequence[str] | None) -> ResolvedRustCommand:
    if override is not None:
        return list(override), REPO_ROOT

    env_command = os.environ.get("POINT_FILTER_RUST_COMMAND", "").strip()
    if env_command:
        return shlex.split(env_command, posix=False), REPO_ROOT

    bundled_command = _find_bundled_rust_command()
    if bundled_command is not None:
        return bundled_command

    manifest_path = RUST_WORKSPACE / "Cargo.toml"
    if manifest_path.exists():
        return (
            [
                "cargo",
                "run",
                "--quiet",
                "-p",
                "point-filter-cli",
                "--manifest-path",
                str(manifest_path),
                "--",
            ],
            REPO_ROOT,
        )

    raise ConfigurationError(
        "Rust engine is unavailable. Set POINT_FILTER_RUST_COMMAND or prepare point-filter-rs or point-filter-cli.exe."
    )


def _build_report_from_outputs(config: AppConfig) -> ProcessingReport:
    region_ids = [region.region_id for region in load_regions(config.region_csv)]
    input_files: dict[InputSystem, int] = {
        "org": len(list(config.input_dir.glob("*_org.txt"))),
        "grd": len(list(config.input_dir.glob("*_grd.txt"))),
    }
    output_counts: dict[InputSystem, dict[str, int]] = {"org": {}, "grd": {}}
    for system in ("org", "grd"):
        for region_id in region_ids:
            output_path = config.output_dir / f"{system}_region{region_id}.txt"
            output_counts[system][region_id] = _count_lines(output_path)
    return ProcessingReport(
        region_count=len(region_ids),
        input_files=input_files,
        output_counts=output_counts,
    )


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        return sum(1 for _ in handle)
