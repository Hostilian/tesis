"""Offline tests for the robustness module.

All arrays below are small synthetic fixtures (data_status: synthetic_demonstration).
They check arithmetic and bookkeeping, not scientific validity.
"""

from __future__ import annotations

import numpy as np
import pytest

from pipeline.src import reference_cos as rc
from pipeline.src import robustness as rb


def _synthetic_scene():
    """40 x 40 synthetic grid: a 10 x 10 'new crop' square, a 6 x 6 false alarm."""
    delta = np.zeros((40, 40), dtype="float32")
    ref = np.zeros((40, 40), dtype=bool)
    ref[5:15, 5:15] = True
    delta[5:15, 5:15] = 0.4  # true change, strong
    delta[5:15, 12:15] = 0.2  # part of the true change, weaker
    delta[25:31, 25:31] = 0.35  # false alarm
    delta[0, 0] = np.nan
    domain = np.isfinite(delta)
    control = np.full((40, 40), 0.01, dtype="float32")
    control[0, :4] = 0.3  # 4 of 1600 control pixels above 0.25
    return delta, ref, domain, control


def test_grid_values_inclusive_and_rounded():
    g = rb.grid_values(0.05, 0.5, 0.025)
    assert g[0] == 0.05 and g[-1] == 0.5 and len(g) == 19
    assert 0.075 in g and 0.3 in g
    assert rb.union_grid([0.3, 0.4], [0.05, 0.3]) == [0.05, 0.3, 0.4]
    with pytest.raises(ValueError):
        rb.grid_values(0.5, 0.1, 0.1)


def test_change_mask_patch_filter_and_exclusion():
    delta, _, _, _ = _synthetic_scene()
    m = rb.change_mask(delta, 0.3, min_pixels=50)
    assert m[5:15, 5:12].all() and not m[25:31, 25:31].any()  # 36 px < 50 removed
    assert m.sum() == 70
    excl = np.zeros_like(m)
    excl[5:15, 5:8] = True
    assert rb.change_mask(delta, 0.3, 1, exclude=excl)[5:15, 5:8].sum() == 0
    assert rb.change_mask(-delta, 0.3, 1, direction="decrease").sum() == 70 + 36
    with pytest.raises(ValueError):
        rb.change_mask(delta, 0.3, 1, direction="sideways")


def test_confusion_matches_reference_cos_binary_agreement():
    delta, ref, domain, _ = _synthetic_scene()
    pred = rb.change_mask(delta, 0.15, 1)
    mine = rb.confusion(pred, ref, domain)
    theirs = rc.binary_agreement(pred[domain], ref[domain])
    for k in ("tp", "fp", "fn", "tn"):
        assert mine[k] == theirs[k]
    assert mine["precision"] == pytest.approx(theirs["precision"])
    assert mine["recall"] == pytest.approx(theirs["recall"])
    assert mine["f1"] == pytest.approx(theirs["f1"])


def test_scores_undefined_is_nan_not_zero():
    s = rb.scores(np.array([0, 5]), np.array([0, 5]), np.array([0, 0]))
    assert np.isnan(s["precision"][0]) and s["precision"][1] == 0.5
    assert np.isnan(s["recall"][0]) and s["recall"][1] == 1.0


def test_threshold_curve_counts_and_control_share():
    delta, ref, domain, control = _synthetic_scene()
    rows = rb.threshold_curve(
        delta, control, ref, domain, [0.1, 0.25, 0.3, 0.5], 1, 100.0
    )
    by_t = {r["threshold"]: r for r in rows}
    # t = 0.1: whole true square (100) + false alarm (36)
    assert by_t[0.1]["tp"] == 100 and by_t[0.1]["fp"] == 36
    assert by_t[0.1]["recall"] == 1.0
    assert by_t[0.1]["flagged_area_ha"] == pytest.approx(136 * 100 / 10_000)
    # t = 0.3: the weaker 0.2 strip drops out
    assert by_t[0.3]["tp"] == 70 and by_t[0.3]["fn"] == 30 and by_t[0.3]["fp"] == 36
    # t = 0.5: nothing flagged, precision undefined
    assert by_t[0.5]["flagged_pixels"] == 0 and by_t[0.5]["precision"] is None
    assert by_t[0.25]["control_flagged_share"] == pytest.approx(4 / 1600)
    assert by_t[0.3]["control_flagged_share"] == 0.0
    flagged = [r["flagged_pixels"] for r in rows]
    assert flagged == sorted(flagged, reverse=True)


def test_block_index_shapes_and_ids():
    ids = rb.block_index((5, 7), 3)
    assert ids.shape == (5, 7)
    assert ids[0, 0] == 0 and ids[0, 3] == 1 and ids[0, 6] == 2 and ids[3, 0] == 3
    assert len(np.unique(ids)) == 2 * 3
    with pytest.raises(ValueError):
        rb.block_index((5, 5), 0)


def test_group_counts_sum_to_totals_and_skip_empty_blocks():
    delta, ref, domain, _ = _synthetic_scene()
    pred = rb.change_mask(delta, 0.3, 1)
    dom = domain.copy()
    dom[30:, :] = False  # blocks fully outside the domain must be dropped
    counts = rb.group_counts(pred, ref, dom, rb.block_index(pred.shape, 10))
    assert counts.shape == (12, 3)  # 3 of 4 block rows remain, 4 columns
    c = rb.confusion(pred, ref, dom)
    assert counts.sum(axis=0).tolist() == [c["tp"], c["fp"], c["fn"]]


def test_block_bootstrap_perfect_prediction_has_degenerate_ci():
    _, ref, domain, _ = _synthetic_scene()
    b = rb.block_bootstrap(ref, ref, domain, block_px=5, iterations=200, seed=1)
    for k in ("precision", "recall", "f1"):
        assert b[k]["estimate"] == 1.0
        assert b[k]["ci_low"] == 1.0 and b[k]["ci_high"] == 1.0
    assert b["units"] == 64 and b["block_px"] == 5


def test_block_bootstrap_is_reproducible_and_brackets_estimate():
    delta, ref, domain, _ = _synthetic_scene()
    rng = np.random.default_rng(7)  # synthetic noise flags
    pred = rb.change_mask(delta, 0.15, 1) | (rng.random(delta.shape) < 0.05)
    a = rb.block_bootstrap(pred, ref, domain, 5, iterations=300, seed=42)
    b = rb.block_bootstrap(pred, ref, domain, 5, iterations=300, seed=42)
    c = rb.block_bootstrap(pred, ref, domain, 5, iterations=300, seed=43)
    assert a["precision"] == b["precision"] and a["recall"] == b["recall"]
    assert a["precision"]["ci_low"] != c["precision"]["ci_low"] or (
        a["precision"]["ci_high"] != c["precision"]["ci_high"]
    )
    for k in ("precision", "recall"):
        assert a[k]["ci_low"] <= a[k]["estimate"] <= a[k]["ci_high"]
    assert a["seed"] == 42 and a["iterations"] == 300
    assert a["precision"]["estimate"] == pytest.approx(
        rb.confusion(pred, ref, domain)["precision"]
    )


def test_bootstrap_counts_reports_undefined_iterations():
    # Only one of 20 units has any flag, so many resamples have tp + fp = 0.
    counts = np.zeros((20, 3), dtype="int64")
    counts[0] = [1, 0, 0]
    counts[1:, 2] = 1
    out = rb.bootstrap_counts(counts, iterations=500, seed=3)
    assert out["precision"]["undefined_iterations"] > 0
    assert out["recall"]["undefined_iterations"] == 0
    with pytest.raises(ValueError):
        rb.bootstrap_counts(np.zeros((0, 3)), 10, 0)
    with pytest.raises(ValueError):
        rb.bootstrap_counts(np.zeros((4, 2)), 10, 0)


def test_polygon_unit_labels_match_reference_cos_polygon_agreement():
    units = np.zeros((20, 20), dtype="int32")
    units[:10, :10], units[:10, 10:], units[10:, :10], units[10:, 10:] = 1, 2, 3, 4
    units[19, 19] = 5  # a unit too small to evaluate
    ref = np.zeros((20, 20), dtype=bool)
    ref[:10, :] = True  # units 1 and 2 positive
    pred = np.zeros((20, 20), dtype=bool)
    pred[:10, :10] = True  # unit 1 detected
    pred[10:, 10:16] = True  # unit 4: 60 % flagged -> detected, false positive
    valid = np.ones((20, 20), dtype=bool)
    up, ur = rb.polygon_unit_labels(units, pred, ref, valid, min_pixels=10)
    assert up.tolist() == [True, False, False, True]
    assert ur.tolist() == [True, True, False, False]
    agg = rc.polygon_agreement(units, pred, ref, valid, min_pixels=10)
    b = rb.unit_bootstrap(up, ur, iterations=100, seed=0)
    assert b["totals"] == {"tp": agg["tp"], "fp": agg["fp"], "fn": agg["fn"]}
    assert b["units"] == agg["units_evaluated"] == 4
    assert b["precision"]["estimate"] == pytest.approx(agg["precision"])


def test_mask_overlap_and_strip_draws():
    a = np.array([True, True, False, False])
    b = np.array([True, False, True, False])
    o = rb.mask_overlap(a, b)
    assert o["pixels_both"] == 1 and o["jaccard"] == pytest.approx(1 / 3)
    assert o["share_of_a_also_in_b"] == 0.5
    empty = rb.mask_overlap(np.zeros(3, bool), np.zeros(3, bool))
    assert empty["jaccard"] is None
    nested = {"x": {"_draws": [1], "keep": 1}, "y": [{"_draws": 2, "z": 3}]}
    assert rb.strip_draws(nested) == {"x": {"keep": 1}, "y": [{"z": 3}]}
