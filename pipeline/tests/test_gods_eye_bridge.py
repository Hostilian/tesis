"""Contract, privacy and deterministic-output tests for the God’s Eye bridge."""

import base64
import copy
import hashlib
import json
from pathlib import Path

import pytest

from pipeline.gods_eye_bridge import (
    DISPLAY_HEIGHT_METRES, OUTPUT, SOURCE, build_bundle, checked_public_observation,
)


def _asset(bundle):
    return base64.b64decode(bundle["assets"][0]["base64"], validate=True)


def test_reviewed_observations_export_integrity_and_determinism():
    record = checked_public_observation()
    bundle = build_bundle(record)
    asset = _asset(bundle)
    assert bundle == build_bundle(record)
    assert bundle["format"] == "gev-scene-bundle"
    assert bundle["version"] == 1
    assert bundle["project"]["version"] == 7
    assert hashlib.sha256(asset).hexdigest() == bundle["assets"][0]["sha256"]
    pack = bundle["project"]["scenes"][0]["dataPacks"][0]
    assert pack["sha256"] == bundle["assets"][0]["sha256"]
    assert pack["byteLength"] == len(asset)
    assert pack["attribution"]["url"].startswith("https://")
    assert pack["placement"] == {"altitudeReference": "ellipsoid"}
    result = json.loads(asset)
    assert len(result["features"]) == len(record["features"]) == 116
    assert len(set(f["id"] for f in result["features"])) == 116
    assert all(len(f["geometry"]["coordinates"][0][0]) == 3 for f in result["features"])
    assert all(f["geometry"]["coordinates"][0][0][2] == DISPLAY_HEIGHT_METRES
               for f in result["features"])
    assert "synthetic_data" not in result  # Not silently relabelled: provenance is pack/scene.
    assert "raw_sensor_data" not in asset.decode("utf-8")


def test_unknown_input_is_rejected_before_reading(tmp_path):
    fake = tmp_path / "farm_private.geojson"
    fake.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="PUBLIC scene"):
        checked_public_observation(fake)


def test_export_rejects_unreviewed_or_fake_observations():
    record = checked_public_observation()
    record["features"][0]["properties"]["median_ndvi_delta"] = float("nan")
    with pytest.raises(ValueError, match="Invalid observation"):
        build_bundle(record)


def test_export_rejects_out_of_extent_geometry():
    record = checked_public_observation()
    record["features"][0]["geometry"]["coordinates"][0][0][0] = 30.0
    with pytest.raises(ValueError, match="outside"):
        build_bundle(record)


def test_generated_bundle_is_in_sync_with_checked_in_public_artifact():
    assert OUTPUT.is_file(), "run python -m pipeline.gods_eye_bridge first"
    expected = build_bundle(checked_public_observation())
    recorded = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert recorded == expected


def test_export_has_no_unreviewed_custom_properties():
    record = checked_public_observation()
    record["features"][0]["properties"]["farm_sensor_secret"] = "DO_NOT_EXPORT"
    record["private_farm_boundary"] = {"secret": True}
    payload = json.dumps(build_bundle(record))
    assert "DO_NOT_EXPORT" not in payload
    assert "private_farm_boundary" not in payload
    assert "farm_sensor_secret" not in payload
