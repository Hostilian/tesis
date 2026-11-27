"""Method sensitivity checks for the Sentinel-2 case studies (private evidence runs).

Usage (from the repository root)::

    python pipeline/run_sensitivity.py b8 --case alqueva_olive --case neves_corvo_mine
    python pipeline/run_sensitivity.py b3 b4 b10 b11 b12 c1 b1 --case alqueva_olive
    python pipeline/run_sensitivity.py b5 b6 c8 --case alqueva_olive
    python pipeline/run_sensitivity.py b7 --case neves_corvo_mine

Checks (one per backlog item):

``b1``  threshold options: config grid vs fine grid vs continuous p99, main and second date pair
``b3``  other summers: 2018 -> 2019 / 2023 / 2024, mid-August scene closest to 21 August
``b4``  other after-dates in summer 2025 (July to September)
``b5``  index: NDVI vs EVI vs NDMI (Alqueva)
``b6``  open-water exclusion on / off (Alqueva)
``b7``  median-centring on / off (Neves-Corvo)
``b8``  minimum patch size 0.5 / 1 / 2 ha
``b10`` 2-pixel buffer around SCL cloud / shadow / cirrus classes (3, 8, 9, 10)
``b11`` SCL 20 m -> 10 m resampling: nearest vs bilinear
``b12`` study area side length -30 % / +30 % about the centre
``c1``  spatial block bootstrap with 0.5, 1, 2 and 5 km blocks
``c8``  within-year stability split of increase pixels vs COS 2025 classes (Alqueva)

Scenes are read live from Earth Search (anonymous, no keys) and COS polygons
live from the DGT OGC API, exactly as ``run_case_study.py``. This runner never
writes to ``docs/case-study/data`` or ``pipeline/case_studies``: each check
writes its JSON, and the temporary config copy of every variant, to
``out/sensitivity/<item>/`` (git-ignored). Raw band reads are cached as
``.npy`` under ``out/sensitivity/_cache`` so that variants sharing a scene
read it once.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass, field
from datetime import date, timedelta
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pipeline import run_case_study as rcs  # noqa: E402
from pipeline.src import case_study as cs  # noqa: E402
from pipeline.src import reference_cos as rc  # noqa: E402
from pipeline.src import robustness as rb  # noqa: E402
from pipeline.src import sensitivity as sv  # noqa: E402

CONFIG_DIR = REPO / "pipeline" / "case_studies"
PUBLIC_ROOT = REPO / "docs" / "case-study" / "data"
DEFAULT_OUT = REPO / "out" / "sensitivity"
INDEX_FINE_GRID = (0.01, 1.0, 0.01)  # for indices whose config grid does not exist (b5)


CODE_PATHS = (
    "pipeline/run_sensitivity.py",
    "pipeline/src/sensitivity.py",
    "pipeline/src/robustness.py",
    "pipeline/src/case_study.py",
    "pipeline/src/reference_cos.py",
    "pipeline/run_case_study.py",
    "pipeline/case_studies",
)


def git_state() -> dict[str, Any]:
    def run(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
            ).stdout.strip()  # nosec B603 B607
        except Exception:
            return "unknown"

    status = run("status", "--porcelain", "--", *CODE_PATHS)
    return {
        "commit": run("rev-parse", "HEAD"),
        "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
        "code_dirty": bool(status) if status != "unknown" else None,
        "code_paths_checked": list(CODE_PATHS),
    }


# ---------------------------------------------------------------------------
# Reading with a disk cache
# ---------------------------------------------------------------------------


def _grid_key(grid: cs.Grid) -> str:
    return f"{grid.crs}|{[round(v, 3) for v in grid.window_bounds]}|{grid.width}x{grid.height}"


class Loader:
    """STAC metadata + band reads, with raw DN arrays cached on disk."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.meta: dict[str, dict[str, Any]] = {}
        self.retrieved_at: str | None = None

    def add(self, ids: Sequence[str]) -> None:
        missing = [i for i in dict.fromkeys(ids) if i not in self.meta]
        if missing:
            items = cs.fetch_items(missing)
            self.retrieved_at = cs.utc_now()
            for iid, it in items.items():
                self.meta[iid] = cs.item_metadata(it)

    def reader(
        self, asset: Mapping[str, Any], grid: cs.Grid, resampling: str
    ) -> np.ndarray:
        key = hashlib.sha256(
            f"{asset['href']}|{_grid_key(grid)}|{resampling}".encode()
        ).hexdigest()[:32]
        path = self.cache_dir / f"{key}.npy"
        if path.exists():
            return np.load(path)
        arr = cs.read_band(asset, grid, resampling)
        np.save(path, arr)
        return arr

    def observation(
        self,
        iid: str,
        grid: cs.Grid,
        index: str,
        valid_scl: Sequence[int],
        scl_resampling: str = "nearest",
        cloud_buffer_px: int = 0,
    ) -> cs.Observation:
        self.add([iid])
        print(
            f"    reading {iid} ({index}, scl {scl_resampling}, buffer {cloud_buffer_px})"
        )
        return cs.load_observation(
            self.meta[iid],
            grid,
            index,
            valid_scl,
            scl_resampling=scl_resampling,
            cloud_buffer_px=cloud_buffer_px,
            reader=self.reader,
        )


# ---------------------------------------------------------------------------
# One variant = the main run with one thing changed
# ---------------------------------------------------------------------------


@dataclass
class Variant:
    name: str
    cfg_raw: dict[str, Any]
    options: dict[str, Any]
    grid: cs.Grid
    summary: dict[str, Any]
    delta: np.ndarray
    control: np.ndarray
    joint: np.ndarray
    water: np.ndarray
    inc: np.ndarray
    dec: np.ndarray
    obs: dict[str, cs.Observation] = field(default_factory=dict)


def run_variant(
    loader: Loader,
    cfg_raw: Mapping[str, Any],
    name: str,
    *,
    scl_resampling: str = "nearest",
    cloud_buffer_px: int = 0,
    threshold_grid: Sequence[float] | None = None,
    fallback_grid: Sequence[float] | None = None,
    keep_obs: bool = False,
) -> Variant:
    """Mirror ``run_case_study.py run`` (no figures, no public outputs)."""
    raw = copy.deepcopy(dict(cfg_raw))
    cfg = cs.CaseStudyConfig.from_mapping(raw, allow_sensitivity_index=True)
    print(f"  [{name}] {cfg.before_item} -> {cfg.after_item}")
    ids = [
        cfg.before_item,
        cfg.after_item,
        cfg.control_before_item,
        cfg.control_after_item,
    ]
    loader.add(ids)
    tiles = {loader.meta[i]["mgrs_tile"] for i in ids}
    if len(tiles) != 1:
        raise SystemExit(f"items span several MGRS tiles {tiles}")
    grid = cs.reference_grid(loader.meta[cfg.before_item], cfg.bbox)
    obs = {
        iid: loader.observation(
            iid, grid, cfg.index, cfg.valid_scl, scl_resampling, cloud_buffer_px
        )
        for iid in dict.fromkeys(ids)
    }
    before, after = obs[cfg.before_item], obs[cfg.after_item]
    cb, ca = obs[cfg.control_before_item], obs[cfg.control_after_item]
    delta, joint = cs.difference(before.index, after.index, before.valid, after.valid)
    control, control_joint = cs.difference(cb.index, ca.index, cb.valid, ca.valid)
    raw_median = float(np.nanmedian(delta))
    centering = cfg.extra.get("center_delta")
    if centering == "median":
        delta = delta - np.float32(raw_median)
        control = control - np.float32(np.nanmedian(control))
    elif centering is not None:
        raise SystemExit(f"unknown center_delta {centering!r}")

    grid_used = list(threshold_grid or cfg.thresholds)
    try:
        t, rule = cs.resolve_threshold(cfg.primary_threshold, grid_used, control)
    except ValueError as exc:
        if not fallback_grid:
            raise
        grid_used = list(fallback_grid)
        t, rule = cs.resolve_threshold(cfg.primary_threshold, grid_used, control)
        rule += f" (config grid failed: {exc}; used fallback grid)"
    water = (before.scl == 6) | (after.scl == 6)
    exclude_water = bool(cfg.extra.get("exclude_water_from_change", False))
    pix_area = grid.pixel_size**2
    change, inc, dec = sv.change_summary(
        delta, control, joint, water, t, cfg.min_patch_ha, pix_area, exclude_water
    )
    total = grid.width * grid.height
    summary: dict[str, Any] = {
        "data_status": "observation_derived_result",
        "index": cfg.index,
        "items": {
            "before": cfg.before_item,
            "after": cfg.after_item,
            "control_before": cfg.control_before_item,
            "control_after": cfg.control_after_item,
        },
        "dates": {
            "before": str(before.meta["datetime"])[:10],
            "after": str(after.meta["datetime"])[:10],
            "control_before": str(cb.meta["datetime"])[:10],
            "control_after": str(ca.meta["datetime"])[:10],
        },
        "platforms": {
            "before": before.meta["platform"],
            "after": after.meta["platform"],
        },
        "bbox": list(cfg.bbox),
        "grid": {"width": grid.width, "height": grid.height, "pixels": total},
        "area_km2": total * pix_area / 1e6,
        "joint_valid_fraction": float(joint.sum() / total),
        "control_joint_valid_pixels": int(control_joint.sum()),
        "status": (
            "ok"
            if joint.sum() / total >= cfg.min_joint_valid_fraction
            else "insufficient_valid_coverage"
        ),
        "delta_centering": centering or "none",
        "raw_median_delta_main": raw_median,
        "threshold_rule": rule,
        "threshold_grid": grid_used,
        "control_abs_delta_p99_continuous": sv.continuous_p99(control),
        "valid_pixels_per_item": {i: int(o.valid.sum()) for i, o in obs.items()},
        **change,
    }
    return Variant(
        name,
        raw,
        {"scl_resampling": scl_resampling, "cloud_buffer_px": cloud_buffer_px},
        grid,
        summary,
        delta,
        control,
        joint,
        water,
        inc,
        dec,
        obs if keep_obs else {},
    )


def published(case: str) -> dict[str, Any]:
    r = json.loads((PUBLIC_ROOT / case / "results.json").read_text(encoding="utf-8"))
    return {
        "run_id": r["run_id"],
        "threshold": r["threshold"]["value"],
        "increase_area_ha": r["change"]["increase_area_ha"],
        "decrease_area_ha": r["change"]["decrease_area_ha"],
        "increase_share_of_valid": r["change"]["increase_share_of_valid"],
        "decrease_share_of_valid": r["change"]["decrease_share_of_valid"],
        "control_flagged_share_at_threshold": r["change"][
            "control_flagged_share_at_threshold"
        ],
    }


def compare(summary: Mapping[str, Any], pub: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "increase_area_ha",
        "decrease_area_ha",
        "increase_share_of_valid",
        "decrease_share_of_valid",
    )
    return {
        f"{k}_pct_change": sv.percent_change(summary.get(k), pub.get(k)) for k in keys
    }


def base_config(case: str) -> dict[str, Any]:
    return json.loads((CONFIG_DIR / f"{case}.json").read_text(encoding="utf-8"))


def reproduces(v: Variant, pub: Mapping[str, Any]) -> bool:
    return bool(
        v.summary["threshold"] == pub["threshold"]
        and abs(v.summary["increase_area_ha"] - pub["increase_area_ha"]) < 1e-6
        and abs(v.summary["decrease_area_ha"] - pub["decrease_area_ha"]) < 1e-6
    )


def fine_grid(case: str) -> list[float]:
    """Fine grid of the published robustness run (union with the config grid)."""
    rob = json.loads(
        (PUBLIC_ROOT / case / "robustness.json").read_text(encoding="utf-8")
    )
    fg = rob["threshold_curve"]["fine_grid"]
    return rb.union_grid(
        base_config(case)["thresholds"],
        rb.grid_values(fg["start"], fg["stop"], fg["step"]),
    )


_COS: dict[str, rb.CosReference] = {}


def cos_for(case: str, bbox: Sequence[float], grid: cs.Grid) -> rb.CosReference:
    key = f"{case}|{_grid_key(grid)}"
    if key not in _COS:
        print(f"  COS reference for {case}")
        _COS[key] = rb.load_cos(bbox, grid)
    return _COS[key]


def cos_scores(case: str, v: Variant, cfg_raw: Mapping[str, Any]) -> dict[str, Any]:
    cos = cos_for(case, cfg_raw["bbox"], v.grid)
    ref, dom, _ = rb.reference_definition(
        base_config(case)["index"], cos, np.isfinite(v.delta)
    )
    c = rb.confusion(v.inc, ref, dom)
    return {
        "precision": c["precision"],
        "recall": c["recall"],
        "f1": c["f1"],
        "tp": c["tp"],
        "fp": c["fp"],
        "fn": c["fn"],
    }


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


Check = Callable[[Loader, str, argparse.Namespace], dict[str, Any]]


def _row(v: Variant, pub: Mapping[str, Any], **extra: Any) -> dict[str, Any]:
    return {
        "variant": v.name,
        "config": v.cfg_raw,
        "options": v.options,
        "summary": v.summary,
        "vs_published": compare(v.summary, pub),
        **extra,
    }


def _baseline(loader: Loader, case: str, **kw: Any) -> Variant:
    v = run_variant(loader, base_config(case), "published_settings", **kw)
    v.summary["reproduces_published_results_json"] = reproduces(v, published(case))
    return v


def _scene_rule(
    loader: Loader, case: str, targets: Sequence[date], exclude: Sequence[str]
) -> list[dict[str, Any]]:
    """After item closest to each target + control-before closest to after - 20 days."""
    cfg = base_config(case)
    loader.add([cfg["after_item"]])
    m = loader.meta[cfg["after_item"]]
    tile, orbit = m["mgrs_tile"], m["relative_orbit"]
    picks = []
    for tgt in targets:
        rows = cs.discover_items(
            cfg["bbox"],
            str(tgt - timedelta(days=45)),
            str(tgt + timedelta(days=30)),
            max_cloud=5.0,
        )
        after = sv.pick_scene(rows, tgt, tile, orbit, exclude=exclude)
        a_day = date.fromisoformat(after["datetime"][:10])
        ctrl = sv.pick_scene(
            rows,
            a_day - timedelta(days=20),
            tile,
            orbit,
            exclude=[after["id"], *exclude],
        )
        picks.append({"target": str(tgt), "after": after, "control_before": ctrl})
    return picks


def check_b3(loader: Loader, case: str, args: argparse.Namespace) -> dict[str, Any]:
    pub = published(case)
    base = _baseline(loader, case)
    rows = [_row(base, pub)]
    fb = fine_grid(case)
    picks = _scene_rule(loader, case, [date(y, 8, 21) for y in args.years], [])
    for p in picks:
        cfg = base_config(case)
        cfg.pop("seasonal_item", None)
        cfg["after_item"] = p["after"]["id"]
        cfg["control_after_item"] = p["after"]["id"]
        cfg["control_before_item"] = p["control_before"]["id"]
        v = run_variant(loader, cfg, f"2018_to_{p['target'][:4]}", fallback_grid=fb)
        rows.append(
            _row(
                v,
                pub,
                selection=p,
                increase_overlap_with_published=rb.mask_overlap(base.inc, v.inc),
                decrease_overlap_with_published=rb.mask_overlap(base.dec, v.dec),
            )
        )
    return {
        "rule": "after = scene closest to 21 Aug of the year (same tile, relative orbit, cloud < 1 %, baseline 05.xx; ties -> earlier); control = closest such scene to after - 20 days, ending on the after date; before item unchanged (2018-08-18)",
        "variants": rows,
    }


def check_b4(loader: Loader, case: str, args: argparse.Namespace) -> dict[str, Any]:
    pub = published(case)
    base = _baseline(loader, case)
    rows = [_row(base, pub)]
    fb = fine_grid(case)
    cfg0 = base_config(case)
    picks = _scene_rule(
        loader,
        case,
        [date.fromisoformat(t) for t in args.after_targets],
        [cfg0["after_item"]],
    )
    for p in picks:
        cfg = base_config(case)
        cfg.pop("seasonal_item", None)
        cfg["after_item"] = p["after"]["id"]
        cfg["control_after_item"] = p["after"]["id"]
        cfg["control_before_item"] = p["control_before"]["id"]
        v = run_variant(
            loader, cfg, f"after_{p['after']['datetime'][:10]}", fallback_grid=fb
        )
        ov = rb.mask_overlap(base.inc, v.inc)
        rows.append(_row(v, pub, selection=p, increase_overlap_with_published=ov))
    return {
        "rule": "after = scene closest to each target date in summer 2025 other than the published after item (same tile, orbit, cloud < 1 %, baseline 05.xx); control = closest such scene to after - 20 days; before item unchanged",
        "variants": rows,
    }


def check_b5(loader: Loader, case: str, args: argparse.Namespace) -> dict[str, Any]:
    pub = published(case)
    base = _baseline(loader, case)
    rows = [
        _row(base, pub, cos_new_permanent_crop=cos_scores(case, base, base.cfg_raw))
    ]
    grid = rb.grid_values(*INDEX_FINE_GRID)
    for index in ("ndvi", "evi", "ndmi"):
        cfg = base_config(case)
        cfg.pop("seasonal_item", None)
        cfg["index"] = index
        cfg["thresholds"] = grid
        v = run_variant(loader, cfg, f"{index}_fine_grid_0.01")
        rows.append(
            _row(
                v,
                pub,
                increase_overlap_with_published=rb.mask_overlap(base.inc, v.inc),
                decrease_overlap_with_published=rb.mask_overlap(base.dec, v.dec),
                cos_new_permanent_crop=cos_scores(case, v, cfg),
            )
        )
    return {
        "note": "Each index uses the same control_p99 rule on a common grid 0.01..1.00 step 0.01 (the config grid was built for NDVI). Areas of different indices are not the same quantity; overlap with the published NDVI flags and COS agreement are the comparable numbers. EVI with MODIS coefficients (2.5, 6, 7.5, 1), not clipped. NDMI = (B08 - B11) / (B08 + B11), B11 nearest-resampled from 20 m.",
        "variants": rows,
    }


def check_b6(loader: Loader, case: str, args: argparse.Namespace) -> dict[str, Any]:
    pub = published(case)
    base = _baseline(loader, case)
    rows = [_row(base, pub)]
    cfg = base_config(case)
    cfg["exclude_water_from_change"] = not bool(
        cfg.get("exclude_water_from_change", False)
    )
    v = run_variant(loader, cfg, f"exclude_water_{cfg['exclude_water_from_change']}")
    rows.append(
        _row(v, pub, water_pixels_either_date_valid=int((v.water & v.joint).sum()))
    )
    return {"variants": rows}


def check_b7(loader: Loader, case: str, args: argparse.Namespace) -> dict[str, Any]:
    pub = published(case)
    base = _baseline(loader, case)
    rows = [_row(base, pub)]
    cfg = base_config(case)
    if cfg.get("center_delta"):
        cfg.pop("center_delta")
    else:
        cfg["center_delta"] = "median"
    v = run_variant(
        loader,
        cfg,
        f"center_delta_{cfg.get('center_delta', 'none')}",
        fallback_grid=fine_grid(case),
    )
    rows.append(
        _row(
            v,
            pub,
            increase_overlap_with_published=rb.mask_overlap(base.inc, v.inc),
            decrease_overlap_with_published=rb.mask_overlap(base.dec, v.dec),
        )
    )
    return {"variants": rows}


def check_b8(loader: Loader, case: str, args: argparse.Namespace) -> dict[str, Any]:
    pub = published(case)
    base = _baseline(loader, case)
    rows = []
    cfg0 = base_config(case)
    pix_area = base.grid.pixel_size**2
    for ha in args.min_patch_ha:
        s, _, _ = sv.change_summary(
            base.delta,
            base.control,
            base.joint,
            base.water,
            base.summary["threshold"],
            ha,
            pix_area,
            bool(cfg0.get("exclude_water_from_change", False)),
        )
        cfg = {**cfg0, "min_patch_ha": ha}
        rows.append(
            {
                "variant": f"min_patch_{ha:g}_ha",
                "config": cfg,
                "summary": {**base.summary, **s},
                "vs_published": compare(s, pub),
            }
        )
    return {
        "note": "Recomputed from the arrays of the published-settings run (same delta, control and threshold).",
        "reproduces_published": base.summary["reproduces_published_results_json"],
        "variants": rows,
    }


def check_b10(loader: Loader, case: str, args: argparse.Namespace) -> dict[str, Any]:
    pub = published(case)
    base = _baseline(loader, case)
    rows = [_row(base, pub)]
    v = run_variant(
        loader,
        base_config(case),
        f"cloud_buffer_{args.buffer_px}px",
        cloud_buffer_px=args.buffer_px,
        fallback_grid=fine_grid(case),
    )
    rows.append(
        _row(
            v,
            pub,
            extra_masked_pixels_main_pair=int(base.joint.sum() - v.joint.sum()),
            increase_overlap_with_published=rb.mask_overlap(base.inc, v.inc),
        )
    )
    return {
        "note": f"SCL classes {list(cs.CLOUD_BUFFER_SCL)} dilated by {args.buffer_px} pixels of the 10 m grid (8-connected, i.e. a square of {2 * args.buffer_px + 1} x {2 * args.buffer_px + 1} px) and removed from the valid mask of every scene.",
        "variants": rows,
    }


def check_b11(loader: Loader, case: str, args: argparse.Namespace) -> dict[str, Any]:
    pub = published(case)
    base = _baseline(loader, case, keep_obs=True)
    rows = [_row(base, pub)]
    v = run_variant(
        loader,
        base_config(case),
        "scl_bilinear",
        scl_resampling="bilinear",
        fallback_grid=fine_grid(case),
        keep_obs=True,
    )
    scl_diff = {
        iid: int((base.obs[iid].scl != v.obs[iid].scl).sum()) for iid in base.obs
    }
    new_codes = {
        iid: {
            str(k): c
            for k, c in cs.scl_class_counts(v.obs[iid].scl).items()
            if k not in cs.scl_class_counts(base.obs[iid].scl)
        }
        for iid in base.obs
    }
    rows.append(
        _row(
            v,
            pub,
            scl_pixels_differing_from_nearest=scl_diff,
            scl_classes_only_in_bilinear=new_codes,
            increase_overlap_with_published=rb.mask_overlap(base.inc, v.inc),
        )
    )
    return {
        "note": "Bilinear interpolation of a class map averages class codes (e.g. 4 vegetation and 6 water at an edge become 5 not_vegetated); its output is not a valid SCL class at those pixels. Reported for completeness, not as a candidate method.",
        "variants": rows,
    }


def check_b12(loader: Loader, case: str, args: argparse.Namespace) -> dict[str, Any]:
    pub = published(case)
    base = _baseline(loader, case)
    rows = [_row(base, pub)]
    for f in args.aoi_factors:
        cfg = base_config(case)
        cfg.pop("seasonal_item", None)
        cfg["bbox"] = list(sv.scale_bbox(cfg["bbox"], f))
        v = run_variant(loader, cfg, f"aoi_side_x{f:g}", fallback_grid=fine_grid(case))
        rows.append(_row(v, pub))
    return {
        "note": "Box scaled about its centre in WGS84 degrees; each side x factor (area ~ factor^2). Compare shares of valid pixels, not hectares.",
        "variants": rows,
    }


def check_c1(loader: Loader, case: str, args: argparse.Namespace) -> dict[str, Any]:
    base = _baseline(loader, case)
    cos = cos_for(case, base.cfg_raw["bbox"], base.grid)
    ref, dom, desc = rb.reference_definition(
        base_config(case)["index"], cos, np.isfinite(base.delta)
    )
    out = []
    for bm in args.block_m:
        bpx = int(round(bm / base.grid.pixel_size))
        b = rb.strip_draws(
            rb.block_bootstrap(base.inc, ref, dom, bpx, args.iterations, args.seed)
        )
        out.append({"block_m": bm, "block_px": bpx, **b})
    return {
        "reference": desc,
        "threshold": base.summary["threshold"],
        "reproduces_published": base.summary["reproduces_published_results_json"],
        "iterations": args.iterations,
        "seed": args.seed,
        "blocks": out,
    }


def _cos_labels(
    case: str, bbox: Sequence[float], grid: cs.Grid, year: str
) -> tuple[np.ndarray, dict[int, str]]:
    coll, prefix = rc.COLLECTIONS[year]
    feats = rc.fetch_features(coll, bbox)
    raster, codes = rc.rasterize_classes(feats, prefix, grid)
    names = {
        str(f["properties"][f"{prefix}_n4_c"]): str(
            f["properties"].get(f"{prefix}_n4_l", "")
        )
        for f in feats
    }
    return raster, {
        i + 1: f"{c} {names.get(c, '')}".strip() for i, c in enumerate(codes)
    }


def check_c8(loader: Loader, case: str, args: argparse.Namespace) -> dict[str, Any]:
    cfg = base_config(case)
    if not cfg.get("seasonal_item"):
        raise SystemExit("c8 needs a seasonal_item (NDVI case)")
    base = _baseline(loader, case, keep_obs=True)
    after = base.obs[cfg["after_item"]]
    so = loader.observation(cfg["seasonal_item"], base.grid, "ndvi", cfg["valid_scl"])
    amp = np.where(so.valid & after.valid, after.index - so.index, np.nan)
    thr = float(cfg.get("seasonal_amplitude_threshold", 0.15))
    usable = base.inc & np.isfinite(amp)
    groups = {
        "stable": usable & (np.abs(amp) <= thr),
        "seasonal": usable & (np.abs(amp) > thr),
    }
    dom = np.isfinite(base.delta)
    pix_area = base.grid.pixel_size**2
    r25, lab25 = _cos_labels(case, cfg["bbox"], base.grid, "2025")
    r18, lab18 = _cos_labels(case, cfg["bbox"], base.grid, "2018")
    cos = cos_for(case, cfg["bbox"], base.grid)
    trans = np.zeros(base.delta.shape, dtype="int32")
    trans[cos.covered & ~cos.perm18 & ~cos.perm25] = 1
    trans[cos.covered & ~cos.perm18 & cos.perm25] = 2
    trans[cos.covered & cos.perm18 & cos.perm25] = 3
    trans[cos.covered & cos.perm18 & ~cos.perm25] = 4
    tlab = {
        0: "not covered by both COS layers",
        1: "non-permanent 2018 and 2025",
        2: "new permanent crop (2018 other -> 2025 2.2.x)",
        3: "permanent crop both years",
        4: "permanent crop lost by 2025",
    }
    l3 = np.zeros_like(r25)
    l3_names: dict[int, str] = {}
    l3_ids: dict[str, int] = {}
    for cid, name in lab25.items():
        code3 = ".".join(name.split()[0].split(".")[:3])
        l3_ids.setdefault(code3, len(l3_ids) + 1)
        l3_names[l3_ids[code3]] = code3
        l3[r25 == cid] = l3_ids[code3]
    return {
        "data_status": "observation_derived_result",
        "rule": f"increase pixels in patches >= 1 ha; stable if |NDVI(after) - NDVI(seasonal item)| <= {thr}",
        "seasonal_item": cfg["seasonal_item"],
        "group_pixels": {g: int(m.sum()) for g, m in groups.items()},
        "reproduces_published": base.summary["reproduces_published_results_json"],
        "by_cos_transition": sv.class_crosstab(trans, groups, tlab, dom, pix_area),
        "by_cos2025_level3": sv.class_crosstab(l3, groups, l3_names, dom, pix_area),
        "by_cos2025_level4": sv.class_crosstab(r25, groups, lab25, dom, pix_area),
        "by_cos2018_level4": sv.class_crosstab(r18, groups, lab18, dom, pix_area),
    }


def check_b1(loader: Loader, case: str, args: argparse.Namespace) -> dict[str, Any]:
    pub = published(case)
    cfg0 = base_config(case)
    rob = json.loads(
        (PUBLIC_ROOT / case / "robustness.json").read_text(encoding="utf-8")
    )
    second = rob["date_pairs"]["second_pair"]["items"]
    fg = fine_grid(case)
    pairs = {
        "main_pair": cfg0,
        "second_pair": {
            **cfg0,
            "before_item": second["before"],
            "after_item": second["after"],
            "control_before_item": second["control_before"],
            "control_after_item": second["control_after"],
        },
    }
    out = []
    for pname, cfg in pairs.items():
        cfg = dict(cfg)
        cfg.pop("seasonal_item", None)
        v = run_variant(loader, cfg, pname, fallback_grid=fg)
        p99 = v.summary["control_abs_delta_p99_continuous"]
        options = {
            "config_grid": v.summary["threshold"],
            "fine_grid": cs.resolve_threshold("control_p99", fg, v.control)[0],
            "continuous_p99": p99,
        }
        cos = cos_for(case, cfg["bbox"], v.grid)
        ref, dom, _ = rb.reference_definition(cfg0["index"], cos, np.isfinite(v.delta))
        for oname, t in options.items():
            s, inc, _ = sv.change_summary(
                v.delta,
                v.control,
                v.joint,
                v.water,
                t,
                cfg0["min_patch_ha"],
                v.grid.pixel_size**2,
                bool(cfg0.get("exclude_water_from_change", False)),
            )
            c = rb.confusion(inc, ref, dom)
            out.append(
                {
                    "pair": pname,
                    "option": oname,
                    "dates": v.summary["dates"],
                    "threshold_grid": fg
                    if oname == "fine_grid"
                    else (
                        v.summary["threshold_grid"] if oname == "config_grid" else None
                    ),
                    **s,
                    "cos_precision": c["precision"],
                    "cos_recall": c["recall"],
                    "cos_f1": c["f1"],
                    "vs_published": compare(s, pub),
                }
            )
    return {
        "fine_grid": fg,
        "note": "Prepared for the owner's decision; no option is chosen here. COS reference as in robustness.json (Alqueva: new permanent crop; Neves-Corvo: COS 2025 mining class).",
        "rows": out,
    }


CHECKS: dict[str, tuple[Check, tuple[str, ...]]] = {
    "b1": (check_b1, ("alqueva_olive", "neves_corvo_mine")),
    "b3": (check_b3, ("alqueva_olive", "neves_corvo_mine")),
    "b4": (check_b4, ("alqueva_olive", "neves_corvo_mine")),
    "b5": (check_b5, ("alqueva_olive",)),
    "b6": (check_b6, ("alqueva_olive",)),
    "b7": (check_b7, ("neves_corvo_mine",)),
    "b8": (check_b8, ("alqueva_olive", "neves_corvo_mine")),
    "b10": (check_b10, ("alqueva_olive", "neves_corvo_mine")),
    "b11": (check_b11, ("alqueva_olive", "neves_corvo_mine")),
    "b12": (check_b12, ("alqueva_olive", "neves_corvo_mine")),
    "c1": (check_c1, ("alqueva_olive", "neves_corvo_mine")),
    "c8": (check_c8, ("alqueva_olive",)),
}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("items", nargs="+", choices=sorted(CHECKS))
    p.add_argument(
        "--case",
        action="append",
        default=None,
        help="case id (default: every case the check applies to)",
    )
    p.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    p.add_argument("--years", type=int, nargs="+", default=[2019, 2023, 2024])
    p.add_argument(
        "--after-targets", nargs="+", default=["2025-07-20", "2025-08-31", "2025-09-15"]
    )
    p.add_argument("--min-patch-ha", type=float, nargs="+", default=[0.5, 1.0, 2.0])
    p.add_argument("--buffer-px", type=int, default=2)
    p.add_argument("--aoi-factors", type=float, nargs="+", default=[0.7, 1.3])
    p.add_argument(
        "--block-m", type=float, nargs="+", default=[500.0, 1000.0, 2000.0, 5000.0]
    )
    p.add_argument("--iterations", type=int, default=rb.DEFAULT_ITERATIONS)
    p.add_argument("--seed", type=int, default=rb.DEFAULT_SEED)
    args = p.parse_args(argv)
    out_root = args.out_root.resolve()
    if PUBLIC_ROOT.resolve() in [
        out_root,
        *out_root.parents,
    ] or CONFIG_DIR.resolve() in [out_root, *out_root.parents]:
        raise SystemExit("refusing to write into the published data or config folders")
    loader = Loader(out_root / "_cache")
    command = "python " + " ".join(
        [Path(sys.argv[0]).as_posix(), *(argv if argv is not None else sys.argv[1:])]
    )
    for item in args.items:
        fn, cases = CHECKS[item]
        for case in args.case or cases:
            if case not in cases:
                print(f"skip {item} for {case} (not applicable)")
                continue
            t0 = time.perf_counter()
            started = cs.utc_now()
            run_id = f"sens-{item}-{case}-{started.replace(':', '').replace('-', '')}"
            print(f"[{run_id}]")
            body = fn(loader, case, args)
            d = out_root / item
            for i, row in enumerate(body.get("variants", [])):
                if "config" in row:
                    rcs.write_json(
                        d / "configs" / f"{run_id}_{i}_{row['variant']}.json",
                        row["config"],
                    )
            payload = {
                "schema": "tesis.case_study.sensitivity.v1",
                "data_status": "observation_derived_result",
                "item": item,
                "case_id": case,
                "run_id": run_id,
                "published_reference": published(case),
                **body,
                "manifest": {
                    "command": command,
                    "started_at": started,
                    "completed_at": cs.utc_now(),
                    "runtime_seconds": round(time.perf_counter() - t0, 1),
                    "code": git_state(),
                    "environment": cs.environment_versions(),
                    "stac": {
                        "url": cs.EARTH_SEARCH_URL,
                        "collection": cs.COLLECTION,
                        "retrieved_at": loader.retrieved_at,
                    },
                },
            }
            rcs.write_json(d / f"{run_id}.json", payload)
            print(
                f"[{run_id}] wrote {d / (run_id + '.json')} in {payload['manifest']['runtime_seconds']} s"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
