from pathlib import Path

from point_filter.config import AppConfig, RegionInput
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
        region_inputs=(RegionInput(path=region_csv),),
        input_dir=input_dir,
        output_dir=tmp_path / "output",
        org_x_col=2,
        org_y_col=3,
        org_z_col=4,
        grd_x_col=2,
        grd_y_col=3,
        grd_z_col=4,
    )

    report = process(
        config, progress_callback=lambda event, payload: events.append((event, payload))
    )

    assert [event for event, _payload in events[:3]] == [
        "region_file_loaded",
        "regions_loaded",
        "input_scan",
    ]
    assert sum(1 for event, _payload in events if event == "file_start") == 2
    assert sum(1 for event, _payload in events if event == "file_done") == 2
    assert report.region_count == 3
    assert report.input_files["org"] == 1
    assert report.input_files["grd"] == 1
    assert report.output_counts["org"]["regions_1"] == 1
    assert report.output_counts["org"]["regions_2"] == 1
    assert report.output_counts["grd"]["regions_3"] == 1
    assert (config.output_dir / "org_regionregions_1.txt").read_text(
        encoding="utf-8"
    ).strip() == "1,5,5,100"
    assert (config.output_dir / "org_regionregions_2.txt").read_text(
        encoding="utf-8"
    ).strip() == "2,25,25,200"
    assert (config.output_dir / "grd_regionregions_3.txt").read_text(
        encoding="utf-8"
    ).strip() == "1,45,45,300"


def test_process_skips_file_id_pairs_whose_grd_bounds_do_not_intersect_regions(
    tmp_path: Path,
) -> None:
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
    (input_dir / "alpha_org.txt").write_text("1,5,5,100\n", encoding="utf-8")
    (input_dir / "alpha_grd.txt").write_text("1,6,6,200\n", encoding="utf-8")
    (input_dir / "beta_org.txt").write_text("1,1000,1000,300\n", encoding="utf-8")
    (input_dir / "beta_grd.txt").write_text("1,1000,1000,400\n", encoding="utf-8")

    events: list[tuple[str, dict[str, object]]] = []
    config = AppConfig(
        region_inputs=(RegionInput(path=region_csv),),
        input_dir=input_dir,
        output_dir=tmp_path / "output",
        org_x_col=2,
        org_y_col=3,
        org_z_col=4,
        grd_x_col=2,
        grd_y_col=3,
        grd_z_col=4,
    )

    report = process(
        config, progress_callback=lambda event, payload: events.append((event, payload))
    )

    skipped_events = [
        payload for event, payload in events if event == "file_group_skipped"
    ]
    assert len(skipped_events) == 1
    assert skipped_events[0]["file_id"] == "beta"
    assert sum(1 for event, _payload in events if event == "file_start") == 2
    assert sum(1 for event, _payload in events if event == "file_done") == 2
    assert report.input_files["org"] == 2
    assert report.input_files["grd"] == 2
    assert report.output_counts["org"]["regions_1"] == 1
    assert report.output_counts["grd"]["regions_1"] == 1
    assert (config.output_dir / "org_regionregions_1.txt").read_text(
        encoding="utf-8"
    ).strip() == "1,5,5,100"
    assert (config.output_dir / "grd_regionregions_1.txt").read_text(
        encoding="utf-8"
    ).strip() == "1,6,6,200"


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
        region_inputs=(RegionInput(path=region_csv),),
        input_dir=input_dir,
        output_dir=tmp_path / "output",
        org_x_col=2,
        org_y_col=3,
        org_z_col=4,
        grd_x_col=2,
        grd_y_col=3,
        grd_z_col=4,
    )

    report = process(
        config, progress_callback=lambda event, payload: events.append((event, payload))
    )

    progress_events = [payload for event, payload in events if event == "file_progress"]
    assert len(progress_events) == 1
    assert progress_events[0]["records"] == 100_000
    assert report.output_counts["org"]["regions_1"] == 100_000


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
        region_inputs=(RegionInput(path=region_csv),),
        input_dir=input_dir,
        output_dir=tmp_path / "output",
        org_x_col=2,
        org_y_col=3,
        org_z_col=4,
        grd_x_col=2,
        grd_y_col=3,
        grd_z_col=4,
    )

    report = process(
        config, progress_callback=lambda event, payload: events.append((event, payload))
    )

    assert sum(1 for event, _payload in events if event == "file_group_skipped") == 1
    assert sum(1 for event, _payload in events if event == "file_start") == 0
    assert sum(1 for event, _payload in events if event == "file_done") == 0
    assert report.output_counts["org"]["regions_1"] == 0
    assert (config.output_dir / "org_regionregions_1.txt").read_text(
        encoding="utf-8"
    ) == ""


def test_process_uses_region_id_in_output_filename(tmp_path: Path) -> None:
    region_csv = tmp_path / "regions.csv"
    region_csv.write_text(
        "region_id,x,y\n4,0,0\n4,10,0\n4,10,10\n8,20,20\n8,30,20\n8,30,30\n",
        encoding="utf-8",
    )

    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "sample_org.txt").write_text("1,5,5,100\n", encoding="utf-8")

    config = AppConfig(
        region_inputs=(RegionInput(path=region_csv),),
        input_dir=input_dir,
        output_dir=tmp_path / "output",
        org_x_col=2,
        org_y_col=3,
        org_z_col=4,
        grd_x_col=2,
        grd_y_col=3,
        grd_z_col=4,
    )

    report = process(config)

    assert report.region_count == 2
    assert report.output_counts["org"]["regions_4"] == 1
    assert (config.output_dir / "org_regionregions_4.txt").read_text(
        encoding="utf-8"
    ).strip() == "1,5,5,100"
    assert (config.output_dir / "org_regionregions_8.txt").read_text(
        encoding="utf-8"
    ) == ""
