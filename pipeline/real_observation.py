"""Fail-closed experimental real Sentinel-2 pixel acquisition.

This is *not* the demo pipeline, nor a ground-truth validation workflow.
It never falls back to synthetic pixels or publishes to GitHub Pages.

Usage:
    python -m pipeline.real_observation \\
      --bbox -68.250 -23.480 -68.238 -23.468 \\
      --start 2024-10-01 --end 2024-10-15 \\
      --output-dir research_private/observations

Requires a working Google Earth Engine account and GCP_PROJECT. It requests
a small area only, to keep sampling finite and affordable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from datetime import date, datetime, timezone
from typing import Any

import numpy as np

from pipeline.src.preprocessing import GeospatialPreprocessor

BAND_NAMES = ("B2", "B3", "B4", "B8", "B11")
MAX_SIDE_METRES = 2000.0
MAX_INPUT_SCENES = 60
MAX_SAMPLED_PIXELS = 25000


def validate_request(
    bbox: list[float], start: str, end: str
) -> tuple[date, date]:
    """Bound the footprint so a research preview cannot query a whole farm."""
    if len(bbox) != 4 or not all(np.isfinite(value) for value in bbox):
        raise ValueError("bbox must contain four finite lon/lat coordinates")
    min_lon, min_lat, max_lon, max_lat = bbox
    if not (-180 <= min_lon < max_lon <= 180):
        raise ValueError("invalid longitude bounds")
    if not (-90 <= min_lat < max_lat <= 90):
        raise ValueError("invalid latitude bounds")
    lat_mid = (min_lat + max_lat) / 2.0
    width = (max_lon - min_lon) * 111320 * abs(np.cos(np.deg2rad(lat_mid)))
    height = (max_lat - min_lat) * 111320
    if width > MAX_SIDE_METRES or height > MAX_SIDE_METRES:
        raise ValueError("sample area too large; use a bounded 2-km preview")
    try:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
    except ValueError as exc:
        raise ValueError("dates must use YYYY-MM-DD") from exc
    if first >= last or (last - first).days > 45:
        raise ValueError("date window must be 1 to 45 days")
    return first, last


def decode_sample(properties: dict[str, Any]) -> dict[str, np.ndarray]:
    """Decode actual GEE sampleRectangle pixels; reject absent/masked bands."""
    missing = [band for band in BAND_NAMES if band not in properties]
    if missing:
        raise ValueError(f"missing observed bands: {', '.join(missing)}")
    output: dict[str, np.ndarray] = {}
    common_shape: tuple[int, ...] | None = None
    for band in BAND_NAMES:
        values = np.asarray(properties[band], dtype=np.float64)
        if values.ndim != 2 or values.size == 0:
            raise ValueError(f"invalid or empty {band} pixel array")
        if values.size > MAX_SAMPLED_PIXELS:
            raise ValueError("sample exceeds pixel budget")
        if common_shape is None:
            common_shape = values.shape
        elif values.shape != common_shape:
            raise ValueError("bands are not on the same grid")
        values[values <= -9999] = np.nan
        output[band] = values * 0.0001  # Sentinel-2 L2A reflectance scale
    valid = np.logical_and.reduce(
        [np.isfinite(output[band]) for band in BAND_NAMES]
    )
    if valid.sum() < 20:
        raise ValueError("insufficient valid observed pixels")
    output["QA60"] = np.zeros(common_shape, dtype=np.uint16)
    return output


def _ensure_private_path(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    project = Path(__file__).resolve().parents[1]
    public = (project / "docs").resolve()
    if resolved == public or public in resolved.parents:
        raise ValueError("refusing to write private observations into docs/")
    private = (project / "research_private").resolve()
    if project in resolved.parents and not (
        resolved == private or private in resolved.parents
    ):
        raise ValueError("inside this repository, output must be under research_private/")
    return resolved


def fetch_observed_sample(
    bbox: list[float], start: str, end: str
) -> tuple[dict[str, np.ndarray], list[str]]:
    """Query real harmonized GEE imagery; never return mock samples."""
    validate_request(bbox, start, end)
    if os.environ.get("MOCK_MODE", "").lower() == "true":
        raise RuntimeError("real observation path rejects MOCK_MODE=true")
    try:
        import ee
    except ImportError as exc:
        raise RuntimeError("earthengine-api must be installed") from exc
    project = os.getenv("GCP_PROJECT")
    if not project:
        raise RuntimeError("set GCP_PROJECT and authenticate Earth Engine first")
    # No automatic interactive login or fallback is attempted.
    ee.Initialize(project=project)
    region = ee.Geometry.BBox(*bbox)
    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate(start, end)
        .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", 35))
    )
    count = int(collection.size().getInfo())
    if not 1 <= count <= MAX_INPUT_SCENES:
        raise ValueError("no source scenes or too many scenes; narrow time range")
    ids = collection.aggregate_array("system:index").getInfo()
    if not isinstance(ids, list) or len(ids) != count:
        raise RuntimeError("scene identifiers unavailable; aborting")

    def mask_scene(image: Any) -> Any:
        # Sentinel-2 Scene Classification: mask shadow, clouds and snow/ice.
        scl = image.select("SCL")
        clear = (
            scl.neq(3)
            .And(scl.neq(8))
            .And(scl.neq(9))
            .And(scl.neq(10))
            .And(scl.neq(11))
            .And(scl.neq(0))
            .And(scl.neq(1))
        )
        return image.updateMask(clear).select(list(BAND_NAMES))

    # All bands are resampled onto a single 30-m geodetic preview grid.
    mosaic = collection.map(mask_scene).median()
    aligned = mosaic.reproject(crs="EPSG:4326", scale=30)
    result = aligned.sampleRectangle(region=region, defaultValue=-9999).getInfo()
    if not isinstance(result, dict) or not isinstance(result.get("properties"), dict):
        raise RuntimeError("Earth Engine did not return a valid pixel sample")
    bands = decode_sample(result["properties"])
    return bands, [str(scene_id) for scene_id in ids]


def save_observation(
    bands: dict[str, np.ndarray],
    scene_ids: list[str],
    bbox: list[float],
    start: str,
    end: str,
    directory: Path,
) -> tuple[Path, Path]:
    """Save source pixels and limited manifest outside the public site."""
    validate_request(bbox, start, end)
    if not scene_ids or any(not sid for sid in scene_ids):
        raise ValueError("real product IDs are required")
    prepared = GeospatialPreprocessor().process_raw_bands(bands)
    if not any(np.isfinite(prepared["ndvi"]).flat):
        raise ValueError("no usable observed spectral indices")
    out_dir = _ensure_private_path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = out_dir / f"sentinel2_observed_{stamp}"
    npz_path = base.with_suffix(".npz")
    manifest_path = base.with_suffix(".json")
    if npz_path.exists() or manifest_path.exists():
        raise FileExistsError("refusing to overwrite observation data")
    np.savez_compressed(
        npz_path,
        **{band: bands[band] for band in BAND_NAMES},
        ndvi=prepared["ndvi"],
        ndwi=prepared["ndwi"],
        bsi=prepared["bsi"],
    )
    digest = hashlib.sha256(npz_path.read_bytes()).hexdigest()
    manifest = {
        "status": "real_pixel_inputs_unvalidated",
        "scientific_validation": "not_performed",
        "source": "Google Earth Engine COPERNICUS/S2_SR_HARMONIZED",
        "scene_identifiers": scene_ids,
        "bbox": bbox,
        "start": start,
        "end": end,
        "projection": "EPSG:4326 preview at 30 m",
        "pixel_grid_shape": list(bands["B2"].shape),
        "checksum_sha256": digest,
        "written_utc": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Source pixels have been retrieved, but no independent label "
            "validation, calibration or model evaluation has been conducted."
        ),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return npz_path, manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bbox", type=float, nargs=4, required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("research_private/observations")
    )
    args = parser.parse_args()
    bands, scene_ids = fetch_observed_sample(args.bbox, args.start, args.end)
    npz, manifest = save_observation(
        bands, scene_ids, args.bbox, args.start, args.end, args.output_dir
    )
    print(f"Observed pixel sample: {npz}")
    print(f"Source manifest: {manifest}")
    print("Status: real pixel inputs acquired; scientific validation NOT performed")


if __name__ == "__main__":
    main()
