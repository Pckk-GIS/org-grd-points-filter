"""入力テキストの列読み取りとファイル列挙を行う。"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable, Iterable

from .geometry import BoundingBox
from .models import InputSystem, PointRecord
from .validation import DataFormatError


@dataclass(frozen=True, slots=True)
class InputFilePair:
    """同じ file ID を持つ org / grd の入力を表す。"""

    file_id: str
    org: Path | None
    grd: Path | None


def detect_system_from_filename(path: Path) -> InputSystem | None:
    """ファイル名末尾から org / grd 系統を判定する。"""
    stem = path.stem.lower()
    if stem.endswith("_org"):
        return "org"
    if stem.endswith("_grd"):
        return "grd"
    return None


def detect_file_id_from_filename(path: Path) -> str | None:
    """ファイル名から org / grd 末尾を除いた ID を取り出す。"""
    stem = path.stem
    lower_stem = stem.lower()
    if lower_stem.endswith("_org") or lower_stem.endswith("_grd"):
        return stem[:-4]
    return None


def iter_input_files(input_dir: Path) -> dict[InputSystem, list[Path]]:
    """入力フォルダ内の対象テキストを系統ごとにまとめる。"""
    grouped: dict[InputSystem, list[Path]] = {"org": [], "grd": []}
    if not input_dir.exists():
        raise DataFormatError(f"Input directory not found: {input_dir}")

    for path in sorted(input_dir.glob("*.txt")):
        system = detect_system_from_filename(path)
        if system is None:
            continue
        grouped[system].append(path)
    return grouped


def iter_input_file_pairs(input_dir: Path) -> list[InputFilePair]:
    """入力フォルダ内の対象テキストを file ID ごとにまとめる。"""
    if not input_dir.exists():
        raise DataFormatError(f"Input directory not found: {input_dir}")

    grouped: dict[str, dict[InputSystem, Path]] = {}
    for path in sorted(input_dir.glob("*.txt")):
        system = detect_system_from_filename(path)
        file_id = detect_file_id_from_filename(path)
        if system is None or file_id is None:
            continue
        grouped.setdefault(file_id, {})[system] = path

    pairs: list[InputFilePair] = []
    for file_id in sorted(grouped):
        files = grouped[file_id]
        pairs.append(
            InputFilePair(
                file_id=file_id,
                org=files.get("org"),
                grd=files.get("grd"),
            )
        )
    return pairs


def find_preview_file(input_dir: Path, system: InputSystem) -> Path | None:
    """指定系統の先頭プレビューファイルを返す。"""
    grouped = iter_input_files(input_dir)
    paths = grouped[system]
    return paths[0] if paths else None


def read_preview_lines(path: Path, limit: int = 5) -> list[str]:
    """先頭数行の非空行を返す。"""
    lines: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw_line in handle:
            stripped = raw_line.rstrip("\r\n")
            if not stripped.strip():
                continue
            lines.append(stripped)
            if len(lines) >= limit:
                break
    return lines


def _parse_float(
    value: str,
    *,
    path: Path,
    line_number: int,
    field_name: str,
) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise DataFormatError(
            f"Invalid {field_name} value in {path} line {line_number}: {value!r}"
        ) from exc


def measure_input_file_bounds(
    path: Path,
    *,
    x_col: int,
    y_col: int,
    system: InputSystem,
    progress_callback: Callable[[int], None] | None = None,
) -> BoundingBox:
    """点群ファイル全体の AABB を求める。"""
    x_index = x_col - 1
    y_index = y_col - 1
    min_x = float("inf")
    max_x = float("-inf")
    min_y = float("inf")
    max_y = float("-inf")
    point_count = 0

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            stripped = raw_line.rstrip("\r\n")
            if not stripped.strip():
                continue

            fields = next(csv.reader([stripped]))
            normalized_fields = tuple(field.strip() for field in fields)

            if max(x_index, y_index) >= len(normalized_fields):
                raise DataFormatError(
                    f"{path} line {line_number} has only {len(normalized_fields)} columns, "
                    f"but columns {x_col} and {y_col} were requested"
                )

            x = _parse_float(
                normalized_fields[x_index],
                path=path,
                line_number=line_number,
                field_name="x",
            )
            y = _parse_float(
                normalized_fields[y_index],
                path=path,
                line_number=line_number,
                field_name="y",
            )

            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            point_count += 1
            if progress_callback is not None and point_count % 100000 == 0:
                progress_callback(point_count)

    if point_count == 0:
        raise DataFormatError(f"{path} does not contain any usable {system} points")

    return BoundingBox(min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y)


def iter_point_records(
    path: Path,
    *,
    x_col: int,
    y_col: int,
    z_col: int,
    system: InputSystem,
) -> Iterable[PointRecord]:
    """指定列から点レコードを順次読み出す。"""
    x_index = x_col - 1
    y_index = y_col - 1
    z_index = z_col - 1

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            stripped = raw_line.rstrip("\r\n")
            if not stripped.strip():
                continue

            fields = next(csv.reader([stripped]))
            normalized_fields = tuple(field.strip() for field in fields)

            if max(x_index, y_index, z_index) >= len(normalized_fields):
                raise DataFormatError(
                    f"{path} line {line_number} has only {len(normalized_fields)} columns, "
                    f"but columns {x_col}, {y_col}, {z_col} were requested"
                )

            x = _parse_float(
                normalized_fields[x_index],
                path=path,
                line_number=line_number,
                field_name="x",
            )
            y = _parse_float(
                normalized_fields[y_index],
                path=path,
                line_number=line_number,
                field_name="y",
            )
            z = _parse_float(
                normalized_fields[z_index],
                path=path,
                line_number=line_number,
                field_name="z",
            )

            yield PointRecord(
                raw_line=stripped,
                fields=normalized_fields,
                x=x,
                y=y,
                z=z,
                source_file=path,
                line_number=line_number,
                system=system,
            )
