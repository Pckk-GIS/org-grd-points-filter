# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import tomllib

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


ROOT = Path(SPECPATH).resolve()
PROJECT_ROOT = ROOT

with (PROJECT_ROOT / "pyproject.toml").open("rb") as handle:
    version = tomllib.load(handle)["project"]["version"]

app_name = f"point-filter-gui-v{version}"
rust_cli = PROJECT_ROOT / "point-filter-rs" / "target" / "release" / "point-filter-cli.exe"
binaries = []
if rust_cli.exists():
    binaries.append((str(rust_cli), "."))

pyogrio_libs_dir = PROJECT_ROOT / ".venv" / "Lib" / "site-packages" / "pyogrio.libs"
if pyogrio_libs_dir.exists():
    binaries.extend((str(path), ".") for path in pyogrio_libs_dir.glob("*.dll"))

datas = collect_data_files("pyogrio", includes=["gdal_data/*", "proj_data/*"])
hiddenimports = collect_submodules("pyogrio")

a = Analysis(
    ["gui_main.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)
