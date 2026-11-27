"""Pure helpers for the method sensitivity checks of the Sentinel-2 case study.

These functions are used by ``pipeline/run_sensitivity.py``. They are unit
tested offline with small synthetic arrays. Every number the runner derives
from real scenes is an ``observation_derived_result``; the runner never writes
to the published ``docs/case-study/data`` folder.
"""

from __future__ import annotations

from datetime import date
import math
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from pipeline.src import case_study as cs
from pipeline.src import robustness as rb


def scale_bbox(bbox: Sequence[float], factor: float) -> tuple[float, ...]:
    """Scale a WGS84 box about its centre; ``factor`` multiplies each side length."""
    if factor <= 0:
        raise ValueError("factor must be > 0")
    lon0, lat0, lon1, lat1 = (float(v) for v in bbox)
    cx, cy = (lon0 + lon1) / 2, (lat0 + lat1) / 2
    hx, hy = (lon1 - lon0) / 2 * factor, (lat1 - lat0) / 2 * factor
    out = (round(cx - hx, 6), round(cy - hy, 6), round(cx + hx, 6), round(cy + hy, 6))
    cs.validate_bbox(out)
    return out


def _day(row: Mapping[str, Any]) -> date:
    return date.fromisoformat(str(row["datetime"])[:10])


def pick_scene(
    rows: Iterable[Mapping[str, Any]],
    target: date,
    tile: str,
    orbit: str,
    max_cloud: float = 1.0,
    baseline_prefix: str = "05.",
    exclude: Iterable[str] = (),
) -> dict[str, Any]:
    """Closest scene to ``target`` that meets the case-study date rule.

    Rule: same MGRS tile and relative orbit, scene cloud < ``max_cloud`` %,
    processing baseline starting with ``baseline_prefix``. Ties in distance go
    to the earlier date. Raises ``LookupError`` if nothing qualifies.
    """
    skip = set(exclude)
    ok = [
        dict(r)
        for r in rows
        if r["mgrs_tile"] == tile
        and str(r["relative_orbit"]) == str(orbit)
        and r["eo_cloud_cover"] is not None
        and float(r["eo_cloud_cover"]) < max_cloud
        and str(r["processing_baseline"]).startswith(baseline_prefix)
        and r["id"] not in skip
    ]
    if not ok:
        raise LookupError(f"no scene for {tile} R{orbit} near {target}")
    ok.sort(key=lambda r: (abs((_day(r) - target).days), _day(r)))
    best = ok[0]
    best["days_from_target"] = (_day(best) - target).days
    return best


def continuous_p99(control: np.ndarray) -> float:
    """99th percentile of |control delta| over valid pixels (no grid snapping)."""
    c = np.abs(control[np.isfinite(control)])
    if c.size == 0:
        raise ValueError("control pair has no valid pixels")
    return float(np.percentile(c, 99))


def percent_change(new: float | None, ref: float | None) -> float | None:
    """100 * (new - ref) / ref, or None if undefined."""
    if new is None or ref is None or ref == 0:
        return None
    if not (math.isfinite(new) and math.isfinite(ref)):
        return None
    return 100.0 * (float(new) - float(ref)) / float(ref)


def change_summary(
    delta: np.ndarray,
    control: np.ndarray,
    joint: np.ndarray,
    water_either: np.ndarray,
    threshold: float,
    min_patch_ha: float,
    pixel_area_m2: float,
    exclude_water: bool,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    """Change numbers exactly as ``run_case_study.py run`` computes them.

    Returns (summary, increase mask in patches, decrease mask in patches).
    """
    min_px = max(1, int(math.ceil(min_patch_ha * 10_000 / pixel_area_m2)))
    exclude = water_either if exclude_water else None
    inc = rb.change_mask(delta, threshold, min_px, exclude, "increase")
    dec = rb.change_mask(delta, threshold, min_px, exclude, "decrease")
    c = np.abs(control[np.isfinite(control)])
    n_joint = int(joint.sum())
    inc_raw = np.nan_to_num(delta, nan=0.0) > threshold
    dec_raw = np.nan_to_num(delta, nan=0.0) < -threshold
    if exclude is not None:
        inc_raw &= ~exclude
        dec_raw &= ~exclude
    ha = pixel_area_m2 / 10_000
    out = {
        "threshold": float(threshold),
        "min_patch_ha": float(min_patch_ha),
        "min_patch_pixels": min_px,
        "water_excluded": bool(exclude_water),
        "joint_valid_pixels": n_joint,
        "increase_pixels_raw": int(inc_raw.sum()),
        "decrease_pixels_raw": int(dec_raw.sum()),
        "increase_area_ha": float(inc.sum() * ha),
        "decrease_area_ha": float(dec.sum() * ha),
        "increase_share_of_valid": float(inc.sum() / n_joint) if n_joint else None,
        "decrease_share_of_valid": float(dec.sum() / n_joint) if n_joint else None,
        "increase_patches_ge_min": int(cs.label_patches(inc)[1]),
        "decrease_patches_ge_min": int(cs.label_patches(dec)[1]),
        "control_flagged_share_at_threshold": (
            float((c > threshold).mean()) if c.size else None
        ),
    }
    return out, inc, dec


def class_crosstab(
    classes: np.ndarray,
    groups: Mapping[str, np.ndarray],
    labels: Mapping[int, str],
    domain: np.ndarray,
    pixel_area_m2: float,
) -> list[dict[str, Any]]:
    """Pixels of each boolean group per class value (e.g. COS code) inside ``domain``.

    ``classes`` holds integer class ids (0 = none); ``labels`` maps id -> name.
    One row per class id that holds at least one group pixel, sorted by the
    total, plus the share of each group that falls in the class.
    """
    ha = pixel_area_m2 / 10_000
    totals = {g: int((m & domain).sum()) for g, m in groups.items()}
    rows = []
    ids = np.unique(classes[domain])
    for cid in ids:
        sel = domain & (classes == cid)
        row: dict[str, Any] = {
            "class_id": int(cid),
            "class": labels.get(int(cid), "none"),
        }
        any_px = 0
        for g, m in groups.items():
            n = int((m & sel).sum())
            any_px += n
            row[f"{g}_pixels"] = n
            row[f"{g}_area_ha"] = n * ha
            row[f"{g}_share"] = n / totals[g] if totals[g] else None
        if any_px:
            rows.append(row)
    rows.sort(key=lambda r: -sum(r[f"{g}_pixels"] for g in groups))
    return rows
