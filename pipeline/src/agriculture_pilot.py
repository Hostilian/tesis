"""Offline, geometry-safe agricultural observation pilot; no private farm data.

Provides a validated WGS84 polygon, an HTTP request *description* for the
Copernicus STAC catalogue, and a simple robust NDVI baseline. No implicit I/O.
"""
from __future__ import annotations

from datetime import date
from math import isfinite
from statistics import median
from typing import Any

CDSE_STAC_URL = "https://stac.opensearch.dataspace.copernicus.eu/v1/search"


def validate_study_area(feature: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        raise ValueError("Require a GeoJSON Feature")
    geometry = feature.get("geometry") or {}
    if geometry.get("type") != "Polygon":
        raise ValueError("Pilot supports only Polygon geometries")
    if feature.get("crs") or geometry.get("crs"):
        raise ValueError("GeoJSON must be RFC7946 WGS84 lon/lat, not a local CRS")
    rings = geometry.get("coordinates")
    if not isinstance(rings, list) or not rings:
        raise ValueError("Polygon coordinates missing")
    for ring in rings:
        if not isinstance(ring, list) or len(ring) < 4 or ring[0] != ring[-1]:
            raise ValueError("Polygon ring must have at least four positions and close")
        for position in ring:
            if not isinstance(position, list) or len(position) < 2:
                raise ValueError("Invalid point")
            lon, lat = position[:2]
            if not all(isinstance(v, (int, float)) and isfinite(v) for v in (lon, lat)):
                raise ValueError("Non-numeric or non-finite coordinates")
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                raise ValueError("Coordinates must be WGS84 lon/lat")
        if len(set(tuple(x[:2]) for x in ring)) < 3:
            raise ValueError("Degenerate polygon")
    return geometry


def stac_search_request(feature: dict[str, Any], start: str, end: str, limit: int = 20) -> dict[str, Any]:
    geom = validate_study_area(feature)
    try:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
    except ValueError as exc:
        raise ValueError("Use ISO calendar dates YYYY-MM-DD") from exc
    if first > last:
        raise ValueError("Start date must not exceed end date")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be from 1 to 100")
    return {
        "url": CDSE_STAC_URL, "method": "POST",
        "json": {"collections": ["sentinel-2-l2a"], "intersects": geom,
                 "datetime": f"{start}T00:00:00Z/{end}T23:59:59Z", "limit": limit},
        "network_performed": False,
    }


def ndvi(nir: float, red: float) -> float | None:
    if not all(isfinite(float(v)) and float(v) >= 0 for v in (nir, red)):
        raise ValueError("Reflectances must be finite and nonnegative")
    denom = nir + red
    return (nir - red) / denom if denom else None


def robust_deviation(value: float, historical: list[float]) -> dict[str, float | None]:
    """MAD-based baseline, not disease, stress or yield classification."""
    if len(historical) < 5 or not all(isfinite(x) for x in [value, *historical]):
        raise ValueError("Require five or more finite comparable observations")
    center = median(historical)
    mad = median([abs(x - center) for x in historical])
    return {"median": center, "mad": mad,
            "robust_z": (0.67448975 * (value - center) / mad) if mad > 0 else None}
