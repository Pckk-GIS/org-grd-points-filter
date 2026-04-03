"""領域定義ファイルを読み込み、内部の Region モデルへ変換する。"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import pyogrio
from shapely.geometry import Polygon

from .config import RegionInput
from .geometry import bounding_box_from_points, convex_hull
from .models import Point2D, Region
from .validation import DataFormatError, validate_region_vertices


EXPECTED_HEADER = ("region_id", "x", "y")
VECTOR_SUFFIXES = {".shp", ".gpkg"}


@dataclass(frozen=True, slots=True)
class RegionLoadResult:
    """領域読込結果を表す。"""

    regions: list[Region]
    warnings: list[str]
    summaries: list[dict[str, object]]


def _parse_float(value: str, *, path: Path, line_number: int, field_name: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise DataFormatError(
            f"Invalid {field_name} value in {path} line {line_number}: {value!r}"
        ) from exc


def load_regions(
    region_inputs: list[RegionInput] | tuple[RegionInput, ...],
) -> RegionLoadResult:
    """複数の領域入力から Region 一覧を構築する。"""
    if not region_inputs:
        raise DataFormatError("At least one region file must be specified")

    regions: list[Region] = []
    warnings: list[str] = []
    summaries: list[dict[str, object]] = []
    region_ids: set[str] = set()
    ordinal = 1

    for region_input in region_inputs:
        path = region_input.path
        suffix = path.suffix.lower()
        if suffix == ".csv":
            loaded_regions = _load_regions_from_csv(path)
            warnings.extend(_warn_for_known_crs(path))
            summaries.append(
                {
                    "path": path,
                    "format": "csv",
                    "layer": None,
                    "feature_count": len(loaded_regions),
                    "region_count": len(loaded_regions),
                    "geometry_type": "CSV point groups",
                }
            )
        elif suffix in VECTOR_SUFFIXES:
            loaded_regions, vector_warnings, summary = _load_regions_from_vector(
                region_input
            )
            warnings.extend(vector_warnings)
            summaries.append(summary)
        else:
            raise DataFormatError(f"Unsupported region file format: {path}")

        for region in loaded_regions:
            if region.region_id in region_ids:
                raise DataFormatError(
                    f"Region id must be unique across all region files: {region.region_id}"
                )
            region_ids.add(region.region_id)
            regions.append(
                Region(
                    ordinal=ordinal,
                    region_id=region.region_id,
                    vertices=region.vertices,
                    bounding_box=region.bounding_box,
                )
            )
            ordinal += 1

    return RegionLoadResult(regions=regions, warnings=warnings, summaries=summaries)


def list_gpkg_layers(path: Path) -> list[str]:
    """GPKG に含まれるレイヤ名一覧を返す。"""
    if path.suffix.lower() != ".gpkg":
        return []
    try:
        return [str(layer_info[0]) for layer_info in pyogrio.list_layers(path)]
    except Exception as exc:  # pragma: no cover - pyogrio specific failure
        raise DataFormatError(f"Failed to read GPKG layers from {path}: {exc}") from exc


def summarize_region_input(region_input: RegionInput) -> str:
    """GUI 表示用に領域ファイルの扱いを短く要約する。"""
    path = region_input.path
    suffix = path.suffix.lower()

    if suffix == ".csv":
        region_ids: set[str] = set()
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            try:
                next(reader)
            except StopIteration as exc:
                raise DataFormatError(f"Region CSV is empty: {path}") from exc
            for row in reader:
                if not row or not any(cell.strip() for cell in row):
                    continue
                if row[0].strip():
                    region_ids.add(row[0].strip())
        return f"CSV です。{len(region_ids)} 個の region_id を {len(region_ids)} 領域として扱います。"

    if suffix == ".shp":
        info = pyogrio.read_info(path)
        feature_count = int(info.get("features") or 0)
        return (
            f"SHP です。{feature_count} 地物を {feature_count} 領域として扱います。"
            "Polygon のみ対応です。"
        )

    if suffix == ".gpkg":
        layer = _resolve_layer(path, region_input.layer)
        info = pyogrio.read_info(path, layer=layer)
        feature_count = int(info.get("features") or 0)
        return (
            f"GPKG です。レイヤ「{layer}」の {feature_count} 地物を {feature_count} 領域として扱います。"
            "Polygon のみ対応です。"
        )

    return "対応していない形式です。"


def _load_regions_from_csv(region_csv: Path) -> list[Region]:
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

        file_stem = _sanitize_identifier(region_csv.stem)
        region_points: dict[str, list[Point2D]] = {}
        region_order: list[str] = []

        for line_number, row in enumerate(reader, start=2):
            if not row or not any(cell.strip() for cell in row):
                continue
            if len(row) < 3:
                raise DataFormatError(
                    f"Region CSV line {line_number} must have at least 3 columns"
                )

            raw_region_id = row[0].strip()
            if not raw_region_id:
                raise DataFormatError(
                    f"Region CSV line {line_number} must have a non-empty region_id"
                )
            region_id = f"{file_stem}_{_sanitize_identifier(raw_region_id)}"
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

        return _regions_from_point_groups(region_points, region_order)


def _load_regions_from_vector(
    region_input: RegionInput,
) -> tuple[list[Region], list[str], dict[str, object]]:
    path = region_input.path
    if not path.exists():
        raise DataFormatError(f"Region file not found: {path}")

    layer = _resolve_layer(path, region_input.layer)
    warnings = _warn_for_known_crs(path, layer)
    file_stem = _sanitize_identifier(path.stem)
    layer_prefix = ""
    if path.suffix.lower() == ".gpkg":
        if layer is None:
            raise DataFormatError(f"GPKG layer resolution failed: {path}")
        layer_prefix = f"_{_sanitize_identifier(layer)}"

    try:
        frame = pyogrio.read_dataframe(path, layer=layer)
    except Exception as exc:  # pragma: no cover - pyogrio specific failure
        raise DataFormatError(f"Failed to read region file {path}: {exc}") from exc

    if frame.empty:
        raise DataFormatError(f"Region file has no features: {path}")

    regions: list[Region] = []
    for index, geom in enumerate(frame.geometry, start=1):
        if geom is None:
            raise DataFormatError(f"Region feature {index} in {path} has no geometry")
        if geom.geom_type != "Polygon":
            raise DataFormatError(
                f"Only Polygon is supported, got {geom.geom_type} in {path}"
            )
        if not isinstance(geom, Polygon):
            raise DataFormatError(
                f"Failed to interpret Polygon geometry in {path} feature {index}"
            )

        vertices = tuple(
            Point2D(x=float(x), y=float(y)) for x, y in list(geom.exterior.coords)[:-1]
        )
        region_id = f"{file_stem}{layer_prefix}_{index}"
        validate_region_vertices(vertices, region_id)
        regions.append(
            Region(
                ordinal=index,
                region_id=region_id,
                vertices=vertices,
                bounding_box=bounding_box_from_points(vertices),
            )
        )

    summary = {
        "path": path,
        "format": path.suffix.lower().lstrip("."),
        "layer": layer,
        "feature_count": len(frame),
        "region_count": len(regions),
        "geometry_type": "Polygon",
    }
    return regions, warnings, summary


def _resolve_layer(path: Path, configured_layer: str | None) -> str | None:
    if path.suffix.lower() != ".gpkg":
        return None

    layers = list_gpkg_layers(path)
    if not layers:
        raise DataFormatError(f"GPKG has no layers: {path}")
    if configured_layer:
        if configured_layer not in layers:
            raise DataFormatError(
                f"GPKG layer not found in {path}: {configured_layer}. Available: {layers}"
            )
        return configured_layer
    return layers[0]


def _regions_from_point_groups(
    region_points: dict[str, list[Point2D]], region_order: list[str]
) -> list[Region]:
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


def _sanitize_identifier(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.strip())
    cleaned = cleaned.strip("_")
    return cleaned or "region"


def _warn_for_known_crs(path: Path, layer: str | None = None) -> list[str]:
    if path.suffix.lower() not in VECTOR_SUFFIXES:
        return []

    try:
        info = pyogrio.read_info(path, layer=layer)
    except Exception:
        return []

    crs = info.get("crs")
    if not crs:
        return []

    target = f"{path}" if layer is None else f"{path}:{layer}"
    return [
        f"CRS detected for region file {target}: {crs}. Point input CRS is not checked; processing continues."
    ]
