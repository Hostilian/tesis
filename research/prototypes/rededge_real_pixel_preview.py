"""Read real public Sentinel-2 red-edge COG assets; calculate spectral indices.

Reproducible *technical* feasibility only. No lab labels, no chlorophyll or
nitrogen estimates, and no privately supplied farm geometry. Uses the same
open STAC/Planetary Computer/rasterio building blocks as planetary_observation.
Run from repository root with dependencies in pipeline/requirements.txt:

    python -m research.prototypes.rededge_real_pixel_preview

Writes a metadata/summary JSON to stdout; does NOT publish pixel arrays.
The default public scene is a generic Alentejo raster window, not a farm asset.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np
import pystac
import rasterio
import requests
from planetary_computer import sign_inplace
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.vrt import WarpedVRT

from pipeline.planetary_observation import PUBLIC_STAC_URL, RASTER_GRID_PIXELS

# The publicly inspectable demonstration scene is fixed intentionally.
PUBLIC_SCENE = "S2B_MSIL2A_20250627T112119_R037_T29SNC_20250627T133415"
PUBLIC_BBOX = (-8.01, 38.59, -8.00, 38.60)
BANDS = ("B04", "B05", "B06", "B07", "B08", "B8A", "SCL")
REFLECTANCE = BANDS[:-1]
EXCLUDED_SCL = (0, 1, 3, 8, 9, 10, 11)


def observe_public_rededge() -> dict[str, Any]:
    """Return only observable optical-index metadata; fail closed on missing data."""
    item_url = f"{PUBLIC_STAC_URL}/collections/sentinel-2-l2a/items/{PUBLIC_SCENE}"
    response = requests.get(item_url, timeout=30)
    response.raise_for_status()
    scene = pystac.Item.from_dict(response.json())
    if scene.id != PUBLIC_SCENE or any(key not in scene.assets for key in BANDS):
        raise ValueError("Unexpected scene or missing real raster assets")
    sign_inplace(scene)

    values: dict[str, np.ndarray] = {}
    n = RASTER_GRID_PIXELS
    for key in BANDS:
        sampling = Resampling.nearest if key == "SCL" else Resampling.bilinear
        with rasterio.open(scene.assets[key].href) as dataset:
            with WarpedVRT(
                dataset,
                crs="EPSG:4326",
                transform=from_bounds(*PUBLIC_BBOX, n, n),
                width=n,
                height=n,
                resampling=sampling,
            ) as aligned:
                values[key] = aligned.read(1, masked=True).astype("float64").filled(np.nan)

    usable = np.isfinite(values["SCL"]) & ~np.isin(values["SCL"], EXCLUDED_SCL)
    for band in REFLECTANCE:
        arr = values[band]
        usable &= np.isfinite(arr) & (arr > 0) & (arr < 65535)
    refl = {key: values[key] / 10000.0 for key in REFLECTANCE}

    with np.errstate(divide="ignore", invalid="ignore"):
        # Both B8A and B05 have 20 m native support; no false 10 m precision.
        ndre = (refl["B8A"] - refl["B05"]) / (refl["B8A"] + refl["B05"])
        ndvi = (refl["B08"] - refl["B04"]) / (refl["B08"] + refl["B04"])
    usable &= np.isfinite(ndre) & np.isfinite(ndvi)
    count = int(np.count_nonzero(usable))
    if count < 20:
        raise ValueError("Too few quality-masked observed pixels")

    checksum = hashlib.sha256(
        np.stack([refl[band][usable] for band in REFLECTANCE])
        .astype("<f4")
        .tobytes()
    ).hexdigest()

    def summary(array: np.ndarray) -> dict[str, float]:
        selected = array[usable]
        return {
            "min": float(np.min(selected)),
            "median": float(np.median(selected)),
            "max": float(np.max(selected)),
        }

    return {
        "schema": "sbei.rededge_public_preview.v1",
        "status": "real_optical_pixels_unvalidated",
        "scene_id": scene.id,
        "acquired_utc": scene.properties.get("datetime"),
        "stac_url": PUBLIC_STAC_URL,
        "bbox": list(PUBLIC_BBOX),
        "bands": list(BANDS),
        "grid_shape": [n, n],
        "valid_grid_pixels": count,
        "ndre": summary(ndre),
        "ndvi": summary(ndvi),
        "array_sha256": checksum,
        "native_red_edge_resolution_m": 20,
        "grid_resampling_not_native_resolution": True,
        "biochemistry_reference_samples": 0,
        "measured_chlorophyll_or_nitrogen": False,
        "scientific_accuracy_validation": "not_performed",
        "disclaimer": "Observed real reflectance; no biochemical model or farm conclusion.",
    }


if __name__ == "__main__":
    print(json.dumps(observe_public_rededge(), indent=2))
