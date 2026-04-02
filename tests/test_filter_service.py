from pathlib import Path

from point_filter.config import AppConfig
from point_filter.filter_service import process


def test_process_emits_progress_events(tmp_path: Path) -> None:
    region_csv = tmp_path / "regions.csv"
    region_csv.write_text(
        "region_id,x,y\n"
        "1,0,0\n"
        "1,10,0\n"
        "1,10,10\n"
        "2,20,20\n"
        "2,30,20\n"
        "2,30,30\n"
        "3,40,40\n"
        "3,50,40\n"
        "3,50,50\n",
        encoding="utf-8",
    )

    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "sample_org.txt").write_text(
        "1,5,5,100\n2,25,25,200\n", encoding="utf-8"
    )
    (input_dir / "sample_grd.txt").write_text("1,45,45,300\n", encoding="utf-8")

    events: list[tuple[str, dict[str, object]]] = []
    config = AppConfig(
        region_csv=region_csv,
        input_dir=input_dir,
        output_dir=tmp_path / "output",
        x_col=2,
        y_col=3,
        z_col=4,
    )

    report = process(
        config, progress_callback=lambda event, payload: events.append((event, payload))
    )

    assert [event for event, _payload in events[:2]] == ["regions_loaded", "input_scan"]
    assert sum(1 for event, _payload in events if event == "file_start") == 2
    assert sum(1 for event, _payload in events if event == "file_done") == 2
    assert report.region_count == 3
    assert report.input_files["org"] == 1
    assert report.input_files["grd"] == 1
    assert report.output_counts["org"][1] == 1
    assert report.output_counts["org"][2] == 1
    assert report.output_counts["grd"][3] == 1
    assert (config.output_dir / "org_region1.txt").read_text(
        encoding="utf-8"
    ).strip() == "1,5,5,100"
    assert (config.output_dir / "org_region2.txt").read_text(
        encoding="utf-8"
    ).strip() == "2,25,25,200"
    assert (config.output_dir / "grd_region3.txt").read_text(
        encoding="utf-8"
    ).strip() == "1,45,45,300"


def test_process_emits_progress_every_100000_lines(tmp_path: Path) -> None:
    region_csv = tmp_path / "regions.csv"
    region_csv.write_text(
        "region_id,x,y\n"
        "1,0,0\n"
        "1,10,0\n"
        "1,10,10\n"
        "2,20,20\n"
        "2,30,20\n"
        "2,30,30\n"
        "3,40,40\n"
        "3,50,40\n"
        "3,50,50\n",
        encoding="utf-8",
    )

    input_dir = tmp_path / "input"
    input_dir.mkdir()
    sample_lines = ["1,5,5,100" for _ in range(100_000)]
    (input_dir / "huge_org.txt").write_text(
        "\n".join(sample_lines) + "\n", encoding="utf-8"
    )

    events: list[tuple[str, dict[str, object]]] = []
    config = AppConfig(
        region_csv=region_csv,
        input_dir=input_dir,
        output_dir=tmp_path / "output",
        x_col=2,
        y_col=3,
        z_col=4,
    )

    report = process(
        config, progress_callback=lambda event, payload: events.append((event, payload))
    )

    progress_events = [payload for event, payload in events if event == "file_progress"]
    assert len(progress_events) == 1
    assert progress_events[0]["records"] == 100_000
    assert report.output_counts["org"][1] == 100_000


def test_process_writes_empty_output_when_no_points_match(tmp_path: Path) -> None:
    region_csv = tmp_path / "regions.csv"
    region_csv.write_text(
        "region_id,x,y\n"
        "1,0,0\n"
        "1,10,0\n"
        "1,10,10\n"
        "2,20,20\n"
        "2,30,20\n"
        "2,30,30\n"
        "3,40,40\n"
        "3,50,40\n"
        "3,50,50\n",
        encoding="utf-8",
    )

    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "far_org.txt").write_text("1,1000,1000,1\n", encoding="utf-8")

    events: list[tuple[str, dict[str, object]]] = []
    config = AppConfig(
        region_csv=region_csv,
        input_dir=input_dir,
        output_dir=tmp_path / "output",
        x_col=2,
        y_col=3,
        z_col=4,
    )

    report = process(
        config, progress_callback=lambda event, payload: events.append((event, payload))
    )

    assert sum(1 for event, _payload in events if event == "file_start") == 1
    assert sum(1 for event, _payload in events if event == "file_done") == 1
    assert report.output_counts["org"][1] == 0
    assert (config.output_dir / "org_region1.txt").read_text(encoding="utf-8") == ""
