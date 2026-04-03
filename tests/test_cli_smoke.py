from pathlib import Path

from point_filter.cli import main


def test_cli_smoke(tmp_path: Path):
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

    output_dir = tmp_path / "output"
    code = main(
        [
            "--region-file",
            str(region_csv),
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
            "--x-col",
            "2",
            "--y-col",
            "3",
            "--z-col",
            "4",
        ]
    )

    assert code == 0
    assert (output_dir / "org_regionregions_1.txt").read_text(
        encoding="utf-8"
    ).strip() == "1,5,5,100"
    assert (output_dir / "org_regionregions_2.txt").read_text(
        encoding="utf-8"
    ).strip() == "2,25,25,200"
    assert (output_dir / "grd_regionregions_3.txt").read_text(
        encoding="utf-8"
    ).strip() == "1,45,45,300"


def test_cli_supports_system_specific_columns(tmp_path: Path):
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
    (input_dir / "sample_org.txt").write_text("1,5,5,100\n", encoding="utf-8")
    (input_dir / "sample_grd.txt").write_text("45,45,300,1\n", encoding="utf-8")

    output_dir = tmp_path / "output"
    code = main(
        [
            "--region-file",
            str(region_csv),
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
            "--org-x-col",
            "2",
            "--org-y-col",
            "3",
            "--org-z-col",
            "4",
            "--grd-x-col",
            "1",
            "--grd-y-col",
            "2",
            "--grd-z-col",
            "3",
        ]
    )

    assert code == 0
    assert (output_dir / "org_regionregions_1.txt").read_text(
        encoding="utf-8"
    ).strip() == "1,5,5,100"
    assert (output_dir / "grd_regionregions_3.txt").read_text(
        encoding="utf-8"
    ).strip() == "45,45,300,1"


def test_cli_accepts_multiple_region_files(tmp_path: Path):
    first_region = tmp_path / "first.csv"
    first_region.write_text(
        "region_id,x,y\n1,0,0\n1,10,0\n1,10,10\n",
        encoding="utf-8",
    )
    second_region = tmp_path / "second.csv"
    second_region.write_text(
        "region_id,x,y\n2,20,20\n2,30,20\n2,30,30\n",
        encoding="utf-8",
    )

    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "sample_org.txt").write_text(
        "1,5,5,100\n2,25,25,200\n", encoding="utf-8"
    )

    output_dir = tmp_path / "output"
    code = main(
        [
            "--region-file",
            str(first_region),
            "--region-file",
            str(second_region),
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
            "--x-col",
            "2",
            "--y-col",
            "3",
            "--z-col",
            "4",
        ]
    )

    assert code == 0
    assert (output_dir / "org_regionfirst_1.txt").read_text(
        encoding="utf-8"
    ).strip() == "1,5,5,100"
    assert (output_dir / "org_regionsecond_2.txt").read_text(
        encoding="utf-8"
    ).strip() == "2,25,25,200"
