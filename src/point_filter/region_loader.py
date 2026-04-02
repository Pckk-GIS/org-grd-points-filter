from __future__ import annotations

import csv
from pathlib import Path

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

        regions: list[Region] = []
        current_region_id: str | None = None
        current_vertices: list[Point2D] = []
        seen_region_ids: set[str] = set()

        for line_number, row in enumerate(reader, start=2):
            if not row or not any(cell.strip() for cell in row):
                continue
            if len(row) < 3:
                raise DataFormatError(
                    f"Region CSV line {line_number} must have at least 3 columns"
                )

            region_id = row[0].strip()
            x = _parse_float(
                row[1].strip(), path=region_csv, line_number=line_number, field_name="x"
            )
            y = _parse_float(
                row[2].strip(), path=region_csv, line_number=line_number, field_name="y"
            )

            if current_region_id is None:
                current_region_id = region_id
            elif region_id != current_region_id:
                if region_id in seen_region_ids:
                    raise DataFormatError(
                        f"Region id {region_id!r} appears in non-contiguous blocks"
                    )
                ordinal = len(regions) + 1
                validate_region_vertices(current_vertices, str(ordinal))
                regions.append(
                    Region(
                        ordinal=ordinal,
                        region_id=current_region_id,
                        vertices=tuple(current_vertices),
                    )
                )
                seen_region_ids.add(current_region_id)
                current_region_id = region_id
                current_vertices = []

            current_vertices.append(Point2D(x=x, y=y))

        if current_region_id is None:
            raise DataFormatError(f"Region CSV has no data rows: {region_csv}")

        ordinal = len(regions) + 1
        validate_region_vertices(current_vertices, str(ordinal))
        regions.append(
            Region(
                ordinal=ordinal,
                region_id=current_region_id,
                vertices=tuple(current_vertices),
            )
        )

    if len(regions) != 3:
        raise DataFormatError(
            f"Region CSV must define exactly 3 regions, got {len(regions)}"
        )

    return regions
