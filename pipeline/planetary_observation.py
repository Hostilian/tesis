"""Read real, publicly accessible Sentinel-2 pixels from Planetary Computer.

Unlike the thesis demonstrator, this module fails closed on missing pixels.
No private company geometry, credentials or synthetic fallback is involved.
Outputs are local, git-ignored research artifacts, not published anomaly claims.

Example:
    python -m pipeline.planetary_observation \\
      --bbox -68.250 -23.480 -68.238 -23.468 \\
      --start 2024-10-01 --end 2024-10-15
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from pipeline.real_observation import (
    BAND_NAMES,
    _ensure_private_path,
    validate_request,
)
from pipeline.src.preprocessing import GeospatialPreprocessor

PUBLIC_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
RASTER_GRID_PIXELS = 96


def select_scene_metadata(items: list[Any]) -> Any:
    """Select a real STAC scene with the required multispectral band assets."""
    eligible = []
    for item in items:
        assets = getattr(item, "assets", {})
        missing = [key for key in (*BAND_NAMES, "SCL") if key not in assets]
        if missing:
            continue
        properties = getattr(item, "properties", {})
        cloud = properties.get("eo:cloud_cover", 100.0)
        try:
            fraction = float(cloud)
        except (ValueError, TypeError):
            continue
        if not (0 <= fraction <= 60) or not getattr(item, "id", ""):
            continue
        eligible.append((fraction, str(item.id), item))
    if not eligible:
        raise ValueError("No item with source ID, clouds and required raster assets")
    return min(eligible, key=lambda choice: (choice[0], choice[1]))[2]


def mask_real_pixels(
    spectral: dict[str, np.ndarray], scl: np.ndarray
) -> dict[str, np.ndarray]:
    """Apply Sentinel-2 scene classification to aligned observed reflectances."""
    shape = scl.shape
    if scl.ndim != 2 or not scl.size:
        raise ValueError("Empty SCL raster")
    if any(spectral[key].shape != shape for key in BAND_NAMES):
        raise ValueError("Spectral assets are not on the SCL preview grid")
    # SCL 0 no data, 1 saturated, 3 shadow, 8-10 clouds, 11 snow/ice.
    excluded = np.isin(scl, [0, 1, 3, 8, 9, 10, 11])
    valid = np.isfinite(scl) & ~excluded
    output = {}
    for name in BAND_NAMES:
        band = np.asarray(spectral[name], dtype=np.float64)
        valid &= np.isfinite(band) & (band > 0) & (band < 65535)
        output[name] = band
    if int(np.count_nonzero(valid)) < 20:
        raise ValueError("Insufficient valid real Sentinel-2 pixels after masking")
    for key in BAND_NAMES:
        output[key] = np.where(valid, output[key] / 10000.0, np.nan)
    # All invalid pixels have NaN reflectance; zero QA60 is not a claim that
    # clouds are absent (the stronger SCL mask was already applied above).
    output["QA60"] = np.zeros(shape, dtype=np.uint16)
    return output


def read_planetary_sample(
    bbox: list[float], start: str, end: str
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Read real COG pixels on one aligned grid, with no synthetic fallback."""
    validate_request(bbox, start, end)
    try:
        from planetary_computer import sign_inplace
        from pystac_client import Client
        import rasterio
        from rasterio.enums import Resampling
        from rasterio.transform import from_bounds
        from rasterio.vrt import WarpedVRT
    except ImportError as exc:
        raise RuntimeError(
            "Install pipeline/requirements.txt (planetary-computer, "
            "pystac-client and rasterio)"
        ) from exc

    catalog = Client.open(PUBLIC_STAC_URL, modifier=sign_inplace)
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=f"{start}/{end}",
        query={"eo:cloud_cover": {"lt": 60}},
        max_items=8,
    )
    scene = select_scene_metadata(list(search.items()))
    transform = from_bounds(*bbox, RASTER_GRID_PIXELS, RASTER_GRID_PIXELS)
    values: dict[str, np.ndarray] = {}
    for key in (*BAND_NAMES, "SCL"):
        asset = scene.assets[key]
        resampling = (
            Resampling.nearest if key == "SCL" else Resampling.bilinear
        )
        # Signed asset URLs are used solely in memory and never written.
        with rasterio.open(asset.href) as source:
            with WarpedVRT(
                source,
                crs="EPSG:4326",
                transform=transform,
                width=RASTER_GRID_PIXELS,
                height=RASTER_GRID_PIXELS,
                resampling=resampling,
            ) as vrt:
                values[key] = (
                    vrt.read(1, masked=True)
                    .astype(np.float64)
                    .filled(np.nan)
                )
    bands = mask_real_pixels(
        {name: values[name] for name in BAND_NAMES}, values["SCL"]
    )
    return bands, {
        "scene_id": str(scene.id),
        "acquired": scene.properties.get("datetime"),
        "cloud_cover_catalog_pct": scene.properties.get("eo:cloud_cover"),
        "collection": "sentinel-2-l2a",
        "public_stac_url": PUBLIC_STAC_URL,
        "asset_keys": list((*BAND_NAMES, "SCL")),
        "grid_shape": [RASTER_GRID_PIXELS, RASTER_GRID_PIXELS],
        "pixel_grid_crs": "EPSG:4326",
        "bounding_box": bbox,
        "evidence_state": "real_pixel_inputs_unvalidated",
    }


def save_private_sample(
    bands: dict[str, np.ndarray],
    metadata: dict[str, Any],
    output_dir: Path,
) -> tuple[Path, Path]:
    """Write actual pixels and unsigned manifest outside the published site."""
    out = _ensure_private_path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = out / f"planetary_observed_{timestamp}"
    pixel_file = base.with_suffix(".npz")
    manifest_file = base.with_suffix(".json")
    if pixel_file.exists() or manifest_file.exists():
        raise FileExistsError("Observation already exists; refusing overwrite")
    result = GeospatialPreprocessor().process_raw_bands(bands)
    if not any(np.isfinite(result["ndvi"]).flat):
        raise ValueError("No usable NDVI observations")
    np.savez_compressed(
        pixel_file,
        **{band: bands[band] for band in BAND_NAMES},
        ndvi=result["ndvi"],
        ndwi=result["ndwi"],
        bsi=result["bsi"],
    )
    record = {
        **metadata,
        "checksum_sha256": hashlib.sha256(pixel_file.read_bytes()).hexdigest(),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_validation": "not_performed",
        "model_performance": "not_evaluated",
        "independent_ground_truth": "not_available",
        "notice": (
            "Observed source pixels, not an independently verified economic "
            "event; no model-performance or geospatial-change claim is made."
        ),
    }
    manifest_file.write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8"
    )
    return pixel_file, manifest_file


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bbox", nargs=4, type=float, required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("research_private/observations")
    )
    args = parser.parse_args()
    bands, metadata = read_planetary_sample(
        args.bbox, args.start, args.end
    )
    data, evidence = save_private_sample(bands, metadata, args.output_dir)
    print(f"Observed pixel sample saved privately: {data}")
    print(f"Unvalidated-source manifest: {evidence}")


if __name__ == "__main__":
    main()
