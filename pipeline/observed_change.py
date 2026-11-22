"""Exploratory TWO-SCENE NDVI change from authentic Sentinel-2 COG pixels.

The existing Planetary Computer reader supplies both scenes. This module adds
only a transparent change baseline and standards-based GeoJSON aggregation.
No fabricated data, inferred resource event, classification score or live feed.

Usage:
 python -m pipeline.observed_change --bbox -68.25 -23.48 -68.238 -23.468 \
   --before-start 2024-10-01 --before-end 2024-10-15 \
   --after-start 2025-10-01 --after-end 2025-10-15
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from pipeline.planetary_observation import _boa_offset_dn, read_planetary_sample
from pipeline.real_observation import _ensure_private_path, validate_request
from pipeline.src.preprocessing import GeospatialPreprocessor

THRESHOLD_NDVI_DROP = -0.15  # fixed exploratory heuristic, NOT a trained model
BLOCK_PIXELS = 8


def analyze_pair(
    before: dict[str, np.ndarray],
    after: dict[str, np.ndarray],
    before_meta: dict[str, Any],
    after_meta: dict[str, Any],
    bbox: list[float],
    threshold: float = THRESHOLD_NDVI_DROP,
) -> dict[str, Any]:
    """Return GeoJSON grid summaries without claiming validated anomalies."""
    if not np.isfinite(threshold) or not -1.0 < threshold < 0:
        raise ValueError("threshold must be a finite negative NDVI difference")
    if not all(np.isfinite(bbox)) or len(bbox) != 4:
        raise ValueError("bbox must contain four finite coordinates")
    west, south, east, north = bbox
    if west >= east or south >= north:
        raise ValueError("invalid geographic extent")
    required_meta = ("scene_id", "acquired", "collection", "pixel_grid_crs", "grid_shape", "s2_processing_baseline")
    for label, meta in (("before", before_meta), ("after", after_meta)):
        if any(not meta.get(k) for k in required_meta):
            raise ValueError(f"{label} scene lineage is incomplete")
        if meta.get("boa_add_offset_dn") != _boa_offset_dn(meta["s2_processing_baseline"]):
            raise ValueError(f"{label} radiometric correction metadata missing")
        if meta["collection"] != "sentinel-2-l2a" or meta["pixel_grid_crs"] != "EPSG:4326":
            raise ValueError("different source collection or grid CRS")
        if meta.get("bounding_box") != bbox:
            raise ValueError("source grid extent does not match requested bbox")
    if before_meta["scene_id"] == after_meta["scene_id"]:
        raise ValueError("change requires two distinct observations")
    first_time = datetime.fromisoformat(before_meta["acquired"].replace("Z", "+00:00"))
    second_time = datetime.fromisoformat(after_meta["acquired"].replace("Z", "+00:00"))
    if not first_time < second_time:
        raise ValueError("observations must be in chronological order")

    prep = GeospatialPreprocessor()
    pre = prep.process_raw_bands(before)["ndvi"]
    post = prep.process_raw_bands(after)["ndvi"]
    if pre.shape != post.shape or pre.ndim != 2 or pre.size == 0:
        raise ValueError("observations must have identical non-empty 2D grids")
    if before_meta["grid_shape"] != list(pre.shape) or after_meta["grid_shape"] != list(pre.shape):
        raise ValueError("source metadata does not match raster shapes")
    valid = np.isfinite(pre) & np.isfinite(post)
    n_overlap = int(valid.sum())
    if n_overlap < 20:
        raise ValueError("insufficient overlapping clear pixels")
    delta = np.where(valid, post - pre, np.nan)
    flags = valid & (delta <= threshold)

    nrows, ncols = delta.shape
    features: list[dict[str, Any]] = []
    for row in range(0, nrows, BLOCK_PIXELS):
        for col in range(0, ncols, BLOCK_PIXELS):
            sub_valid = valid[row : row + BLOCK_PIXELS, col : col + BLOCK_PIXELS]
            count = int(sub_valid.sum())
            if count == 0:
                continue
            sub_delta = delta[row : row + BLOCK_PIXELS, col : col + BLOCK_PIXELS]
            sub_flags = flags[row : row + BLOCK_PIXELS, col : col + BLOCK_PIXELS]
            left = west + (east - west) * col / ncols
            right = west + (east - west) * min(col + BLOCK_PIXELS, ncols) / ncols
            top = north - (north - south) * row / nrows
            bottom = north - (north - south) * min(row + BLOCK_PIXELS, nrows) / nrows
            features.append({
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [[
                    [left, bottom], [right, bottom], [right, top],
                    [left, top], [left, bottom],
                ]]},
                "properties": {
                    "valid_overlap_pixels": count,
                    "median_ndvi_delta": round(float(np.nanmedian(sub_delta)), 5),
                    "heuristic_drop_pixels": int(sub_flags.sum()),
                    "drop_fraction": round(float(sub_flags.sum()) / count, 5),
                    "verification_status": "unverified_interpretation",
                },
            })

    # Array digest: identifies aligned derived input arrays, not original COGs.
    arrays_digest = hashlib.sha256(
        np.ascontiguousarray(pre, dtype="<f8").tobytes()
        + np.ascontiguousarray(post, dtype="<f8").tobytes()
    ).hexdigest()
    return {
        "type": "FeatureCollection",
        "schema": "sbei.observed_ndvi_change.v1",
        "verification_status": "observed_pixels_unvalidated_change",
        "synthetic_data": False,
        "source_provider": "Microsoft Planetary Computer / ESA Sentinel-2",
        "collection": "sentinel-2-l2a",
        "scenes": [before_meta["scene_id"], after_meta["scene_id"]],
        "acquisition_times": [before_meta["acquired"], after_meta["acquired"]],
        "s2_processing_baselines": [before_meta["s2_processing_baseline"], after_meta["s2_processing_baseline"]],
        "boa_add_offset_dn": [before_meta["boa_add_offset_dn"], after_meta["boa_add_offset_dn"]],
        "quality_mask": "Sentinel-2 SCL excluded 0,1,3,8,9,10,11",
        "spatial_reference": "EPSG:4326",
        "bounding_box": bbox,
        "derived_arrays_sha256": arrays_digest,
        "processing_version": "ndvi-change-baseline-v1",
        "analysis_method": "NDVI(after)-NDVI(before); fixed decline threshold, aggregated 8x8 pixels",
        "threshold_ndvi_delta": threshold,
        "overlap_valid_pixels": n_overlap,
        "total_grid_pixels": int(pre.size),
        "flagged_pixel_count": int(flags.sum()),
        "median_ndvi_delta": float(np.nanmedian(delta)),
        "independent_ground_truth": "not_available",
        "model_performance": "not_evaluated",
        "limitations": [
            "Two scenes do not establish a temporal trend, causal event or resource extraction.",
            "A fixed NDVI threshold is an illustrative heuristic, not a validated detector.",
            "Seasonality, atmospheric conditions, terrain and residual cloud contamination may explain change.",
            "Geographic preview grid resampling is not a field-accurate measurement.",
            "Input checksum covers DERIVED arrays, not original ESA COG archive.",
        ],
        "features": features,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bbox", nargs=4, type=float, required=True)
    for label in ("before", "after"):
        parser.add_argument(f"--{label}-start", required=True)
        parser.add_argument(f"--{label}-end", required=True)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("research_private/observations")
    )
    args = parser.parse_args()
    bbox = args.bbox
    validate_request(bbox, args.before_start, args.before_end)
    validate_request(bbox, args.after_start, args.after_end)
    before, bmeta = read_planetary_sample(bbox, args.before_start, args.before_end)
    after, ameta = read_planetary_sample(bbox, args.after_start, args.after_end)
    result = analyze_pair(before, after, bmeta, ameta, bbox)
    output = _ensure_private_path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = output / f"observed_ndvi_change_{stamp}.geojson"
    if target.exists():
        raise FileExistsError("refusing to overwrite scientific artifact")
    result["processed_utc"] = datetime.now(timezone.utc).isoformat()
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PRIVATE exploratory two-scene NDVI change: {target}")
    print(f"Valid overlapping pixels: {result['overlap_valid_pixels']}")
    print("No ground-truth anomaly detection or validation is claimed.")


if __name__ == "__main__":
    main()
