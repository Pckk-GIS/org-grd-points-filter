from pathlib import Path

import pytest

from point_filter.region_loader import load_regions
from point_filter.validation import GeometryError


def test_load_regions(tmp_path: Path):
    csv_path = tmp_path / "regions.csv"
    csv_path.write_text(
        "region_id,x,y\n"
        "1,10,10\n"
        "2,30,30\n"
        "1,0,0\n"
        "3,50,50\n"
        "2,20,20\n"
        "1,10,0\n"
        "3,40,40\n"
        "2,30,20\n"
        "3,50,40\n",
        encoding="utf-8",
    )

    regions = load_regions(csv_path)

    assert len(regions) == 3
    assert regions[0].ordinal == 1
    assert regions[0].region_id == "1"
    assert [(vertex.x, vertex.y) for vertex in regions[0].vertices] == [
        (0.0, 0.0),
        (10.0, 0.0),
        (10.0, 10.0),
    ]


def test_load_regions_rejects_interior_points(tmp_path: Path):
    csv_path = tmp_path / "regions.csv"
    csv_path.write_text(
        "region_id,x,y\n"
        "1,0,0\n"
        "1,10,0\n"
        "1,10,10\n"
        "1,5,5\n"
        "2,20,0\n"
        "2,30,0\n"
        "2,30,10\n"
        "3,40,40\n"
        "3,50,40\n"
        "3,50,50\n",
        encoding="utf-8",
    )

    with pytest.raises(GeometryError):
        load_regions(csv_path)
