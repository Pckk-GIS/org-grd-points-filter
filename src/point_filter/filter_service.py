"""点群抽出の中核処理をまとめるモジュール。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .config import AppConfig
from .geometry import (
    bounding_boxes_intersect,
    point_in_bounding_box,
    point_in_convex_polygon,
)
from .models import Point2D, InputSystem
from .output_writer import StreamingOutputWriter
from .point_reader import (
    iter_input_files,
    iter_point_records,
    measure_input_file_bounds,
)
from .region_loader import load_regions
from .validation import require_positive_column_index


ProgressCallback = Callable[[str, dict[str, object]], None]


@dataclass(frozen=True, slots=True)
class ProcessingReport:
    """処理結果の要約を表す。"""

    region_count: int
    input_files: dict[InputSystem, int]
    output_counts: dict[InputSystem, dict[int, int]]


def _emit(
    progress_callback: ProgressCallback | None, event: str, payload: dict[str, object]
) -> None:
    if progress_callback is not None:
        progress_callback(event, payload)


def process(
    config: AppConfig, progress_callback: ProgressCallback | None = None
) -> ProcessingReport:
    """設定に従って点群を 3 領域へ振り分ける。"""
    require_positive_column_index(config.x_col, "X")
    require_positive_column_index(config.y_col, "Y")
    require_positive_column_index(config.z_col, "Z")

    regions = load_regions(config.region_csv)
    _emit(
        progress_callback,
        "regions_loaded",
        {
            "region_count": len(regions),
            "region_ids": [region.region_id for region in regions],
        },
    )

    grouped_input_files = iter_input_files(config.input_dir)
    writer = StreamingOutputWriter(config.output_dir, len(regions))
    _emit(
        progress_callback,
        "input_scan",
        {
            "org_files": len(grouped_input_files["org"]),
            "grd_files": len(grouped_input_files["grd"]),
            "total_files": len(grouped_input_files["org"])
            + len(grouped_input_files["grd"]),
        },
    )

    input_file_counts: dict[InputSystem, int] = {
        "org": len(grouped_input_files["org"]),
        "grd": len(grouped_input_files["grd"]),
    }

    try:
        for system, paths in grouped_input_files.items():
            for index, path in enumerate(paths, start=1):
                file_bounds = measure_input_file_bounds(
                    path,
                    x_col=config.x_col,
                    y_col=config.y_col,
                    z_col=config.z_col,
                )

                if file_bounds is None:
                    _emit(
                        progress_callback,
                        "file_skipped",
                        {
                            "system": system,
                            "path": path,
                            "reason": "有効な点がありません",
                            "index": index,
                            "total": len(paths),
                        },
                    )
                    continue

                if not any(
                    bounding_boxes_intersect(file_bounds, region.bounding_box)
                    for region in regions
                ):
                    _emit(
                        progress_callback,
                        "file_skipped",
                        {
                            "system": system,
                            "path": path,
                            "reason": "領域矩形と交差しません",
                            "index": index,
                            "total": len(paths),
                        },
                    )
                    continue

                _emit(
                    progress_callback,
                    "file_start",
                    {
                        "system": system,
                        "path": path,
                        "index": index,
                        "total": len(paths),
                    },
                )
                record_count = 0
                match_counts = {region.ordinal: 0 for region in regions}
                for record in iter_point_records(
                    path,
                    x_col=config.x_col,
                    y_col=config.y_col,
                    z_col=config.z_col,
                    system=system,
                ):
                    record_count += 1
                    point = Point2D(record.x, record.y)
                    for region in regions:
                        if not point_in_bounding_box(point, region.bounding_box):
                            continue
                        if point_in_convex_polygon(point, region.vertices):
                            writer.write(system, region.ordinal, record.raw_line)
                            match_counts[region.ordinal] += 1

                    if record_count % 100000 == 0:
                        _emit(
                            progress_callback,
                            "file_progress",
                            {
                                "system": system,
                                "path": path,
                                "index": index,
                                "total": len(paths),
                                "records": record_count,
                            },
                        )

                _emit(
                    progress_callback,
                    "file_done",
                    {
                        "system": system,
                        "path": path,
                        "records": record_count,
                        "matches": match_counts,
                    },
                )
        writer.commit()
    except Exception:
        writer.discard()
        raise

    return ProcessingReport(
        region_count=len(regions),
        input_files=input_file_counts,
        output_counts=writer.counts,
    )
