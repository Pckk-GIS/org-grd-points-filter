from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .models import InputSystem, PointRecord
from .validation import DataFormatError


def detect_system_from_filename(path: Path) -> InputSystem | None:
    stem = path.stem.lower()
    if stem.endswith("_org"):
        return "org"
    if stem.endswith("_grd"):
        return "grd"
    return None


def iter_input_files(input_dir: Path) -> dict[InputSystem, list[Path]]:
    grouped: dict[InputSystem, list[Path]] = {"org": [], "grd": []}
    if not input_dir.exists():
        raise DataFormatError(f"Input directory not found: {input_dir}")

    for path in sorted(input_dir.glob("*.txt")):
        system = detect_system_from_filename(path)
        if system is None:
            continue
        grouped[system].append(path)
    return grouped


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


def iter_point_records(
    path: Path,
    *,
    x_col: int,
    y_col: int,
    z_col: int,
    system: InputSystem,
) -> Iterable[PointRecord]:
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
