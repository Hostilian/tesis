"""Three observed Sentinel-2 dates on ONE shared valid-pixel grid.

Fixes an actual interpretation gap in the 2024→2025 and 2025→2026
pairwise studies: different clear masks are NOT interchangeable.
No private company input, synthetic fallback or event labels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from pipeline.observed_change import THRESHOLD_NDVI_DROP
from pipeline.planetary_observation import _boa_offset_dn, read_planetary_sample
from pipeline.real_observation import _ensure_private_path, validate_request
from pipeline.src.preprocessing import GeospatialPreprocessor


def analyze_three(samples: list[dict], metadata: list[dict], bbox: list[float]) -> dict:
    if len(samples) != 3 or len(metadata) != 3:
        raise ValueError("Exactly three independently observed scenes are required")
    if len(bbox) != 4 or not all(np.isfinite(bbox)):
        raise ValueError("Invalid geographic bbox")
    west, south, east, north = bbox
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("Invalid bbox bounds")
    required = ("scene_id", "acquired", "collection", "grid_shape", "bounding_box",
                "pixel_grid_crs", "s2_processing_baseline", "boa_add_offset_dn")
    for m in metadata:
        if any(k not in m or m[k] is None for k in required):
            raise ValueError("Missing required source provenance")
        if m["collection"] != "sentinel-2-l2a" or m["pixel_grid_crs"] != "EPSG:4326":
            raise ValueError("Incompatible collection or coordinate reference")
        if m["bounding_box"] != bbox:
            raise ValueError("Input extent differs; independent gridding forbidden")
        if _boa_offset_dn(m["s2_processing_baseline"]) != m["boa_add_offset_dn"]:
            raise ValueError("Invalid radiometric offset provenance")
    if len({m["scene_id"] for m in metadata}) != 3:
        raise ValueError("Repeated source scene")
    dates = [datetime.fromisoformat(m["acquired"].replace("Z", "+00:00")) for m in metadata]
    if not (dates[0] < dates[1] < dates[2]):
        raise ValueError("Scenes must be chronological")

    preprocessor = GeospatialPreprocessor()
    cubes = [preprocessor.process_raw_bands(s)["ndvi"] for s in samples]
    shape = cubes[0].shape
    if len(shape) != 2 or min(shape) == 0 or any(c.shape != shape for c in cubes):
        raise ValueError("Invalid common two-dimensional grid")
    if any(m["grid_shape"] != list(shape) for m in metadata):
        raise ValueError("Grid shape does not match source metadata")
    # Each finite sample must be present at all THREE dates for both deltas.
    common = np.logical_and.reduce([np.isfinite(c) for c in cubes])
    n = int(common.sum())
    if n < 20:
        raise ValueError("Insufficient three-way clear-pixel intersection")
    a, b, c = (cube[common] for cube in cubes)
    first_delta = b - a
    second_delta = c - b
    total_delta = c - a
    def describe(values):
        return {
            "median_ndvi_delta": float(np.median(values)),
            "q10_ndvi_delta": float(np.quantile(values, .10)),
            "q90_ndvi_delta": float(np.quantile(values, .90)),
            "heuristic_drop_pixels": int(np.sum(values <= THRESHOLD_NDVI_DROP)),
        }
    # All three NDVI arrays in the original fixed pixel order; a derived-array
    # digest only, not the checksum of ESA's original signed COG assets.
    digest = hashlib.sha256(b"".join(
        np.ascontiguousarray(array, dtype="<f8").tobytes() for array in cubes
    )).hexdigest()
    return {
        "schema": "sbei.common_mask_ndvi.v1",
        "verification_status": "observed_pixels_unvalidated_three_scene",
        "synthetic_data": False,
        "source_provider": "Microsoft Planetary Computer / ESA Sentinel-2",
        "collection": "sentinel-2-l2a",
        "scenes": [m["scene_id"] for m in metadata],
        "acquisition_times": [m["acquired"] for m in metadata],
        "s2_processing_baselines": [m["s2_processing_baseline"] for m in metadata],
        "boa_add_offset_dn": [m["boa_add_offset_dn"] for m in metadata],
        "bounding_box": bbox,
        "spatial_reference": "EPSG:4326",
        "grid_shape": list(shape),
        "total_grid_pixels": int(cubes[0].size),
        "per_scene_valid_pixels": [int(np.isfinite(cube).sum()) for cube in cubes],
        "common_valid_pixels": n,
        "common_valid_fraction": float(n / cubes[0].size),
        "valid_mask_policy": "same three-way finite NDVI pixel intersection for ALL comparisons",
        "comparison_2024_2025": describe(first_delta),
        "comparison_2025_2026": describe(second_delta),
        "comparison_2024_2026": describe(total_delta),
        "first_scene_common_mask_median_ndvi": float(np.median(a)),
        "middle_scene_common_mask_median_ndvi": float(np.median(b)),
        "last_scene_common_mask_median_ndvi": float(np.median(c)),
        "derived_arrays_sha256": digest,
        "threshold_ndvi_delta": THRESHOLD_NDVI_DROP,
        "independent_ground_truth": "not_available",
        "model_performance": "not_evaluated",
        "uncertainty_status": "radiometry cross-sensor/baseline and residual cloud errors unquantified",
        "limitations": [
            "Three temporally separated scenes do not prove a resource event, trend or causality.",
            "The shared pixel mask prevents denominator drift, not environmental confounding.",
            "Sentinel-2B and Sentinel-2C plus processing-baseline changes need calibration QA.",
            "There are no event labels or empirical anomaly-model performance measures.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bbox", nargs=4, type=float, required=True)
    for label in ("first", "middle", "last"):
        parser.add_argument(f"--{label}-start", required=True)
        parser.add_argument(f"--{label}-end", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("research_private/observations/three_scene"))
    args = parser.parse_args()
    samples, metas = [], []
    for label in ("first", "middle", "last"):
        start, end = getattr(args, f"{label}_start"), getattr(args, f"{label}_end")
        validate_request(args.bbox, start, end)
        bands, meta = read_planetary_sample(args.bbox, start, end)
        samples.append(bands)
        metas.append(meta)
    result = analyze_three(samples, metas, args.bbox)
    out = _ensure_private_path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = out / f"three_scene_common_mask_{stamp}.json"
    if filename.exists():
        raise FileExistsError("Refusing to overwrite research evidence")
    result["processed_utc"] = datetime.now(timezone.utc).isoformat()
    filename.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"PRIVATE shared-mask result: {filename}")
    print(f"Common valid pixels: {result['common_valid_pixels']} / {result['total_grid_pixels']}")
    print(f"Median 2024->2025: {result['comparison_2024_2025']['median_ndvi_delta']:.6f}")
    print(f"Median 2025->2026: {result['comparison_2025_2026']['median_ndvi_delta']:.6f}")
    print("Scientific event interpretation: UNVALIDATED")


if __name__ == "__main__":
    main()
