
import math
import os
import tempfile
import zipfile

import geopandas as gpd
from pyproj import Geod


def process_file(file_path: str, filename: str):
    filename = filename.lower()

    if filename.endswith(".kml"):
        gdf = gpd.read_file(file_path, driver="KML")

    elif filename.endswith(".zip"):
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                # Prevent ZIP path traversal
                root_path = os.path.realpath(temp_dir) + os.sep

                for member in zip_ref.infolist():
                    target = os.path.realpath(
                        os.path.join(temp_dir, member.filename)
                    )

                    if not target.startswith(root_path):
                        raise ValueError("Unsafe ZIP file contents")

                zip_ref.extractall(temp_dir)

            shp_files = [
                os.path.join(root, name)
                for root, _, files in os.walk(temp_dir)
                for name in files
                if name.lower().endswith(".shp")
            ]

            if not shp_files:
                raise ValueError("ZIP does not contain a Shapefile")

            # Process while extracted files still exist
            gdf = gpd.read_file(shp_files[0])
            return get_file_info(gdf)

    else:
        raise ValueError("Only KML and ZIP files are supported")

    return get_file_info(gdf)


def get_file_info(gdf):
    measurements = []

    if gdf.crs is None:
        raise ValueError(
            "Input file has no CRS; accurate measurements cannot be calculated"
        )

    # Convert coordinates to longitude/latitude for geodesic calculations
    geographic_gdf = gdf.to_crs("EPSG:4326")

    # Global equal-area projection for polygon area
    equal_area_gdf = gdf.to_crs("EPSG:6933")

    # WGS84 ellipsoid for measuring line length over Earth's surface
    geod = Geod(ellps="WGS84")

    for index, row in gdf.iterrows():
        geometry = row.geometry
        geographic_geometry = geographic_gdf.geometry.loc[index]
        area_geometry = equal_area_gdf.geometry.loc[index]

        feature = {
            "feature_id": (
                int(index) if isinstance(index, int) else str(index)
            ),
            "geometry_type": (
                geometry.geom_type if geometry is not None else None
            ),
            "properties": {
                key: value
                for key, value in row.items()
                if key != "geometry"
            },
        }

        if geometry is None or geometry.is_empty:
            feature["measurement"] = None

        elif geometry.geom_type in ("Polygon", "MultiPolygon"):
            area = float(area_geometry.area)

            feature["area_m2"] = (
                area if math.isfinite(area) else None
            )

        elif geometry.geom_type in ("LineString", "MultiLineString"):
            length = float(
                abs(geod.geometry_length(geographic_geometry))
            )

            feature["length_m"] = (
                length if math.isfinite(length) else None
            )

        else:
            # Points and unsupported geometries require no measurement
            feature["measurement"] = None

        # Convert NumPy scalar values and non-finite floats for JSON
        for key, value in feature["properties"].items():
            if hasattr(value, "item"):
                value = value.item()

            if isinstance(value, float) and not math.isfinite(value):
                value = None

            feature["properties"][key] = value

        measurements.append(feature)

    return {
        "feature_count": len(gdf),
        "crs": str(gdf.crs),
        "measurement_crs": {
            "area": "EPSG:6933",
            "length": "WGS84 geodesic",
        },
        "features": measurements,
    }
