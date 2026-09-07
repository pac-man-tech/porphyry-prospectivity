"""Spatial utilities: reprojection, spatial CV helpers, and geometry IO."""
from typing import Any
import geopandas as gpd


def read_vector(path: str) -> gpd.GeoDataFrame:
    return gpd.read_file(path)


def reproject_gdf(gdf: gpd.GeoDataFrame, crs: Any) -> gpd.GeoDataFrame:
    return gdf.to_crs(crs)
