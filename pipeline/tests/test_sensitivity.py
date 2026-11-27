"""Offline tests for the sensitivity helpers and the new index / mask options.

All arrays below are small synthetic fixtures (data_status: synthetic_demonstration).
They check arithmetic and bookkeeping, not scientific validity.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pytest

from pipeline.src import case_study as cs
from pipeline.src import robustness as rb
from pipeline.src import sensitivity as sv


def test_evi_and_ndmi_formulas():
    bands = {
        "blue": np.array([[0.05, 0.0]], dtype="float32"),
        "red": np.array([[0.08, 0.0]], dtype="float32"),
        "nir": np.array([[0.40, 0.0]], dtype="float32"),
        "swir16": np.array([[0.20, 0.0]], dtype="float32"),
    }
    evi = cs.compute_index("evi", bands)
    expected = 2.5 * (0.40 - 0.08) / (0.40 + 6 * 0.08 - 7.5 * 0.05 + 1)
    assert evi[0, 0] == pytest.approx(expected, rel=1e-5)
    ndmi = cs.compute_index("ndmi", bands)
    assert ndmi[0, 0] == pytest.approx((0.40 - 0.20) / 0.60, rel=1e-5)
    assert np.isnan(ndmi[0, 1])  # zero denominator
    assert set(cs.ALL_INDEX_BANDS["evi"]) == {"blue", "red", "nir"}
    assert set(cs.ALL_INDEX_BANDS["ndmi"]) == {"nir", "swir16"}
    assert "evi" not in cs.INDEX_BANDS  # published configs cannot select it


def test_sensitivity_index_needs_opt_in():
    raw = {
        "case_id": "x",
        "title": "x",
        "bbox": [-8.0, 38.0, -7.9, 38.1],
        "index": "ndmi",
        "before_item": "a",
        "after_item": "b",
        "control_before_item": "c",
        "control_after_item": "b",
        "primary_threshold": "control_p99",
        "thresholds": [0.1, 0.2],
    }
    with pytest.raises(ValueError):
        cs.CaseStudyConfig.from_mapping(raw)
    assert (
        cs.CaseStudyConfig.from_mapping(raw, allow_sensitivity_index=True).index
        == "ndmi"
    )


def test_buffered_valid_mask_zero_buffer_is_plain_mask():
    scl = np.array([[4, 5, 6, 9], [3, 4, 4, 4], [4, 4, 8, 4]], dtype="uint8")
    np.testing.assert_array_equal(
        cs.buffered_valid_mask(scl, (4, 5, 6), (3, 8, 9, 10), 0),
        cs.scl_valid_mask(scl, (4, 5, 6)),
    )


def test_buffered_valid_mask_grows_square_buffer():
    scl = np.full((9, 9), 4, dtype="uint8")
    scl[4, 4] = 9  # one cloud pixel
    m1 = cs.buffered_valid_mask(scl, (4,), (3, 8, 9, 10), 1)
    m2 = cs.buffered_valid_mask(scl, (4,), (3, 8, 9, 10), 2)
    assert (~m1).sum() == 9 and (~m2).sum() == 25
    assert not m2[2, 2] and m2[1, 1]
    # water and bare soil are not buffered
    scl[4, 4] = 6
    assert cs.buffered_valid_mask(scl, (4,), (3, 8, 9, 10), 2).sum() == 80


def test_scale_bbox_about_centre():
    out = sv.scale_bbox((0.0, 10.0, 2.0, 12.0), 0.5)
    assert out == (0.5, 10.5, 1.5, 11.5)
    big = sv.scale_bbox((0.0, 10.0, 2.0, 12.0), 1.3)
    assert big[2] - big[0] == pytest.approx(2.6)
    with pytest.raises(ValueError):
        sv.scale_bbox((0.0, 10.0, 2.0, 12.0), 0)


def _row(iid, day, cloud=0.01, tile="29SNC", orbit="037", baseline="05.11"):
    return {
        "id": iid,
        "datetime": f"{day}T11:30:00Z",
        "mgrs_tile": tile,
        "relative_orbit": orbit,
        "processing_baseline": baseline,
        "eo_cloud_cover": cloud,
    }


def test_pick_scene_rule_and_ties():
    rows = [
        _row("a", "2023-08-17"),
        _row("b", "2023-08-25"),  # 4 days after target, same as a
        _row("c", "2023-08-21", cloud=2.0),  # too cloudy
        _row("d", "2023-08-21", tile="29SNB"),  # other tile
        _row("e", "2023-08-20", baseline="02.13"),  # old baseline
        _row("f", "2023-08-22", orbit="080"),  # other orbit
    ]
    best = sv.pick_scene(rows, date(2023, 8, 21), "29SNC", "037")
    assert best["id"] == "a" and best["days_from_target"] == -4
    assert (
        sv.pick_scene(rows, date(2023, 8, 21), "29SNC", "037", exclude=["a"])["id"]
        == "b"
    )
    with pytest.raises(LookupError):
        sv.pick_scene(rows, date(2023, 8, 21), "29SNC", "037", exclude=["a", "b"])


def test_continuous_p99_and_percent_change():
    c = np.concatenate([np.linspace(-1, 1, 201), [np.nan]]).astype("float32")
    assert sv.continuous_p99(c) == pytest.approx(np.percentile(np.abs(c[:-1]), 99))
    with pytest.raises(ValueError):
        sv.continuous_p99(np.array([np.nan]))
    assert sv.percent_change(110.0, 100.0) == pytest.approx(10.0)
    assert sv.percent_change(1.0, 0.0) is None
    assert sv.percent_change(None, 1.0) is None


def test_change_summary_matches_change_mask_and_water_rule():
    delta = np.zeros((20, 20), dtype="float32")
    delta[2:8, 2:8] = 0.5  # 36 px increase
    delta[12:14, 12:14] = -0.5  # 4 px decrease (below min patch of 9 px)
    delta[15:19, 15:19] = 0.5  # 16 px increase over water
    joint = np.ones_like(delta, dtype=bool)
    water = np.zeros_like(joint)
    water[15:19, 15:19] = True
    control = np.full(delta.shape, 0.01, dtype="float32")
    control[0, :4] = 0.6
    s, inc, dec = sv.change_summary(
        delta, control, joint, water, 0.3, 0.09, 100.0, True
    )
    assert s["min_patch_pixels"] == 9
    assert int(inc.sum()) == 36 and int(dec.sum()) == 0
    np.testing.assert_array_equal(inc, rb.change_mask(delta, 0.3, 9, water, "increase"))
    assert s["increase_area_ha"] == pytest.approx(0.36)
    assert s["decrease_pixels_raw"] == 4
    assert s["control_flagged_share_at_threshold"] == pytest.approx(4 / 400)
    s2, inc2, _ = sv.change_summary(
        delta, control, joint, water, 0.3, 0.09, 100.0, False
    )
    assert int(inc2.sum()) == 52 and s2["increase_patches_ge_min"] == 2


def test_class_crosstab_counts_and_shares():
    classes = np.array([[1, 1, 2], [2, 0, 0]])
    a = np.array([[True, False, True], [False, False, True]])
    b = np.array([[False, True, False], [True, False, False]])
    dom = np.ones_like(a)
    rows = sv.class_crosstab(
        classes, {"a": a, "b": b}, {1: "one", 2: "two"}, dom, 100.0
    )
    by = {r["class"]: r for r in rows}
    assert by["one"]["a_pixels"] == 1 and by["one"]["b_pixels"] == 1
    assert by["two"]["a_share"] == pytest.approx(1 / 3) and by["two"]["b_pixels"] == 1
    assert by["none"]["a_pixels"] == 1 and by["none"]["a_area_ha"] == pytest.approx(
        0.01
    )
