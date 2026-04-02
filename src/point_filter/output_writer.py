from __future__ import annotations

from pathlib import Path

from .models import InputSystem


def write_outputs(
    output_dir: Path, buckets: dict[InputSystem, dict[int, list[str]]]
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for system, region_map in buckets.items():
        for ordinal, lines in region_map.items():
            output_path = output_dir / f"{system}_region{ordinal}.txt"
            content = "\n".join(lines)
            if lines:
                content += "\n"
            output_path.write_text(content, encoding="utf-8")
