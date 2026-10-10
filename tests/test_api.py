
import geopandas as gpd
import pytest
from shapely.geometry import Polygon, LineString

from fastapi.testclient import TestClient
from app.main import app
from app.services.geospatial import get_file_info

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_reject_invalid_file_type():
    response = client.post(
        "/api/files/",
        files={"file": ("document.pdf", b"dummy content", "application/pdf")},
    )
    assert response.status_code == 400


def test_polygon_area():
    gdf = gpd.GeoDataFrame(
        {"name": ["test"]},
        geometry=[
            Polygon([
                (77.0, 12.0),
                (77.01, 12.0),
                (77.01, 12.01),
                (77.0, 12.01),
                (77.0, 12.0),
            ])
        ],
        crs="EPSG:4326",
    )

    result = get_file_info(gdf)
    feature = result["features"][0]

    assert feature["area_m2"] > 0
    assert result["measurement_crs"] != "EPSG:4326"


def test_line_length():
    gdf = gpd.GeoDataFrame(
        {"name": ["test"]},
        geometry=[LineString([(77.0, 12.0), (77.01, 12.01)])],
        crs="EPSG:4326",
    )

    result = get_file_info(gdf)
    assert result["features"][0]["length_m"] > 0


def test_missing_crs_is_rejected():
    gdf = gpd.GeoDataFrame(
        geometry=[Polygon([
            (0, 0), (1, 0), (1, 1), (0, 1), (0, 0)
        ])]
    )

    with pytest.raises(ValueError, match="no CRS"):
        get_file_info(gdf)
