"""領域 CSV を読み込み、凸包の領域列へ変換する。"""

from __future__ import annotations

import csv
from pathlib import Path

from .geometry import bounding_box_from_points, convex_hull
from .models import Point2D, Region
from .validation import DataFormatError, validate_region_vertices


EXPECTED_HEADER = ("region_id", "x", "y")


def _parse_float(value: str, *, path: Path, line_number: int, field_name: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise DataFormatError(
            f"Invalid {field_name} value in {path} line {line_number}: {value!r}"
        ) from exc


def load_regions(region_csv: Path) -> list[Region]:
    """領域 CSV から複数領域を読み込む。"""
    if not region_csv.exists():
        raise DataFormatError(f"Region CSV not found: {region_csv}")

    with region_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise DataFormatError(f"Region CSV is empty: {region_csv}") from exc

        normalized_header = tuple(column.strip().lower() for column in header)
        if normalized_header != EXPECTED_HEADER:
            raise DataFormatError(
                f"Region CSV header must be {EXPECTED_HEADER}, got {tuple(header)}"
            )

        region_points: dict[str, list[Point2D]] = {}
        region_order: list[str] = []

        for line_number, row in enumerate(reader, start=2):
            if not row or not any(cell.strip() for cell in row):
                continue
            if len(row) < 3:
                raise DataFormatError(
                    f"Region CSV line {line_number} must have at least 3 columns"
                )

            region_id = row[0].strip()
            if not region_id:
                raise DataFormatError(
                    f"Region CSV line {line_number} must have a non-empty region_id"
                )
            x = _parse_float(
                row[1].strip(), path=region_csv, line_number=line_number, field_name="x"
            )
            y = _parse_float(
                row[2].strip(), path=region_csv, line_number=line_number, field_name="y"
            )

            if region_id not in region_points:
                region_points[region_id] = []
                region_order.append(region_id)

            region_points[region_id].append(Point2D(x=x, y=y))

        if not region_order:
            raise DataFormatError(f"Region CSV has no data rows: {region_csv}")

        regions: list[Region] = []
        for ordinal, region_id in enumerate(region_order, start=1):
            vertices = convex_hull(region_points[region_id])
            validate_region_vertices(vertices, region_id)
            regions.append(
                Region(
                    ordinal=ordinal,
                    region_id=region_id,
                    vertices=vertices,
                    bounding_box=bounding_box_from_points(vertices),
                )
            )

    return regions
