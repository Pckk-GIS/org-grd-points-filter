from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

import pytest

from point_filter.config import AppConfig, RegionInput
from point_filter.engine import run_rust_engine
from point_filter.validation import ConfigurationError


def test_run_rust_engine_uses_override_command(tmp_path: Path) -> None:
    region_csv = tmp_path / "regions.csv"
    region_csv.write_text(
        "region_id,x,y\n4,0,0\n4,10,0\n4,10,10\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "org_regionregions_4.txt").write_text("1,5,5,100\n", encoding="utf-8")
    (output_dir / "grd_regionregions_4.txt").write_text("", encoding="utf-8")
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    config = AppConfig(
        region_inputs=(RegionInput(path=region_csv),),
        input_dir=input_dir,
        output_dir=output_dir,
        org_x_col=2,
        org_y_col=3,
        org_z_col=4,
        grd_x_col=2,
        grd_y_col=3,
        grd_z_col=4,
    )

    with patch(
        "point_filter.engine.subprocess.run",
        return_value=CompletedProcess(
            args=["dummy"], returncode=0, stdout="", stderr=""
        ),
    ) as mocked_run:
        report = run_rust_engine(config, rust_command=["dummy", "--flag"])

    called_command = mocked_run.call_args.args[0]
    assert called_command[:2] == ["dummy", "--flag"]
    assert "--region-csv" in called_command
    assert "--org-x-col" in called_command
    assert "--grd-z-col" in called_command
    assert report.output_counts["org"]["regions_4"] == 1
    assert report.output_counts["grd"]["regions_4"] == 0


def test_run_rust_engine_rejects_multiple_region_files(tmp_path: Path) -> None:
    first = tmp_path / "regions.csv"
    second = tmp_path / "other.csv"
    first.write_text("region_id,x,y\n1,0,0\n1,10,0\n1,10,10\n", encoding="utf-8")
    second.write_text("region_id,x,y\n2,0,0\n2,10,0\n2,10,10\n", encoding="utf-8")

    config = AppConfig(
        region_inputs=(RegionInput(path=first), RegionInput(path=second)),
        input_dir=tmp_path / "input",
        output_dir=tmp_path / "output",
        org_x_col=2,
        org_y_col=3,
        org_z_col=4,
        grd_x_col=2,
        grd_y_col=3,
        grd_z_col=4,
    )

    with pytest.raises(ConfigurationError, match="multiple region files"):
        run_rust_engine(config, rust_command=["dummy"])
