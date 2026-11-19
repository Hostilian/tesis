"""Public or explicitly authorised agriculture study-area exploration.

This module has a strict metadata/discovery boundary. STAC search results do
not prove raster access, physical anomalies, or independently validated events.
The default demonstration performs no network requests or company-data access.
"""

from __future__ import annotations

from datetime import date
from math import isfinite
from statistics import median
from typing import Any

import requests

CDSE_STAC_SEARCH_URL = "https://stac.opensearch.dataspace.copernicus.eu/v1/search"


class StudyAreaError(ValueError):
    """An input polygon is not a valid public/authorised WGS84 study area."""


def validate_study_area(feature: dict[str, Any]) -> dict[str, Any]:
    """Require a closed, finite, non-degenerate WGS84 GeoJSON polygon."""
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        raise StudyAreaError("Require a GeoJSON Feature")
    geometry = feature.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") != "Polygon":
        raise StudyAreaError("Only GeoJSON Polygon geometry is supported")
    if feature.get("crs") is not None or geometry.get("crs") is not None:
        raise StudyAreaError("GeoJSON must be WGS84 lon/lat (RFC 7946)")

    rings = geometry.get("coordinates")
    if not isinstance(rings, list) or not rings:
        raise StudyAreaError("Polygon rings are missing")

    for ring in rings:
        if not isinstance(ring, list) or len(ring) < 4:
            raise StudyAreaError("Polygon rings require at least four positions")
        if ring[0] != ring[-1]:
            raise StudyAreaError("Polygon ring must be closed")
        coordinates: set[tuple[float, float]] = set()
        for position in ring:
            if not isinstance(position, (list, tuple)) or len(position) < 2:
                raise StudyAreaError("Invalid coordinate")
            lon, lat = position[:2]
            if any(type(v) not in (float, int) for v in (lon, lat)):
                raise StudyAreaError("Coordinates must be numeric, not boolean")
            if not all(isfinite(v) for v in (lon, lat)):
                raise StudyAreaError("Coordinates must be finite")
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                raise StudyAreaError("Coordinates must be WGS84 lon/lat")
            coordinates.add((float(lon), float(lat)))
        if len(coordinates) < 3:
            raise StudyAreaError("Degenerate polygon")
    return geometry


def stac_search_request(
    feature: dict[str, Any], start: str, end: str, limit: int = 20
) -> dict[str, Any]:
    """Describe a CDSE search; never send farm geometry as a side effect."""
    geometry = validate_study_area(feature)
    try:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
    except ValueError as exc:
        raise ValueError("Dates must use YYYY-MM-DD") from exc
    if first > last:
        raise ValueError("Start date must not exceed end date")
    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100")
    return {
        "url": CDSE_STAC_SEARCH_URL,
        "method": "POST",
        "json": {
            "collections": ["sentinel-2-l2a"],
            "intersects": geometry,
            "datetime": f"{start}T00:00:00Z/{end}T23:59:59Z",
            "limit": limit,
        },
        "network_performed": False,
    }


def execute_stac_discovery(
    request_description: dict[str, Any],
    *,
    approved_public_geometry: bool = False,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """Query metadata only after the caller explicitly approves disclosure.

    Preserve product ID, timestamp and cloud metadata, but never return item
    geometry or a signed asset URL. Fail closed on all catalogue errors.
    """
    if not approved_public_geometry:
        raise PermissionError(
            "Do not send study polygons to external APIs without permission"
        )
    if request_description.get("url") != CDSE_STAC_SEARCH_URL:
        raise ValueError("Unrecognised catalogue endpoint")
    if request_description.get("method") != "POST":
        raise ValueError("Expected STAC POST search")
    payload = request_description.get("json")
    if not isinstance(payload, dict):
        raise ValueError("Missing STAC search request body")

    client = session or requests.Session()
    response = client.post(CDSE_STAC_SEARCH_URL, json=payload, timeout=30)
    response.raise_for_status()
    document = response.json()
    if not isinstance(document, dict) or not isinstance(
        document.get("features"), list
    ):
        raise ValueError("STAC response is not a FeatureCollection")

    summaries = []
    for item in document["features"]:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("STAC item is missing its product identifier")
        properties = item.get("properties", {})
        if not isinstance(properties, dict):
            raise ValueError("STAC item properties are malformed")
        summaries.append(
            {
                "product_id": item["id"],
                "collection": item.get("collection"),
                "acquired_at": properties.get("datetime"),
                "cloud_cover_pct": properties.get("eo:cloud_cover"),
                "asset_keys": sorted(
                    list(item.get("assets", {}).keys())
                    if isinstance(item.get("assets", {}), dict)
                    else []
                ),
                "evidence_state": "catalogue_metadata_only",
                "pixel_assets_read": False,
                "ground_truth_validated": False,
            }
        )
    return summaries


def ndvi(nir: float, red: float) -> float | None:
    """NDVI from calibrated comparable reflectance values, or None if zero."""
    if not all(isfinite(float(v)) and v >= 0 for v in (nir, red)):
        raise ValueError("Reflectance must be finite and nonnegative")
    denom = nir + red
    return (nir - red) / denom if denom else None


def ndmi(nir: float, swir1: float) -> float | None:
    """Canopy moisture index; not interchangeable with green/NIR NDWI."""
    return ndvi(nir, swir1)


def robust_deviation(value: float, historical: list[float]) -> dict[str, float | None]:
    """MAD-based season-matched baseline, not crop stress diagnosis."""
    if len(historical) < 5 or not all(isfinite(v) for v in [value, *historical]):
        raise ValueError("Five or more finite comparable observations required")
    center = median(historical)
    mad = median(abs(v - center) for v in historical)
    return {
        "median": center,
        "mad": mad,
        "robust_z": 0.67448975 * (value - center) / mad if mad > 0 else None,
    }
