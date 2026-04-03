from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from point_filter.config import AppConfig
from point_filter.engine import run_rust_engine


def test_run_rust_engine_uses_override_command(tmp_path: Path) -> None:
    region_csv = tmp_path / "regions.csv"
    region_csv.write_text(
        "region_id,x,y\n4,0,0\n4,10,0\n4,10,10\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "org_region4.txt").write_text("1,5,5,100\n", encoding="utf-8")
    (output_dir / "grd_region4.txt").write_text("", encoding="utf-8")
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    config = AppConfig(
        region_csv=region_csv,
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
    assert "--org-x-col" in called_command
    assert "--grd-z-col" in called_command
    assert report.output_counts["org"]["4"] == 1
    assert report.output_counts["grd"]["4"] == 0
