from __future__ import annotations

import re
import sys
from pathlib import Path


def extract_section(changelog_path: Path, version: str) -> str:
    text = changelog_path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"^## \[{re.escape(version)}\] - .*$\n(?P<body>.*?)(?=^## \[|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if match is None:
        raise SystemExit(f"CHANGELOG.md にバージョン {version} の節が見つかりません。")
    return match.group(0).strip() + "\n"


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: extract_changelog.py <CHANGELOG.md> <version>")

    changelog_path = Path(sys.argv[1])
    version = sys.argv[2]
    print(extract_section(changelog_path, version), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
