"""Robustness checks for the Sentinel-2 case study against the COS reference.

Three checks, all computed from public inputs:

1. Threshold curve: pixel-level precision / recall / F1 of the change flags
   against the DGT COS reference for every threshold of a grid, next to the
   share of control-pair pixels that the same threshold would flag.
2. Spatial bootstrap: percentile confidence intervals for precision and
   recall that resample square blocks of pixels (or whole COS polygons) with
   replacement, so that neighbouring, correlated pixels move together.
3. Second date pair: the same method on another pair of summer scenes, to see
   how much the result depends on the choice of dates.

The pure array functions at the top are unit-tested offline with synthetic
arrays. The functions after them read scenes and COS polygons over the network.

Data status: every number produced here is an ``observation_derived_result``.
Agreement with COS is not ground-truth accuracy (COS has its own errors,
generalisation and reference dates).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

from pipeline.src import case_study as cs
from pipeline.src import reference_cos as rc

DEFAULT_SEED = 20261126
DEFAULT_ITERATIONS = 1000
DEFAULT_BLOCK_M = (500.0, 1000.0)


# ---------------------------------------------------------------------------
# Pure array functions (unit-tested without network access)
# ---------------------------------------------------------------------------


def grid_values(start: float, stop: float, step: float) -> list[float]:
    """Inclusive arithmetic grid, rounded to avoid float drift (0.05, 0.075, ...)."""
    if step <= 0 or stop < start:
        raise ValueError("need step > 0 and stop >= start")
    n = int(round((stop - start) / step)) + 1
    return [round(start + i * step, 6) for i in range(n)]


def union_grid(*grids: Sequence[float]) -> list[float]:
    return sorted({round(float(t), 6) for g in grids for t in g})


def change_mask(
    delta: NDArray[Any],
    threshold: float,
    min_pixels: int,
    exclude: NDArray[Any] | None = None,
    direction: str = "increase",
) -> NDArray[Any]:
    """Change flags exactly as ``run_case_study.py run`` builds them.

    delta > t (increase) or delta < -t (decrease), NaN never flagged, optional
    exclusion mask (open water), then only 8-connected patches >= min_pixels.
    """
    d = np.nan_to_num(delta, nan=0.0)
    if direction == "increase":
        m = d > threshold
    elif direction == "decrease":
        m = d < -threshold
    else:
        raise ValueError("direction must be 'increase' or 'decrease'")
    if exclude is not None:
        m &= ~exclude
    return cs.keep_patches_ge(m, min_pixels)


def scores(
    tp: NDArray[Any] | int, fp: NDArray[Any] | int, fn: NDArray[Any] | int
) -> dict[str, NDArray[Any]]:
    """Precision, recall, F1 (NaN where undefined). Works on scalars or arrays."""
    tp_a = np.asarray(tp, dtype="float64")
    fp_a = np.asarray(fp, dtype="float64")
    fn_a = np.asarray(fn, dtype="float64")
    with np.errstate(divide="ignore", invalid="ignore"):
        precision = np.where(tp_a + fp_a > 0, tp_a / (tp_a + fp_a), np.nan)
        recall = np.where(tp_a + fn_a > 0, tp_a / (tp_a + fn_a), np.nan)
        f1 = np.where(
            (precision + recall) > 0,
            2 * precision * recall / (precision + recall),
            np.nan,
        )
    return {"precision": precision, "recall": recall, "f1": f1}


def _num(x: Any) -> float | None:
    v = float(x)
    return v if np.isfinite(v) else None


def confusion(
    pred: NDArray[Any], ref: NDArray[Any], domain: NDArray[Any]
) -> dict[str, Any]:
    """Pixel confusion counts inside ``domain`` plus precision / recall / F1."""
    p = pred & domain
    r = ref & domain
    tp = int((p & r).sum())
    fp = int((p & ~r).sum())
    fn = int((~p & r & domain).sum())
    tn = int((domain & ~p & ~r).sum())
    s = scores(tp, fp, fn)
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": _num(s["precision"]),
        "recall": _num(s["recall"]),
        "f1": _num(s["f1"]),
    }


def threshold_curve(
    delta: NDArray[Any],
    control: NDArray[Any],
    reference: NDArray[Any],
    domain: NDArray[Any],
    thresholds: Sequence[float],
    min_pixels: int,
    pixel_area_m2: float,
    exclude: NDArray[Any] | None = None,
    direction: str = "increase",
) -> list[dict[str, Any]]:
    """One row per threshold: flagged area, agreement with ``reference`` and control share.

    ``control_flagged_share`` uses the same definition as
    ``case_study.threshold_table``: share of valid control-pair pixels with
    |delta| > t, before the patch filter.
    """
    c = np.abs(control[np.isfinite(control)])
    rows = []
    for t in thresholds:
        flags = change_mask(delta, t, min_pixels, exclude, direction)
        row: dict[str, Any] = {
            "threshold": float(t),
            "flagged_pixels": int(flags.sum()),
            "flagged_area_ha": float(flags.sum() * pixel_area_m2 / 10_000),
        }
        row.update(confusion(flags, reference, domain))
        row["control_flagged_share"] = float((c > t).mean()) if c.size else None
        rows.append(row)
    return rows


def block_index(shape: tuple[int, ...], block_px: int) -> NDArray[Any]:
    """Integer id of the square block (block_px x block_px) each pixel falls in."""
    if block_px < 1:
        raise ValueError("block_px must be >= 1")
    rows, cols = shape
    n_cols = -(-cols // block_px)
    r = np.arange(rows)[:, None] // block_px
    c = np.arange(cols)[None, :] // block_px
    return np.asarray(r * n_cols + c, dtype="int64")


def group_counts(
    pred: NDArray[Any], ref: NDArray[Any], domain: NDArray[Any], groups: NDArray[Any]
) -> NDArray[Any]:
    """(tp, fp, fn) per group for groups that contain at least one domain pixel."""
    g = groups[domain]
    p = pred[domain]
    r = ref[domain]
    n = int(groups.max()) + 1
    tp = np.bincount(g[p & r], minlength=n)
    fp = np.bincount(g[p & ~r], minlength=n)
    fn = np.bincount(g[~p & r], minlength=n)
    present = np.bincount(g, minlength=n) > 0
    return np.stack([tp, fp, fn], axis=1)[present]


def percentile_ci(values: NDArray[Any], level: float = 0.95) -> tuple[float, float]:
    lo = (1 - level) / 2 * 100
    v = values[np.isfinite(values)]
    if v.size == 0:
        return (float("nan"), float("nan"))
    a, b = np.percentile(v, [lo, 100 - lo])
    return float(a), float(b)


def bootstrap_counts(
    counts: NDArray[Any], iterations: int, seed: int, level: float = 0.95
) -> dict[str, Any]:
    """Resample rows of ``counts`` (tp, fp, fn per unit) with replacement.

    Each iteration draws as many units as there are, sums their counts and
    recomputes precision / recall / F1. Returns the point estimate (all units
    once), percentile CIs, the bootstrap standard deviation and the draws.
    """
    if counts.ndim != 2 or counts.shape[1] != 3:
        raise ValueError("counts must have shape (n_units, 3)")
    n = counts.shape[0]
    if n == 0:
        raise ValueError("no units to resample")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(iterations, n))
    sums = counts[idx].sum(axis=1)
    boot = scores(sums[:, 0], sums[:, 1], sums[:, 2])
    tot = counts.sum(axis=0)
    point = scores(tot[0], tot[1], tot[2])
    out: dict[str, Any] = {
        "units": int(n),
        "iterations": int(iterations),
        "seed": int(seed),
        "ci_level": level,
        "ci_method": "percentile",
        "totals": {"tp": int(tot[0]), "fp": int(tot[1]), "fn": int(tot[2])},
    }
    draws: dict[str, NDArray[Any]] = {}
    for k in ("precision", "recall", "f1"):
        lo, hi = percentile_ci(boot[k], level)
        out[k] = {
            "estimate": _num(point[k]),
            "ci_low": _num(lo),
            "ci_high": _num(hi),
            "bootstrap_sd": _num(np.nanstd(boot[k], ddof=1)),
            "undefined_iterations": int((~np.isfinite(boot[k])).sum()),
        }
        draws[k] = boot[k]
    out["_draws"] = draws
    return out


def block_bootstrap(
    pred: NDArray[Any],
    ref: NDArray[Any],
    domain: NDArray[Any],
    block_px: int,
    iterations: int = DEFAULT_ITERATIONS,
    seed: int = DEFAULT_SEED,
    level: float = 0.95,
) -> dict[str, Any]:
    """Spatial block bootstrap of pixel-level precision / recall / F1."""
    counts = group_counts(pred, ref, domain, block_index(pred.shape, block_px))
    out = bootstrap_counts(counts, iterations, seed, level)
    out["block_px"] = int(block_px)
    return out


def polygon_unit_labels(
    units: NDArray[Any],
    pred: NDArray[Any],
    ref: NDArray[Any],
    valid: NDArray[Any],
    min_pixels: int,
    share: float = 0.5,
) -> tuple[NDArray[Any], NDArray[Any]]:
    """Per-unit (detected, reference-positive) labels, same rule as
    ``reference_cos.polygon_agreement``."""
    inside = valid & (units > 0)
    n_ids = int(units.max()) + 1
    count = np.bincount(units[inside], minlength=n_ids)
    pred_c = np.bincount(units[inside & pred], minlength=n_ids)
    ref_c = np.bincount(units[inside & ref], minlength=n_ids)
    keep = count >= min_pixels
    keep[0] = False
    return (pred_c[keep] / count[keep]) >= share, (ref_c[keep] / count[keep]) >= share


def unit_bootstrap(
    unit_pred: NDArray[Any],
    unit_ref: NDArray[Any],
    iterations: int = DEFAULT_ITERATIONS,
    seed: int = DEFAULT_SEED,
    level: float = 0.95,
) -> dict[str, Any]:
    """Bootstrap of polygon-level scores, resampling whole polygons."""
    p = np.asarray(unit_pred, dtype=bool)
    r = np.asarray(unit_ref, dtype=bool)
    counts = np.stack([p & r, p & ~r, ~p & r], axis=1).astype("int64")
    return bootstrap_counts(counts, iterations, seed, level)


def mask_overlap(a: NDArray[Any], b: NDArray[Any]) -> dict[str, Any]:
    """Overlap of two boolean masks (e.g. increase flags of two date pairs)."""
    na, nb, both = int(a.sum()), int(b.sum()), int((a & b).sum())
    union = int((a | b).sum())
    return {
        "pixels_a": na,
        "pixels_b": nb,
        "pixels_both": both,
        "jaccard": both / union if union else None,
        "share_of_a_also_in_b": both / na if na else None,
        "share_of_b_also_in_a": both / nb if nb else None,
    }


def strip_draws(obj: Any) -> Any:
    """Remove the private ``_draws`` arrays before writing JSON."""
    if isinstance(obj, dict):
        return {k: strip_draws(v) for k, v in obj.items() if k != "_draws"}
    if isinstance(obj, list):
        return [strip_draws(v) for v in obj]
    return obj


# ---------------------------------------------------------------------------
# Scenes and reference (network)
# ---------------------------------------------------------------------------


@dataclass
class PairResult:
    """Main-pair difference, control-pair difference and the derived threshold."""

    before_id: str
    after_id: str
    control_before_id: str
    control_after_id: str
    delta: NDArray[Any]
    control: NDArray[Any]
    joint: NDArray[Any]
    water_either: NDArray[Any]
    threshold: float
    threshold_rule: str
    threshold_grid: list[float]
    centering: str
    raw_median_delta: float
    dates: dict[str, str] = field(default_factory=dict)


class ObservationCache:
    """Load each STAC item once (items are shared between main and control pairs)."""

    def __init__(self, cfg: cs.CaseStudyConfig, grid: cs.Grid | None = None) -> None:
        self.cfg = cfg
        self.grid = grid
        self.meta: dict[str, dict[str, Any]] = {}
        self.obs: dict[str, cs.Observation] = {}
        self.retrieved_at: str | None = None

    def add_items(self, ids: Sequence[str]) -> None:
        missing = [i for i in dict.fromkeys(ids) if i not in self.meta]
        if not missing:
            return
        items = cs.fetch_items(missing)
        self.retrieved_at = cs.utc_now()
        for iid, it in items.items():
            m = cs.item_metadata(it)
            if m["mgrs_tile"] != _tile_of(self.meta) and self.meta:
                raise ValueError(f"{iid} is on another MGRS tile; grids differ")
            self.meta[iid] = m

    def get(self, iid: str) -> cs.Observation:
        if iid not in self.obs:
            if self.grid is None:
                raise ValueError("set the grid before reading observations")
            self.add_items([iid])
            print(f"  reading {iid}")
            self.obs[iid] = cs.load_observation(
                self.meta[iid], self.grid, self.cfg.index, self.cfg.valid_scl
            )
        return self.obs[iid]


def _tile_of(meta: Mapping[str, Mapping[str, Any]]) -> str | None:
    for m in meta.values():
        return str(m["mgrs_tile"])
    return None


def compute_pair(
    cache: ObservationCache,
    before_id: str,
    after_id: str,
    control_before_id: str,
    control_after_id: str,
    threshold_grid: Sequence[float],
    fallback_grid: Sequence[float] | None = None,
) -> PairResult:
    """Difference and control threshold, mirroring ``run_case_study.py run``."""
    cfg = cache.cfg
    before, after = cache.get(before_id), cache.get(after_id)
    cb, ca = cache.get(control_before_id), cache.get(control_after_id)
    delta, joint = cs.difference(before.index, after.index, before.valid, after.valid)
    control, _ = cs.difference(cb.index, ca.index, cb.valid, ca.valid)
    raw_median = float(np.nanmedian(delta))
    centering = cfg.extra.get("center_delta")
    if centering == "median":
        delta = delta - np.float32(raw_median)
        control = control - np.float32(np.nanmedian(control))
    elif centering is not None:
        raise ValueError(f"unknown center_delta {centering!r}")
    grid_used = list(threshold_grid)
    try:
        t, rule = cs.resolve_threshold(cfg.primary_threshold, grid_used, control)
    except ValueError as exc:
        if not fallback_grid:
            raise
        grid_used = list(fallback_grid)
        t, rule = cs.resolve_threshold(cfg.primary_threshold, grid_used, control)
        rule += f" (config grid failed: {exc}; used the robustness grid)"
    water = (before.scl == 6) | (after.scl == 6)
    return PairResult(
        before_id=before_id,
        after_id=after_id,
        control_before_id=control_before_id,
        control_after_id=control_after_id,
        delta=delta,
        control=control,
        joint=joint,
        water_either=water,
        threshold=float(t),
        threshold_rule=rule,
        threshold_grid=grid_used,
        centering=centering or "none",
        raw_median_delta=raw_median,
        dates={
            "before": str(before.meta["datetime"]),
            "after": str(after.meta["datetime"]),
            "control_before": str(cb.meta["datetime"]),
            "control_after": str(ca.meta["datetime"]),
        },
    )


@dataclass
class CosReference:
    perm18: NDArray[Any]
    perm25: NDArray[Any]
    covered: NDArray[Any]
    water25: NDArray[Any]
    mining25: NDArray[Any]
    units25: NDArray[Any]
    retrieved_at: str
    polygons_2018: int
    polygons_2025: int


def load_cos(bbox: Sequence[float], grid: cs.Grid) -> CosReference:
    """Fetch COS 2018v4 and 2025v1 for the AOI and burn them onto the grid."""
    retrieved = cs.utc_now()
    layers = {}
    for year, (coll, prefix) in rc.COLLECTIONS.items():
        feats = rc.fetch_features(coll, bbox)
        raster, codes = rc.rasterize_classes(feats, prefix, grid)
        layers[year] = (feats, prefix, raster, codes)
    f18, _, r18, c18 = layers["2018"]
    f25, p25, r25, c25 = layers["2025"]

    def is_perm(c: str) -> bool:
        return c.startswith(rc.PERMANENT_CROP_PREFIX)

    def is_mine(c: str) -> bool:
        return c.startswith(rc.MINING_PREFIXES)

    return CosReference(
        perm18=rc.code_mask(r18, c18, is_perm),
        perm25=rc.code_mask(r25, c25, is_perm),
        covered=(r18 > 0) & (r25 > 0),
        water25=rc.code_mask(r25, c25, lambda c: c.startswith("9.")),
        mining25=rc.code_mask(r25, c25, is_mine),
        units25=rc.polygon_units(f25, p25, grid),
        retrieved_at=retrieved,
        polygons_2018=len(f18),
        polygons_2025=len(f25),
    )


def reference_definition(
    index: str, cos: CosReference, valid: NDArray[Any]
) -> tuple[NDArray[Any], NDArray[Any], dict[str, str]]:
    """(reference positives, evaluation domain, description) for a case index."""
    ev = valid & cos.covered
    if index == "ndvi":
        return (
            ~cos.perm18 & cos.perm25,
            ev & ~cos.perm18,
            {
                "flag": "NDVI increase in patches >= min_patch_ha",
                "reference_positive": "COS new permanent crop: not 2.2.x in COS2018v4, 2.2.x in COS2025v1",
                "domain": "pixels that are not permanent crop in COS2018v4, have a valid difference and are covered by both COS layers",
                "reading": "agreement of a change flag with a mapped land-use change",
            },
        )
    if index == "bsi":
        return (
            cos.mining25,
            ev,
            {
                "flag": "BSI increase (median-centred) in patches >= min_patch_ha",
                "reference_positive": "COS2025v1 mines and quarries (1.6.x); a land-use state, not a mapped change",
                "domain": "pixels with a valid difference covered by both COS layers",
                "reading": "how concentrated the bare-surface increase flags are inside the mapped mine area; not a detection accuracy",
            },
        )
    raise ValueError(f"no reference definition for index {index!r}")
