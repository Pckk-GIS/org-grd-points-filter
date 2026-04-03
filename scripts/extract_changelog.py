from __future__ import annotations

import re
import sys
from pathlib import Path


def extract_section(changelog_path: Path, version: str) -> str:
    text = changelog_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    pattern = re.compile(r"^## \[(?P<version>[^\]]+)\] - .*$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    target_index = next(
        (
            index
            for index, match in enumerate(matches)
            if match.group("version") == version
        ),
        None,
    )
    if target_index is None:
        raise SystemExit(f"CHANGELOG.md にバージョン {version} の節が見つかりません。")
    start = matches[target_index].start()
    end = (
        matches[target_index + 1].start()
        if target_index + 1 < len(matches)
        else len(text)
    )
    return text[start:end].strip() + "\n"


def main() -> int:
    if len(sys.argv) not in {3, 4}:
        raise SystemExit(
            "usage: extract_changelog.py <CHANGELOG.md> <version> [output_path]"
        )

    changelog_path = Path(sys.argv[1])
    version = sys.argv[2]
    content = extract_section(changelog_path, version)
    if len(sys.argv) == 4:
        output_path = Path(sys.argv[3])
        output_path.write_text(content, encoding="utf-8")
    else:
        sys.stdout.buffer.write(content.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
