"""Scientific provenance safeguards for the Portugal-first public preview.

These are static-source checks, not an independently labeled event evaluation.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs/experimental/geo-intelligence/data/portugal_alentejo_ndvi_change_20261123.geojson"
REGIONS = ROOT / "docs/research/portugal-europe-study-areas.json"
VIEWER = ROOT / "docs/experimental/geo-intelligence/index.html"


def test_portugal_public_experiment_is_real_but_interpretation_unvalidated():
    result = json.loads(DATA.read_text(encoding="utf-8"))
    assert result["schema"] == "sbei.observed_ndvi_change.v1"
    assert result["synthetic_data"] is False
    assert result["verification_status"] == "observed_pixels_unvalidated_change"
    assert result["independent_ground_truth"] == "not_available"
    assert result["model_performance"] == "not_evaluated"
    assert result["overlap_valid_pixels"] == 9216
    assert result["total_grid_pixels"] == 9216
    assert result["bounding_box"] == [-8.03, 38.53, -8.018, 38.542]
    assert len(result["features"]) == 144
    assert len(result["scenes"]) == 2
    assert all("_T29SNC_" in scene for scene in result["scenes"])
    assert result["derived_arrays_sha256"] == "89f27454c67a008f91304468d4d8fbae7dda1cd71fd08e2119492805c8b01ee7"
    assert all(f["properties"]["verification_status"] == "unverified_interpretation"
               for f in result["features"])


def test_public_geojson_contains_only_approved_research_properties():
    result = json.loads(DATA.read_text(encoding="utf-8"))
    allowed_top = {"type", "schema", "verification_status", "synthetic_data",
                   "source_provider", "collection", "scenes", "acquisition_times",
                   "s2_processing_baselines", "boa_add_offset_dn", "quality_mask",
                   "spatial_reference", "bounding_box", "derived_arrays_sha256",
                   "processing_version", "analysis_method", "threshold_ndvi_delta",
                   "overlap_valid_pixels", "total_grid_pixels", "flagged_pixel_count",
                   "median_ndvi_delta", "independent_ground_truth", "model_performance",
                   "limitations", "features", "processed_utc"}
    allowed_props = {"valid_overlap_pixels", "median_ndvi_delta",
                     "heuristic_drop_pixels", "drop_fraction", "verification_status"}
    assert set(result) <= allowed_top
    west, south, east, north = result["bounding_box"]
    for f in result["features"]:
        assert f["type"] == "Feature"
        assert f["geometry"]["type"] == "Polygon"
        assert set(f["properties"]) <= allowed_props
        assert 0 < f["properties"]["valid_overlap_pixels"] <= 64
        for ring in f["geometry"]["coordinates"]:
            for x, y in ring:
                assert west <= x <= east and south <= y <= north


def test_geographic_priority_and_preview_are_explicit():
    areas = json.loads(REGIONS.read_text(encoding="utf-8"))
    assert areas["public_geography_only"] is True
    assert areas["default_region"] == "portugal_evora_west"
    assert areas["approved_thesis_title_change"] is False
    assert areas["europe_comparator"]["status"] == "not_yet_selected_or_queried"
    html = VIEWER.read_text(encoding="utf-8")
    assert 'id="area"' in html
    assert "portugal_alentejo_ndvi_change_20261123.geojson" in html
    assert "observed_ndvi_change_20261120.geojson" in html
    assert "unvalidated" in html.lower()

def test_portugal_gods_eye_scene_reuses_official_bundle_contract():
    """Public 3D export preserves a separate Portugal identity and narrow data fields."""
    import base64
    import hashlib
    from pipeline.gods_eye_bridge import (
        PORTUGAL_SOURCE, PORTUGAL_OUTPUT, checked_public_observation, build_bundle,
    )

    observed = checked_public_observation(PORTUGAL_SOURCE)
    bundle = build_bundle(observed, region="portugal")
    assert bundle == json.loads(PORTUGAL_OUTPUT.read_text(encoding="utf-8"))
    assert bundle["format"] == "gev-scene-bundle"
    assert bundle["project"]["scenes"][0]["id"] == "sbei-observed-portugal-sentinel2-2025-2026"
    pack = bundle["project"]["scenes"][0]["dataPacks"][0]
    payload = base64.b64decode(bundle["assets"][0]["base64"], validate=True)
    assert hashlib.sha256(payload).hexdigest() == pack["sha256"]
    assert pack["byteLength"] == len(payload)
    exported = json.loads(payload)["features"]
    assert len(exported) == 144
    assert all(f["properties"]["verification_status"] == "observed_pixels_unvalidated_change" for f in exported)
    assert all(len(f["geometry"]["coordinates"][0][0]) == 3 for f in exported)
    assert all(f["geometry"]["coordinates"][0][0][2] == 6500 for f in exported)
    assert "farm_sensor_secret" not in payload.decode("utf-8")
    assert "agrotics" not in payload.decode("utf-8").lower()
