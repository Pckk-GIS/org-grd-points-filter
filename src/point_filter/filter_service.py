from __future__ import annotations

from .config import AppConfig
from .geometry import point_in_convex_polygon
from .models import Point2D, InputSystem
from .point_reader import iter_input_files, iter_point_records
from .region_loader import load_regions
from .validation import require_positive_column_index


OutputBuckets = dict[InputSystem, dict[int, list[str]]]


def _empty_buckets(region_count: int) -> OutputBuckets:
    return {
        "org": {index: [] for index in range(1, region_count + 1)},
        "grd": {index: [] for index in range(1, region_count + 1)},
    }


def process(config: AppConfig) -> OutputBuckets:
    require_positive_column_index(config.x_col, "X")
    require_positive_column_index(config.y_col, "Y")
    require_positive_column_index(config.z_col, "Z")

    regions = load_regions(config.region_csv)
    buckets = _empty_buckets(len(regions))
    grouped_input_files = iter_input_files(config.input_dir)

    for system, paths in grouped_input_files.items():
        for path in paths:
            for record in iter_point_records(
                path,
                x_col=config.x_col,
                y_col=config.y_col,
                z_col=config.z_col,
                system=system,
            ):
                point = Point2D(record.x, record.y)
                for region in regions:
                    if point_in_convex_polygon(point, region.vertices):
                        buckets[system][region.ordinal].append(record.raw_line)

    return buckets
