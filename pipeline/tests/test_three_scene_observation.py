"""Only synthetic fixtures; live three-date observations are stored separately."""
from copy import deepcopy

import numpy as np
import pytest

from pipeline.three_scene_observation import analyze_three

BBOX = [-68.25, -23.48, -68.238, -23.468]


def scene(n):
    bands = {key: np.full((8, 8), .08) for key in ("B2", "B3", "B4", "B8", "B11")}
    bands["QA60"] = np.zeros((8, 8), dtype=np.uint16)
    bands["B8"][:] = (.3, .2, .1)[n]
    meta = {
        "scene_id": f"TEST_SCENE_{n}",
        "acquired": f"{2024+n}-10-09T14:00:00Z",
        "collection": "sentinel-2-l2a",
        "pixel_grid_crs": "EPSG:4326",
        "grid_shape": [8, 8],
        "s2_processing_baseline": "05.11",
        "boa_add_offset_dn": -1000,
        "bounding_box": BBOX,
    }
    return bands, meta


def inputs():
    pairs = [scene(n) for n in range(3)]
    return [p[0] for p in pairs], [p[1] for p in pairs]


def test_three_way_mask_gives_same_denominator_for_all_deltas():
    samples, metas = inputs()
    samples[0]["B8"][0, 0] = np.nan
    samples[2]["B8"][0, 1] = np.nan
    result = analyze_three(samples, metas, BBOX)
    assert result["common_valid_pixels"] == 62
    assert result["per_scene_valid_pixels"] == [63, 64, 63]
    assert result["total_grid_pixels"] == 64
    assert len(result["derived_arrays_sha256"]) == 64
    assert result["independent_ground_truth"] == "not_available"
    assert result["model_performance"] == "not_evaluated"
    assert result["comparison_2024_2025"]["median_ndvi_delta"] < 0
    assert result["comparison_2025_2026"]["median_ndvi_delta"] < 0
    assert result["comparison_2024_2026"]["median_ndvi_delta"] < 0


def test_inputs_are_not_mutated():
    samples, metas = inputs()
    saved = deepcopy(samples)
    analyze_three(samples, metas, BBOX)
    for actual, expected in zip(samples, saved):
        for name in expected:
            np.testing.assert_array_equal(actual[name], expected[name])


@pytest.mark.parametrize("change", ["duplicate", "date", "bbox", "baseline", "shape", "missing", "insufficient", "length"])
def test_bad_three_scene_contracts_fail_closed(change):
    samples, metas = inputs()
    if change == "duplicate":
        metas[2]["scene_id"] = metas[1]["scene_id"]
    elif change == "date":
        metas[2]["acquired"] = "2023-10-09T14:00:00Z"
    elif change == "bbox":
        metas[1]["bounding_box"] = [0, 0, 1, 1]
    elif change == "baseline":
        metas[1]["boa_add_offset_dn"] = 0
    elif change == "shape":
        samples[2]["B8"] = np.full((7, 8), .1)
    elif change == "missing":
        del metas[0]["scene_id"]
    elif change == "insufficient":
        samples[1]["B8"][:,:] = np.nan
    elif change == "length":
        samples.pop()
    with pytest.raises((ValueError, KeyError)):
        analyze_three(samples, metas, BBOX)
