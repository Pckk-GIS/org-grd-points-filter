"""点群抽出の中核処理をまとめるモジュール。"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from multiprocessing import Manager
from queue import Empty
from pathlib import Path
from typing import Protocol, TypedDict, cast

from .config import AppConfig
from .geometry import (
    point_in_bounding_box,
    point_in_convex_polygon,
)
from .models import Point2D, InputSystem, Region
from .output_writer import StreamingOutputWriter
from .point_reader import iter_input_files, iter_point_records
from .region_loader import load_regions
from .validation import require_positive_column_index


ProgressCallback = Callable[[str, dict[str, object]], None]
SYSTEM_ORDER = {"org": 0, "grd": 1}


class ProgressMessage(TypedDict):
    """ワーカーから main へ渡す進捗メッセージ。"""

    event: str
    payload: dict[str, object]


class ProgressQueueLike(Protocol):
    """進捗メッセージを受け取るキューの最小インターフェース。"""

    def put(self, message: ProgressMessage) -> None: ...

    def get_nowait(self) -> ProgressMessage: ...


@dataclass(frozen=True, slots=True)
class ProcessingReport:
    """処理結果の要約を表す。"""

    region_count: int
    input_files: dict[InputSystem, int]
    output_counts: dict[InputSystem, dict[int, int]]


@dataclass(frozen=True, slots=True)
class FileTask:
    """1 ファイル分の処理タスクを表す。"""

    system: InputSystem
    index: int
    total: int
    path: Path


@dataclass(frozen=True, slots=True)
class FileTaskResult:
    """1 ファイル分の処理結果を表す。"""

    system: InputSystem
    index: int
    total: int
    path: Path
    temp_dir: Path
    records: int
    matches: dict[int, int]


def _emit(
    progress_callback: ProgressCallback | None, event: str, payload: dict[str, object]
) -> None:
    if progress_callback is not None:
        progress_callback(event, payload)


def _drain_progress_queue(
    progress_queue: ProgressQueueLike | None, progress_callback: ProgressCallback | None
) -> None:
    if progress_queue is None or progress_callback is None:
        return

    while True:
        try:
            message = progress_queue.get_nowait()
        except Empty:
            return
        progress_callback(message["event"], message["payload"])


def _build_file_tasks(
    grouped_input_files: dict[InputSystem, list[Path]],
) -> list[FileTask]:
    tasks: list[FileTask] = []
    for system, paths in grouped_input_files.items():
        total = len(paths)
        for index, path in enumerate(paths, start=1):
            tasks.append(FileTask(system=system, index=index, total=total, path=path))
    return tasks


def _process_file_task(
    task: FileTask,
    regions: list[Region],
    *,
    x_col: int,
    y_col: int,
    z_col: int,
    temp_root: Path,
    progress_queue: ProgressQueueLike | None,
) -> FileTaskResult:
    temp_dir = temp_root / f"{task.system}_{task.index:04d}"
    writer = StreamingOutputWriter(temp_dir, len(regions))
    record_count = 0
    match_counts = {region.ordinal: 0 for region in regions}

    try:
        for record in iter_point_records(
            task.path,
            x_col=x_col,
            y_col=y_col,
            z_col=z_col,
            system=task.system,
        ):
            record_count += 1
            point = Point2D(record.x, record.y)
            for region in regions:
                if not point_in_bounding_box(point, region.bounding_box):
                    continue
                if point_in_convex_polygon(point, region.vertices):
                    writer.write(task.system, region.ordinal, record.raw_line)
                    match_counts[region.ordinal] += 1

            if progress_queue is not None and record_count % 100000 == 0:
                progress_queue.put(
                    {
                        "event": "file_progress",
                        "payload": {
                            "system": task.system,
                            "path": task.path,
                            "index": task.index,
                            "total": task.total,
                            "records": record_count,
                        },
                    }
                )

        writer.commit()
    except Exception:
        writer.discard()
        raise

    return FileTaskResult(
        system=task.system,
        index=task.index,
        total=task.total,
        path=task.path,
        temp_dir=temp_dir,
        records=record_count,
        matches=match_counts,
    )


def _merge_partial_result(
    writer: StreamingOutputWriter, result: FileTaskResult, regions: list[Region]
) -> None:
    for region in regions:
        part_path = result.temp_dir / f"{result.system}_region{region.ordinal}.txt"
        if not part_path.exists():
            continue
        with part_path.open("r", encoding="utf-8", newline="") as handle:
            for line in handle:
                writer.write(result.system, region.ordinal, line.rstrip("\r\n"))


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

    tasks = _build_file_tasks(grouped_input_files)
    input_file_counts: dict[InputSystem, int] = {
        "org": len(grouped_input_files["org"]),
        "grd": len(grouped_input_files["grd"]),
    }

    if not tasks:
        writer = StreamingOutputWriter(config.output_dir, len(regions))
        writer.commit()
        return ProcessingReport(
            region_count=len(regions),
            input_files=input_file_counts,
            output_counts=writer.counts,
        )

    temp_root = Path(tempfile.mkdtemp(prefix="point_filter_parallel_"))
    final_writer = StreamingOutputWriter(config.output_dir, len(regions))
    results_by_key: dict[tuple[InputSystem, int], FileTaskResult] = {}

    try:
        progress_queue: ProgressQueueLike | None = None
        manager = None
        try:
            if progress_callback is not None:
                manager = Manager()
                progress_queue = cast(ProgressQueueLike, manager.Queue())

            with ProcessPoolExecutor(max_workers=min(2, len(tasks))) as executor:
                futures = {
                    executor.submit(
                        _process_file_task,
                        task,
                        regions,
                        x_col=config.x_col,
                        y_col=config.y_col,
                        z_col=config.z_col,
                        temp_root=temp_root,
                        progress_queue=progress_queue,
                    ): task
                    for task in tasks
                }

                for task in tasks:
                    _emit(
                        progress_callback,
                        "file_start",
                        {
                            "system": task.system,
                            "path": task.path,
                            "index": task.index,
                            "total": task.total,
                        },
                    )

                remaining = set(futures)
                while remaining:
                    done, remaining = wait(
                        remaining, timeout=0.1, return_when=FIRST_COMPLETED
                    )
                    _drain_progress_queue(progress_queue, progress_callback)
                    for future in done:
                        task = futures[future]
                        result = future.result()
                        results_by_key[(task.system, task.index)] = result

                _drain_progress_queue(progress_queue, progress_callback)
        finally:
            if manager is not None:
                manager.shutdown()

        ordered_results = sorted(
            results_by_key.values(),
            key=lambda result: (SYSTEM_ORDER[result.system], result.index),
        )
        for result in ordered_results:
            _merge_partial_result(final_writer, result, regions)
            _emit(
                progress_callback,
                "file_done",
                {
                    "system": result.system,
                    "path": result.path,
                    "records": result.records,
                    "matches": result.matches,
                },
            )

        final_writer.commit()
        return ProcessingReport(
            region_count=len(regions),
            input_files=input_file_counts,
            output_counts=final_writer.counts,
        )
    except Exception:
        final_writer.discard()
        raise
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
