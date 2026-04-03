"""抽出結果を一時ファイルへ逐次書き込み、成功時に本名へ確定する。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from .models import InputSystem


@dataclass(frozen=True, slots=True)
class OutputFileTarget:
    """1 つの出力ファイルの一時ファイルと本番ファイルを表す。"""

    system: InputSystem
    region_id: str
    final_path: Path
    temp_path: Path


class StreamingOutputWriter:
    """抽出結果を逐次書き込むためのライター。"""

    def __init__(self, output_dir: Path, region_ids: list[str]) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._targets: dict[tuple[InputSystem, str], OutputFileTarget] = {}
        self._handles: dict[tuple[InputSystem, str], TextIO] = {}
        self._counts: dict[InputSystem, dict[str, int]] = {
            "org": {region_id: 0 for region_id in region_ids},
            "grd": {region_id: 0 for region_id in region_ids},
        }
        self._committed = False

        for system in ("org", "grd"):
            for region_id in region_ids:
                final_path = self.output_dir / f"{system}_region{region_id}.txt"
                temp_path = self.output_dir / f".{system}_region{region_id}.txt.tmp"
                target = OutputFileTarget(
                    system=system,
                    region_id=region_id,
                    final_path=final_path,
                    temp_path=temp_path,
                )
                self._targets[(system, region_id)] = target
                self._handles[(system, region_id)] = temp_path.open(
                    "w", encoding="utf-8", newline="\n"
                )

    @property
    def counts(self) -> dict[InputSystem, dict[str, int]]:
        """領域ごとの書き込み件数を返す。"""
        return {
            system: dict(region_counts)
            for system, region_counts in self._counts.items()
        }

    def write(self, system: InputSystem, region_id: str, line: str) -> None:
        """指定した出力先へ 1 行を書き込む。"""
        handle = self._handles[(system, region_id)]
        handle.write(f"{line}\n")
        self._counts[system][region_id] += 1

    def commit(self) -> None:
        """一時ファイルを本番ファイルへ置き換える。"""
        if self._committed:
            return

        self._close_handles()
        for target in self._targets.values():
            os.replace(target.temp_path, target.final_path)
        self._committed = True

    def discard(self) -> None:
        """一時ファイルを削除する。"""
        self._close_handles()
        for target in self._targets.values():
            if target.temp_path.exists():
                target.temp_path.unlink()

    def _close_handles(self) -> None:
        for handle in self._handles.values():
            handle.close()
        self._handles.clear()
