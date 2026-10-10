
import math
import os
import zipfile
import tempfile

import geopandas as gpd


def process_file(file_path: str, filename: str):
    filename = filename.lower()

    if filename.endswith(".kml"):
        gdf = gpd.read_file(file_path, driver="KML")

    elif filename.endswith(".zip"):
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                # Prevent ZIP path traversal
                for member in zip_ref.infolist():
                    target = os.path.realpath(
                        os.path.join(temp_dir, member.filename)
                    )
                    if not target.startswith(
                        os.path.realpath(temp_dir) + os.sep
                    ):
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

            gdf = gpd.read_file(shp_files[0])

            # Process before the temporary directory is deleted
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

    # Reproject coordinates before calculating area or length
    projected_crs = gdf.estimate_utm_crs()

    if projected_crs is None:
        raise ValueError("Could not determine a suitable projected CRS")

    projected_gdf = gdf.to_crs(projected_crs)

    for index, row in gdf.iterrows():
        geometry = row.geometry
        measurement_geometry = projected_gdf.geometry.loc[index]

        feature = {
            "feature_id": int(index) if isinstance(index, int) else str(index),
            "geometry_type": (
                geometry.geom_type if geometry is not None else None
            ),
            "properties": {
                key: value
                for key, value in row.items()
                if key != "geometry"
            },
        }

        # Handle missing or empty geometries
        if geometry is None or geometry.is_empty:
            feature["measurement"] = None

        elif geometry.geom_type in ("Polygon", "MultiPolygon"):
            area = float(measurement_geometry.area)
            feature["area_m2"] = (
                area if math.isfinite(area) else None
            )

        elif geometry.geom_type in ("LineString", "MultiLineString"):
            length = float(measurement_geometry.length)
            feature["length_m"] = (
                length if math.isfinite(length) else None
            )

        else:
            # Points and unsupported geometry types need no measurement
            feature["measurement"] = None

        # Ensure property values can be returned as valid JSON
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
        "measurement_crs": str(projected_gdf.crs),
        "features": measurements,
    }
