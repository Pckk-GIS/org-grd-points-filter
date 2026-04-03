from pathlib import Path

import geopandas as gpd
import pyogrio
import pytest
from shapely.geometry import MultiPolygon, Polygon

from point_filter.config import RegionInput
from point_filter.region_loader import load_regions
from point_filter.validation import DataFormatError, GeometryError


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

    result = load_regions([RegionInput(path=csv_path)])
    regions = result.regions

    assert len(regions) == 3
    assert regions[0].ordinal == 1
    assert regions[0].region_id == "regions_1"
    assert [(vertex.x, vertex.y) for vertex in regions[0].vertices] == [
        (0.0, 0.0),
        (10.0, 0.0),
        (10.0, 10.0),
    ]


def test_load_regions_accepts_more_than_three_regions(tmp_path: Path):
    csv_path = tmp_path / "regions.csv"
    csv_path.write_text(
        "region_id,x,y\n"
        "4,0,0\n"
        "4,10,0\n"
        "4,10,10\n"
        "5,20,20\n"
        "5,30,20\n"
        "5,30,30\n"
        "6,40,40\n"
        "6,50,40\n"
        "6,50,50\n"
        "7,60,60\n"
        "7,70,60\n"
        "7,70,70\n",
        encoding="utf-8",
    )

    regions = load_regions([RegionInput(path=csv_path)]).regions

    assert [region.region_id for region in regions] == [
        "regions_4",
        "regions_5",
        "regions_6",
        "regions_7",
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
        load_regions([RegionInput(path=csv_path)])


def test_load_regions_reads_shapefile_polygons(tmp_path: Path) -> None:
    shp_path = tmp_path / "zones.shp"
    frame = gpd.GeoDataFrame(
        {
            "geometry": [
                Polygon([(0, 0), (10, 0), (10, 10), (0, 0)]),
                Polygon([(20, 20), (30, 20), (30, 30), (20, 20)]),
            ]
        }
    )
    pyogrio.write_dataframe(frame, shp_path, driver="ESRI Shapefile")

    result = load_regions([RegionInput(path=shp_path)])

    assert [region.region_id for region in result.regions] == ["zones_1", "zones_2"]


def test_load_regions_reads_gpkg_first_layer_by_default(tmp_path: Path) -> None:
    gpkg_path = tmp_path / "layers.gpkg"
    first = gpd.GeoDataFrame(
        {"geometry": [Polygon([(0, 0), (10, 0), (10, 10), (0, 0)])]}
    )
    second = gpd.GeoDataFrame(
        {"geometry": [Polygon([(20, 20), (30, 20), (30, 30), (20, 20)])]}
    )
    pyogrio.write_dataframe(first, gpkg_path, layer="alpha", driver="GPKG")
    pyogrio.write_dataframe(second, gpkg_path, layer="beta", driver="GPKG", append=True)

    result = load_regions([RegionInput(path=gpkg_path)])

    assert [region.region_id for region in result.regions] == ["layers_alpha_1"]


def test_load_regions_rejects_multipolygon(tmp_path: Path) -> None:
    gpkg_path = tmp_path / "multi.gpkg"
    frame = gpd.GeoDataFrame(
        {
            "geometry": [
                MultiPolygon(
                    [
                        Polygon([(0, 0), (10, 0), (10, 10), (0, 0)]),
                        Polygon([(20, 20), (30, 20), (30, 30), (20, 20)]),
                    ]
                )
            ]
        }
    )
    pyogrio.write_dataframe(frame, gpkg_path, layer="alpha", driver="GPKG")

    with pytest.raises(DataFormatError, match="Only Polygon is supported"):
        load_regions([RegionInput(path=gpkg_path)])
