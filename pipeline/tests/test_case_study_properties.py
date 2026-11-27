"""Property tests: rules the change method must satisfy for ANY input.

Each test draws many random arrays from a seeded generator (synthetic
demonstration data, not evidence) and checks an invariant. No network.
"""

from __future__ import annotations

import numpy as np
import pytest

from pipeline.src import case_study as cs
from pipeline.src import reference_cos as rc

SEEDS = range(25)


def rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(1000 + seed)


def reflectance(g: np.random.Generator, shape=(40, 40)) -> np.ndarray:
    a = g.uniform(0.0, 0.6, shape).astype("float32")
    a[g.random(shape) < 0.03] = np.nan  # some nodata
    return a


@pytest.mark.parametrize("seed", SEEDS)
def test_normalized_difference_bounds_and_antisymmetry(seed):
    g = rng(seed)
    a, b = reflectance(g), reflectance(g)
    nd = cs.normalized_difference(a, b)
    finite = np.isfinite(nd)
    assert np.all(nd[finite] >= -1.0) and np.all(nd[finite] <= 1.0)
    swapped = cs.normalized_difference(b, a)
    np.testing.assert_allclose(nd[finite], -swapped[finite], atol=1e-6)
    # NaN input never produces a finite value
    assert not np.any(finite & (np.isnan(a) | np.isnan(b)))


@pytest.mark.parametrize("seed", SEEDS)
def test_ndvi_matches_textbook_formula(seed):
    g = rng(seed)
    red, nir = reflectance(g), reflectance(g)
    ndvi = cs.compute_index("ndvi", {"red": red, "nir": nir})
    with np.errstate(divide="ignore", invalid="ignore"):
        expected = (nir - red) / (nir + red)
    ok = np.isfinite(expected) & (np.abs(nir + red) > 1e-6)
    np.testing.assert_allclose(ndvi[ok], np.clip(expected[ok], -1, 1), atol=1e-6)


@pytest.mark.parametrize("seed", SEEDS)
def test_to_reflectance_is_linear_and_masks_nodata(seed):
    g = rng(seed)
    dn = g.integers(0, 10000, (30, 30)).astype("uint16")
    scale, offset = 0.0001, float(g.choice([0.0, -0.1]))
    out = cs.to_reflectance(dn, scale, offset, nodata=0)
    valid = dn != 0
    np.testing.assert_allclose(out[valid], dn[valid] * scale + offset, atol=1e-6)
    assert np.all(np.isnan(out[~valid]))


@pytest.mark.parametrize("seed", SEEDS)
def test_difference_swaps_sign_and_respects_masks(seed):
    g = rng(seed)
    b, a = reflectance(g), reflectance(g)
    vb, va = g.random(b.shape) > 0.1, g.random(a.shape) > 0.1
    d1, j1 = cs.difference(b, a, vb, va)
    d2, j2 = cs.difference(a, b, va, vb)
    assert np.array_equal(j1, j2)
    np.testing.assert_allclose(d1[j1], -d2[j2], atol=1e-7)
    assert np.all(np.isnan(d1[~j1]))
    assert not np.any(j1 & ~(vb & va))


@pytest.mark.parametrize("seed", SEEDS)
def test_threshold_table_is_monotone(seed):
    g = rng(seed)
    main = g.normal(0.05, 0.2, 5000).astype("float32")
    ctrl = g.normal(0.0, 0.05, 5000).astype("float32")
    grid = sorted(set(np.round(g.uniform(0.01, 0.6, 8), 3)))
    rows = cs.threshold_table(main, ctrl, grid)
    main_share = [r["main_flagged_share"] for r in rows]
    ctrl_share = [r["control_flagged_share"] for r in rows]
    assert all(x >= y for x, y in zip(main_share, main_share[1:]))
    assert all(x >= y for x, y in zip(ctrl_share, ctrl_share[1:]))
    for r in rows:
        assert (
            r["main_increase_pixels"] + r["main_decrease_pixels"]
            <= r["main_valid_pixels"]
        )


@pytest.mark.parametrize("seed", SEEDS)
def test_resolve_threshold_is_smallest_grid_value_above_p99(seed):
    g = rng(seed)
    ctrl = g.normal(0.0, g.uniform(0.01, 0.1), 4000).astype("float32")
    grid = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.6, 1.0]
    p99 = float(np.percentile(np.abs(ctrl), 99))
    t, _ = cs.resolve_threshold("control_p99", grid, ctrl)
    assert t >= p99
    smaller = [x for x in grid if x < t]
    assert not smaller or max(smaller) < p99
    # at most ~1 % of control pixels can exceed the chosen threshold
    assert (np.abs(ctrl) > t).mean() <= 0.0101


@pytest.mark.parametrize("seed", SEEDS)
def test_patch_filter_only_removes_and_keeps_big_components(seed):
    g = rng(seed)
    mask = g.random((60, 60)) < g.uniform(0.05, 0.5)
    min_px = int(g.integers(1, 40))
    kept = cs.keep_patches_ge(mask, min_px)
    assert not np.any(kept & ~mask)  # never adds pixels
    labels, n = cs.label_patches(kept)
    if n:
        sizes = np.bincount(labels.ravel())[1:]
        assert sizes.min() >= min_px
    stats = cs.patch_statistics(mask, pixel_area_m2=100.0, min_patch_ha=min_px / 100.0)
    assert stats["flagged_pixels"] == int(mask.sum())
    if stats["patches_total"]:
        assert stats["area_ge_min_ha"] == pytest.approx(kept.sum() * 100.0 / 10_000)


@pytest.mark.parametrize("seed", SEEDS)
def test_binary_agreement_counts_and_formulas(seed):
    g = rng(seed)
    pred, ref = g.random(3000) < 0.3, g.random(3000) < 0.4
    out = rc.binary_agreement(pred, ref)
    assert out["tp"] + out["fp"] + out["fn"] + out["tn"] == 3000
    assert out["tp"] == int((pred & ref).sum())
    if out["precision"] is not None:
        assert out["precision"] == pytest.approx(out["tp"] / (out["tp"] + out["fp"]))
    if out["precision"] and out["recall"]:
        p, r = out["precision"], out["recall"]
        assert out["f1"] == pytest.approx(2 * p * r / (p + r))


@pytest.mark.parametrize("seed", SEEDS)
def test_seasonal_split_partitions_usable_pixels(seed):
    g = rng(seed)
    inc = g.random((30, 30)) < 0.4
    summer, spring = reflectance(g, (30, 30)), reflectance(g, (30, 30))
    valid = g.random((30, 30)) > 0.1
    out = cs.seasonal_split(inc, summer, spring, valid, 0.15)
    assert (
        out["stable_within_year"] + out["strongly_seasonal"]
        == out["with_valid_second_date"]
    )
    assert out["with_valid_second_date"] <= out["increase_pixels"] == int(inc.sum())


def test_resolution_table_matches_geometry():
    for area in (0.5, 1.0, 5.2, 26.0):
        for row in cs.resolution_table(area):
            side = (area * 10_000) ** 0.5
            assert row["pixels_total"] == pytest.approx(
                (side / row["resolution_m"]) ** 2
            )
            assert 0 <= row["pixels_interior"] <= row["pixels_total"]
