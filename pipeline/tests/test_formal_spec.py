"""Tie the real Python change-detection rules to the Lean specification in ``formal/``.

The Lean files prove properties of small mathematical models of the rules.
These tests check, on many seeded random inputs (synthetic demonstration
data, not evidence), that the functions the pipeline actually runs behave
like those models:

* ``case_study.resolve_threshold``  <->  ``Formal/Threshold.lean`` (``selectThreshold``)
* ``case_study.threshold_table`` and ``robustness.change_mask``  <->  ``Formal/Flags.lean``
* ``case_study.keep_patches_ge`` and ``patch_statistics``  <->  ``Formal/Patches.lean``
* ``robustness.confusion`` and ``reference_cos.binary_agreement``  <->  ``Formal/Confusion.lean``
* ``case_study.normalized_difference``  <->  ``Formal/Indices.lean``

The last two tests check the Lean project itself: no unfinished proofs in the
sources, and ``lake build`` passes (skipped when Lean is not installed).
"""

from __future__ import annotations

import math
from pathlib import Path
import random
import re
import shutil
import subprocess

import numpy as np
import pytest

from pipeline.src import case_study as cs
from pipeline.src import reference_cos as rc
from pipeline.src import robustness as rb

REPO = Path(__file__).resolve().parents[2]
FORMAL = REPO / "formal"
SEEDS = range(40)


# ---------------------------------------------------------------------------
# Python copies of the Lean definitions (kept deliberately literal)
# ---------------------------------------------------------------------------


def select_threshold(grid, q):
    """Lean ``selectThreshold``: smallest grid value >= q, else None."""
    out = None
    for g in reversed(list(grid)):
        if out is None:
            out = g if q <= g else None
        else:
            out = min(g, out) if q <= g else out
    return out


def lean_ceil_min_px(needed_m2: int, pixel_m2: int) -> int:
    """Lean ``minPatchPixels``: max 1 (ceil(needed / pixel)) with whole numbers."""
    return max(1, (needed_m2 + pixel_m2 - 1) // pixel_m2)


def random_grid(r: random.Random) -> list[float]:
    """Positive grid in 0.005 steps, unsorted, sometimes with duplicates."""
    n = r.randint(1, 12)
    grid = [round(r.randint(1, 80) * 0.005, 6) for _ in range(n)]
    if r.random() < 0.3:
        grid.append(r.choice(grid))
    r.shuffle(grid)
    return grid


def random_control(g: np.random.Generator, scale: float) -> np.ndarray:
    c = g.normal(0.0, scale, size=(30, 30)).astype("float32")
    c[g.random(c.shape) < 0.05] = np.nan
    return c


def p99(control: np.ndarray) -> float:
    return float(np.percentile(np.abs(control[np.isfinite(control)]), 99))


# ---------------------------------------------------------------------------
# Threshold rule
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_resolve_threshold_matches_lean_select(seed):
    r = random.Random(7000 + seed)
    g = np.random.default_rng(7000 + seed)
    for _ in range(25):
        grid = random_grid(r)
        control = random_control(g, r.uniform(0.01, 0.15))
        q = p99(control)
        expected = select_threshold(grid, q)
        if expected is None:
            with pytest.raises(ValueError):
                cs.resolve_threshold("control_p99", grid, control)
            assert all(t < q for t in grid)  # select_none_iff
            continue
        t, _ = cs.resolve_threshold("control_p99", grid, control)
        assert t == expected
        # select_mem, select_ge, select_le
        assert t in grid and t >= q
        assert all(t <= x for x in grid if x >= q)
        # select_perm: the order of the config grid does not matter
        shuffled = grid[:]
        r.shuffle(shuffled)
        assert cs.resolve_threshold("control_p99", shuffled, control)[0] == t


@pytest.mark.parametrize("seed", SEEDS)
def test_resolve_threshold_is_monotone(seed):
    """select_mono: a noisier control pair never gives a smaller threshold."""
    r = random.Random(8000 + seed)
    g = np.random.default_rng(8000 + seed)
    grid = sorted(set(random_grid(r) + [0.4, 0.5]))
    control = random_control(g, r.uniform(0.01, 0.08))
    results = []
    for factor in (1.0, 1.1, 1.5, 2.0, 3.0):
        try:
            results.append(
                cs.resolve_threshold("control_p99", grid, control * factor)[0]
            )
        except ValueError:
            break
    assert results == sorted(results)


def test_resolve_threshold_fixed_rule_passes_through():
    assert cs.resolve_threshold(0.2, [0.1, 0.2], np.zeros(3))[0] == 0.2


# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------


def integer_deltas(g: np.random.Generator, shape=(25, 25)) -> np.ndarray:
    """Differences on a 0.01 grid so that ties with the threshold actually occur."""
    d = (g.integers(-40, 41, size=shape) / 100).astype("float64")
    d[g.random(shape) < 0.05] = np.nan
    return d


@pytest.mark.parametrize("seed", SEEDS)
def test_threshold_table_counts_follow_lean_flags(seed):
    g = np.random.default_rng(9000 + seed)
    main, control = integer_deltas(g), integer_deltas(g)
    thresholds = sorted({round(float(t), 2) for t in g.integers(1, 40, 8) / 100})
    rows = cs.threshold_table(main, control, thresholds)
    m = main[np.isfinite(main)]
    prev = None
    for row in rows:
        t = row["threshold"]
        # count_inc_add_dec: increase + decrease = |d| > t (t > 0)
        assert row["main_increase_pixels"] + row["main_decrease_pixels"] == int(
            (np.abs(m) > t).sum()
        )
        # strict comparison: a difference exactly equal to t is not flagged
        assert row["main_increase_pixels"] == int((m > t).sum())
        assert row["main_decrease_pixels"] == int((m < -t).sum())
        # antitone in t (thresholds are sorted ascending)
        if prev is not None:
            for k in (
                "main_increase_pixels",
                "main_decrease_pixels",
                "control_flagged_pixels",
            ):
                assert row[k] <= prev[k]
        prev = row


@pytest.mark.parametrize("seed", SEEDS)
def test_change_mask_flags_disjoint_and_nan_never_flagged(seed):
    g = np.random.default_rng(9500 + seed)
    delta = integer_deltas(g)
    t = float(g.integers(1, 30)) / 100
    inc = rb.change_mask(delta, t, 1, direction="increase")
    dec = rb.change_mask(delta, t, 1, direction="decrease")
    assert not np.any(inc & dec)  # inc_dec_disjoint
    assert not np.any((inc | dec) & np.isnan(delta))  # missing_never_flagged
    d0 = np.nan_to_num(delta, nan=0.0)
    np.testing.assert_array_equal(inc, d0 > t)  # min 1 pixel keeps every patch
    np.testing.assert_array_equal(dec, d0 < -t)
    # decrease_is_negated_increase
    np.testing.assert_array_equal(
        dec, rb.change_mask(-delta, t, 1, direction="increase")
    )


@pytest.mark.parametrize("seed", SEEDS)
def test_control_flags_at_selected_threshold_le_p99_level(seed):
    """control_flags_at_selected_le: the chosen t flags no more control pixels than q."""
    r = random.Random(9900 + seed)
    g = np.random.default_rng(9900 + seed)
    grid = sorted(set(random_grid(r) + [0.5]))
    control = random_control(g, r.uniform(0.01, 0.1))
    q = p99(control)
    t, _ = cs.resolve_threshold("control_p99", grid, control)
    c = np.abs(control[np.isfinite(control)])
    assert int((c > t).sum()) <= int((c > q).sum())


# ---------------------------------------------------------------------------
# Patch filter
# ---------------------------------------------------------------------------


def component_sizes(mask: np.ndarray) -> list[int]:
    labels, n = cs.label_patches(mask)
    return [] if n == 0 else np.bincount(labels.ravel())[1:].tolist()


@pytest.mark.parametrize("seed", SEEDS)
def test_keep_patches_ge_matches_lean_size_filter(seed):
    g = np.random.default_rng(11000 + seed)
    mask = g.random((30, 30)) < g.uniform(0.05, 0.6)
    sizes = component_sizes(mask)
    prev_kept = None
    for m in (1, 2, 3, 5, 8, 13, 40):
        kept = cs.keep_patches_ge(mask, m)
        lean_kept = [s for s in sizes if s >= m]
        assert int(kept.sum()) == sum(lean_kept)  # pixels (kept m sizes)
        assert not np.any(kept & ~mask)  # kept_sublist
        assert int(kept.sum()) <= int(mask.sum())  # kept_pixels_le
        np.testing.assert_array_equal(cs.keep_patches_ge(kept, m), kept)  # kept_idem
        assert all(s >= m for s in component_sizes(kept))  # kept_all_ge
        assert sorted(component_sizes(kept)) == sorted(lean_kept)
        if prev_kept is not None:
            assert int(kept.sum()) <= prev_kept  # kept_antitone
        prev_kept = int(kept.sum())
    np.testing.assert_array_equal(cs.keep_patches_ge(mask, 1), mask)  # kept_one


@pytest.mark.parametrize("seed", SEEDS)
def test_min_patch_pixels_covers_requested_area(seed):
    """minPatchPixels_pos and minPatchPixels_covers_area, against patch_statistics."""
    r = random.Random(12000 + seed)
    mask = np.ones((3, 3), dtype=bool)
    for _ in range(20):
        pixel_m2 = r.choice([100, 400, 900, 3600])
        needed_m2 = r.randint(0, 50_000)
        stats = cs.patch_statistics(mask, float(pixel_m2), needed_m2 / 10_000)
        min_px = stats["min_patch_pixels"]
        assert min_px >= 1
        assert min_px * pixel_m2 >= needed_m2
        assert min_px == lean_ceil_min_px(needed_m2, pixel_m2)


# ---------------------------------------------------------------------------
# Confusion counts
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_confusion_counts_follow_lean_spec(seed):
    g = np.random.default_rng(13000 + seed)
    shape = (20, 20)
    pred = g.random(shape) < g.uniform(0, 1)
    ref = g.random(shape) < g.uniform(0, 1)
    dom = g.random(shape) < g.uniform(0.2, 1)
    c = rb.confusion(pred, ref, dom)
    tp, fp, fn, tn = c["tp"], c["fp"], c["fn"], c["tn"]
    assert tp + fp + fn + tn == int(dom.sum())  # confusion_total
    assert tp + fp == int((pred & dom).sum())  # tp_add_fp
    assert tp + fn == int((ref & dom).sum())  # tp_add_fn
    for k in ("precision", "recall", "f1"):
        assert c[k] is None or 0.0 <= c[k] <= 1.0
    if tp + fp == 0:
        assert c["precision"] is None
    if c["f1"] is not None:
        assert math.isclose(c["f1"], 2 * tp / (2 * tp + fp + fn), rel_tol=1e-9)
    # swap_pred_ref
    s = rb.confusion(ref, pred, dom)
    assert (s["tp"], s["fp"], s["fn"], s["tn"]) == (tp, fn, fp, tn)
    # outside_domain_ignored: changing pixels outside the domain changes nothing
    c2 = rb.confusion(pred ^ ~dom, ref ^ ~dom, dom)
    assert (c2["tp"], c2["fp"], c2["fn"], c2["tn"]) == (tp, fp, fn, tn)
    # binary_agreement is the same count with every pixel in the domain
    b = rc.binary_agreement(pred.ravel(), ref.ravel())
    assert b["tp"] + b["fp"] + b["fn"] + b["tn"] == pred.size


# ---------------------------------------------------------------------------
# Indices
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_normalized_difference_clip_is_noop_for_nonnegative_inputs(seed):
    """ndvi_clip_noop / bsi_clip_noop on digital-number-like non-negative integers."""
    g = np.random.default_rng(14000 + seed)
    bands = {
        k: g.integers(0, 10_000, (20, 20)).astype("float32")
        for k in ("blue", "red", "nir", "swir16")
    }
    for index, (a, b) in {
        "ndvi": (bands["nir"], bands["red"]),
        "bsi": (bands["swir16"] + bands["red"], bands["nir"] + bands["blue"]),
    }.items():
        out = cs.compute_index(index, bands)
        ok = (a + b) > 0
        raw = (a[ok].astype("float64") - b[ok]) / (a[ok].astype("float64") + b[ok])
        assert np.all(raw >= -1.0) and np.all(raw <= 1.0)
        np.testing.assert_allclose(out[ok], raw, atol=1e-6)


# ---------------------------------------------------------------------------
# The Lean project itself
# ---------------------------------------------------------------------------


def _strip_lean_comments(text: str) -> str:
    text = re.sub(r"/-.*?-/", " ", text, flags=re.S)
    return re.sub(r"--[^\n]*", " ", text)


def test_formal_sources_have_no_unfinished_proofs():
    files = sorted(FORMAL.rglob("*.lean"))
    files = [f for f in files if ".lake" not in f.parts]
    assert len(files) >= 7, "formal/ Lean sources are missing"
    for f in files:
        raw = f.read_text(encoding="utf-8")
        assert not re.search(r"\b(sorry|admit)\b", raw), f"{f}: unfinished proof"
        code = _strip_lean_comments(raw)
        assert not re.search(
            r"^\s*(axiom|unsafe|@\[extern)", code, flags=re.M
        ), f"{f}: new axiom or unchecked code"


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean (lake) not on PATH")
def test_lake_build_passes():
    proc = subprocess.run(  # nosec B603 B607
        ["lake", "build"],
        cwd=FORMAL,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, out[-4000:]
    assert "Build completed successfully" in out
    if "Built Formal.Audit" in out:  # only printed when the audit actually re-ran
        assert "axiom audit passed" in out
