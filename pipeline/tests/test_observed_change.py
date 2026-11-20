"""Synthetic test arrays are fixtures only; NEVER published as observed evidence."""
from __future__ import annotations

from copy import deepcopy

import numpy as np
import pytest

from pipeline.observed_change import analyze_pair

BBOX = [-68.25, -23.48, -68.238, -23.468]


def example_scene(date: str, scene_id: str):
    meta = {
        "scene_id": scene_id,
        "acquired": date,
        "collection": "sentinel-2-l2a",
        "pixel_grid_crs": "EPSG:4326",
        "grid_shape": [16, 16],
        "s2_processing_baseline": "05.11",
        "boa_add_offset_dn": -1000,
        "bounding_box": BBOX,
    }
    bands = {
        "B2": np.full((16, 16), 0.1),
        "B3": np.full((16, 16), 0.1),
        "B4": np.full((16, 16), 0.1),
        "B8": np.full((16, 16), 0.3),
        "B11": np.full((16, 16), 0.1),
        "QA60": np.zeros((16, 16), dtype=np.uint16),
    }
    return bands, meta


def test_real_pair_contract_with_fixture_arrays():
    before, bmeta = example_scene("2024-10-04T14:00:00Z", "TEST_BEFORE")
    after, ameta = example_scene("2025-10-04T14:00:00Z", "TEST_AFTER")
    after["B8"][0:8, 0:8] = 0.1
    report = analyze_pair(before, after, bmeta, ameta, BBOX)
    assert report["type"] == "FeatureCollection"
    assert report["overlap_valid_pixels"] == 256
    assert report["flagged_pixel_count"] == 64
    assert len(report["features"]) == 4
    assert report["model_performance"] == "not_evaluated"
    assert report["verification_status"] == "observed_pixels_unvalidated_change"
    assert report["features"][0]["properties"]["drop_fraction"] == 1.0
    assert report["features"][-1]["properties"]["drop_fraction"] == 0.0
    assert len(report["derived_arrays_sha256"]) == 64
    assert report["boa_add_offset_dn"] == [-1000, -1000]
    assert report["s2_processing_baselines"] == ["05.11", "05.11"]


def test_missing_pixels_cannot_be_zeros_or_flags():
    before, bmeta = example_scene("2024-10-04T14:00:00Z", "TEST_BEFORE")
    after, ameta = example_scene("2025-10-04T14:00:00Z", "TEST_AFTER")
    after["B8"][:, :] = np.nan
    with pytest.raises(ValueError, match="insufficient overlapping"):
        analyze_pair(before, after, bmeta, ameta, BBOX)


@pytest.mark.parametrize("case", ["same_scene", "backdated", "missing_lineage", "wrong_bbox", "wrong_grid"])
def test_fail_closed_source_integrity(case):
    before, bmeta = example_scene("2024-10-04T14:00:00Z", "TEST_BEFORE")
    after, ameta = example_scene("2025-10-04T14:00:00Z", "TEST_AFTER")
    if case == "same_scene":
        ameta["scene_id"] = "TEST_BEFORE"
    elif case == "backdated":
        ameta["acquired"] = "2023-10-04T14:00:00Z"
    elif case == "missing_lineage":
        del ameta["collection"]
    elif case == "wrong_bbox":
        ameta["bounding_box"] = [-1, -1, 1, 1]
    elif case == "wrong_grid":
        ameta["grid_shape"] = [8, 8]
    with pytest.raises(ValueError):
        analyze_pair(before, after, bmeta, ameta, BBOX)


def test_input_arrays_not_mutated():
    before, bmeta = example_scene("2024-10-04T14:00:00Z", "TEST_BEFORE")
    after, ameta = example_scene("2025-10-04T14:00:00Z", "TEST_AFTER")
    before_copy = deepcopy(before)
    analyze_pair(before, after, bmeta, ameta, BBOX)
    for k, v in before.items():
        np.testing.assert_array_equal(v, before_copy[k])
