"""Public Sentinel-2 pair, quality-masked optical difference preview (SOIL-5).

Reuse PySTAC, Planetary Computer and rasterio. This is not a model detecting
erosion, sealing, or chemistry. It does not use private farms or synthetic inputs.

  python research/prototypes/soil_surface_pair_public_preview.py --out research_private/soil5_public_pair.json

Data result carries scene IDs, dates and optical variability, and remains local
unless separately reviewed and published as an explicit no-ground-truth proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from planetary_computer import sign_inplace
from pystac_client import Client
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.vrt import WarpedVRT

BBOX = (-8.01, 38.59, -8.00, 38.60)
GRID = 96
BANDS = ("B02", "B04", "B08", "B11", "SCL")
COLLECTION = "sentinel-2-l2a"
PUBLIC_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
DATERANGES = ("2024-06-15/2024-07-15", "2025-06-15/2025-07-15")
UNSAFE_SCL = (0, 1, 3, 8, 9, 10, 11)


def best_public_scene(catalog: Client, period: str) -> Any:
    scenes = list(catalog.search(
        collections=[COLLECTION],
        bbox=BBOX,
        datetime=period,
        query={"eo:cloud_cover": {"lt": 30}},
        max_items=35,
    ).items())
    choices = [s for s in scenes if all(band in s.assets for band in BANDS)]
    if not choices:
        raise ValueError("No complete real Sentinel-2 data for " + period)
    # Stable choice; never synthesize a missing scene.
    return min(choices, key=lambda s: (
        float(s.properties.get("eo:cloud_cover", 100)),
        str(s.id),
    ))


def read_real_bands(scene: Any) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {}
    for band in BANDS:
        with rasterio.open(scene.assets[band].href) as ds:
            with WarpedVRT(
                ds, crs="EPSG:4326",
                transform=from_bounds(*BBOX, GRID, GRID),
                width=GRID, height=GRID,
                resampling=(Resampling.nearest if band == "SCL" else Resampling.bilinear),
            ) as sample:
                arrays[band] = sample.read(1, masked=True).astype("float64").filled(np.nan)
    return arrays


def indices(bands: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    qa = np.isfinite(bands["SCL"]) & ~np.isin(bands["SCL"], UNSAFE_SCL)
    r = {}
    for band in BANDS[:-1]:
        raw = bands[band]
        qa &= np.isfinite(raw) & (raw > 0) & (raw < 65535)
        r[band] = raw / 10000
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = (r["B08"] - r["B04"]) / (r["B08"] + r["B04"])
        # Bare Soil Index is a spectral feature, not proof of actual exposed soil.
        bsi = ((r["B11"] + r["B04"]) - (r["B08"] + r["B02"])) / (
            (r["B11"] + r["B04"]) + (r["B08"] + r["B02"])
        )
    qa &= np.isfinite(ndvi) & np.isfinite(bsi)
    return qa, ndvi, bsi


def run() -> dict[str, Any]:
    catalog = Client.open(PUBLIC_STAC_URL, modifier=sign_inplace)
    items = [best_public_scene(catalog, p) for p in DATERANGES]
    data = [read_real_bands(x) for x in items]
    before, ndvi0, bsi0 = indices(data[0])
    after, ndvi1, bsi1 = indices(data[1])
    valid = before & after
    n = int(np.count_nonzero(valid))
    if n < 20:
        raise ValueError("Insufficient independent-date overlapping QA-masked optical pixels")
    delta_ndvi = ndvi1[valid] - ndvi0[valid]
    delta_bsi = bsi1[valid] - bsi0[valid]
    samplebytes = np.stack([
        ndvi0[valid], ndvi1[valid], bsi0[valid], bsi1[valid]
    ]).astype("<f4").tobytes()

    def summary(arr: np.ndarray) -> dict[str, float]:
        return {"min": float(np.min(arr)), "median": float(np.median(arr)),
                "max": float(np.max(arr))}

    return {
        "schema": "sbei.soil5.surface_pair_public_preview.v1",
        "status": "observed_optical_change_candidate_only",
        "source": PUBLIC_STAC_URL,
        "collection": COLLECTION,
        "bbox": list(BBOX),
        "requested_date_ranges": list(DATERANGES),
        "scenes": [
            {"scene_id": i.id, "acquired_utc": i.properties.get("datetime"),
             "catalog_cloud_pct": i.properties.get("eo:cloud_cover")}
            for i in items
        ],
        "band_assets": list(BANDS),
        "grid_shape": [GRID, GRID],
        "qa_valid_overlap_grid_pixels": n,
        "ndvi_before": summary(ndvi0[valid]),
        "ndvi_after": summary(ndvi1[valid]),
        "ndvi_change": summary(delta_ndvi),
        "bsi_before": summary(bsi0[valid]),
        "bsi_after": summary(bsi1[valid]),
        "bsi_change": summary(delta_bsi),
        "abs_ndvi_delta_over_0_15_grid_count": int(np.count_nonzero(
            np.abs(delta_ndvi) > 0.15
        )),
        "analytical_array_sha256": hashlib.sha256(samplebytes).hexdigest(),
        "native_resolution_note": "Aligned interpolation, not independent site labels; B11 originally 20 m",
        "independent_reference_samples": 0,
        "verified_soil_sealing_cases": 0,
        "verified_erosion_cases": 0,
        "chemical_laboratory_equivalence": False,
        "scientific_validation": "not_performed",
        "note": "Two real optical source scenes. Change threshold is arbitrary exploration and NOT soil sealing, soil removal, erosion or measured chemistry.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("research_private/soil5_public_pair.json"))
    args = parser.parse_args()
    record = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        raise FileExistsError("Would overwrite prior receipt")
    args.out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("WROTE_PUBLIC_SOURCE_EVIDENCE", args.out)
