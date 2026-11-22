"""Export *reviewed public* thesis observations to a God's Eye View Director scene.

No upstream source or third-party dataset is copied. Output is a portable,
integrity-checked GEV scene bundle, using the documented version-1 format.
Only the repository's reviewed public 2024→2025 observation is eligible.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/experimental/geo-intelligence/data/observed_ndvi_change_20261120.geojson"
OUTPUT = ROOT / "docs/experimental/geo-intelligence/gods-eye/sentinel2-observed-2024-2025.gevbundle.json"
ATTRIBUTION = {
    "text": "Contains modified Copernicus Sentinel-2 (2024, 2025) observations; Microsoft Planetary Computer STAC; SBEI thesis derived grid",
    "license": "Copernicus Sentinel Data Policy (third-party data terms apply)",
    "url": "https://dataspace.copernicus.eu/terms-and-conditions",
}
PACK_PATH = "atlas/sentinel2-observed-2024-2025.geojson"
DISPLAY_HEIGHT_METRES = 6500  # geometric illustration, NOT sensor altitude or land elevation


def checked_public_observation(source: Path = SOURCE) -> dict:
    """Fail closed rather than exporting unknown or potentially private data."""
    if source.resolve() != SOURCE.resolve():
        raise ValueError("Exporter accepts only the previously reviewed PUBLIC scene")
    raw = source.read_bytes()
    if len(raw) > 8 * 1024 * 1024:
        raise ValueError("Source exceeds the upstream 8 MiB data-pack limit")
    record = json.loads(raw)
    if not (
        record.get("type") == "FeatureCollection"
        and record.get("schema") == "sbei.observed_ndvi_change.v1"
        and record.get("verification_status") == "observed_pixels_unvalidated_change"
        and record.get("synthetic_data") is False
        and record.get("collection") == "sentinel-2-l2a"
        and record.get("spatial_reference") == "EPSG:4326"
        and record.get("source_provider") == "Microsoft Planetary Computer / ESA Sentinel-2"
        and record.get("independent_ground_truth") == "not_available"
        and record.get("model_performance") == "not_evaluated"
        and isinstance(record.get("derived_arrays_sha256"), str)
        and len(record["derived_arrays_sha256"]) == 64
        and len(record.get("scenes", [])) == 2
        and record.get("overlap_valid_pixels", 0) > 0
        and record.get("acquisition_times", ["", ""])[0].startswith("2024-")
        and record.get("acquisition_times", ["", ""])[1].startswith("2025-")
    ):
        raise ValueError("Source provenance or review gate failed")
    features = record.get("features")
    if not isinstance(features, list) or not (1 <= len(features) <= 2000):
        raise ValueError("Missing or oversized reviewed polygon features")
    return record


def build_bundle(record: dict) -> dict:
    """Use geographic polygons, finite values and explicit provenance labels."""
    bbox = record["bounding_box"]
    if not (len(bbox) == 4 and all(math.isfinite(float(x)) for x in bbox)):
        raise ValueError("Missing valid bbox")
    west, south, east, north = map(float, bbox)
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("Invalid bbox")
    exported = []
    for n, feature in enumerate(record["features"], 1):
        geometry = feature.get("geometry", {})
        if geometry.get("type") != "Polygon":
            raise ValueError("Only reviewed polygon cells can be exported")
        rings = []
        for ring in geometry.get("coordinates", []):
            if len(ring) < 4:
                raise ValueError("Invalid polygon ring")
            points = []
            for point in ring:
                if len(point) != 2 or not all(math.isfinite(float(v)) for v in point):
                    raise ValueError("Invalid or non-2D coordinate")
                lon, lat = map(float, point)
                if not (west <= lon <= east and south <= lat <= north):
                    raise ValueError("Coordinate outside reviewed public extent")
                points.append([lon, lat, DISPLAY_HEIGHT_METRES])
            if points[0] != points[-1]:
                raise ValueError("Unclosed polygon ring")
            rings.append(points)
        p = feature.get("properties", {})
        delta = p.get("median_ndvi_delta")
        valid = p.get("valid_overlap_pixels")
        if not (
            isinstance(delta, (int, float)) and math.isfinite(delta) and -2 <= delta <= 2
            and type(valid) is int and 0 < valid <= 9216
        ):
            raise ValueError("Invalid observation summary")
        exported.append({
            "type": "Feature",
            "id": f"sbei-public-cell-{n:04d}",
            "geometry": {"type": "Polygon", "coordinates": rings},
            "properties": {
                "median_ndvi_delta": round(float(delta), 6),
                "valid_overlap_pixels": valid,
                "verification_status": "observed_pixels_unvalidated_change",
            },
        })
    payload = {
        "type": "FeatureCollection",
        "features": exported,
    }
    asset = (json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    if len(asset) > 8 * 1024 * 1024:
        raise ValueError("Encoded data pack exceeds upstream 8 MiB limit")
    digest = hashlib.sha256(asset).hexdigest()
    scene = {
        "id": "sbei-observed-sentinel2-2024-2025",
        "title": "SBEI / observed Sentinel-2 2024–2025 / interpretation unvalidated",
        "dataPacks": [{
            "id": "sbei-observed-pixels",
            "version": 1,
            "format": "geojson",
            "source": {"adapter": "scene-bundle", "path": PACK_PATH},
            "attribution": ATTRIBUTION,
            "placement": {"altitudeReference": "ellipsoid"},
            "byteLength": len(asset),
            "sha256": digest,
        }],
        "shots": [{
            "id": "overview",
            "title": "Public evidence grid (not a validated anomaly)",
            "durationSec": 4,
            "holdSec": 2,
            "camera": {"lat": (south + north) / 2, "lon": (west + east) / 2,
                       "alt": 19000, "pitch": -80, "heading": 0, "roll": 0},
            "dataPackIds": ["sbei-observed-pixels"],
        }],
    }
    return {
        "format": "gev-scene-bundle",
        "version": 1,
        "project": {"version": 7, "scenes": [scene]},
        "assets": [{
            "path": PACK_PATH,
            "mimeType": "application/geo+json",
            "base64": base64.b64encode(asset).decode("ascii"),
            "sha256": digest,
        }],
    }


def main() -> None:
    record = checked_public_observation()
    output = build_bundle(record)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"Generated {OUTPUT.relative_to(ROOT)} from reviewed public Sentinel-2 cells")
    print(f"features={len(record['features'])}; overlap_pixels={record['overlap_valid_pixels']}; "
          f"source_derived_sha256={record['derived_arrays_sha256']}")
    print("Research status: observed satellite changes; anomalies and economic causality UNVALIDATED")


if __name__ == "__main__":
    main()
