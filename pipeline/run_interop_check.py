"""Compare Earth Search and Microsoft Planetary Computer for a case study's main pair.

Usage (from the repository root)::

    python pipeline/run_interop_check.py pipeline/case_studies/alqueva_olive.json

For the ``before_item`` and ``after_item`` of the config, the script reads red,
NIR and SCL from Earth Search (as ``run_case_study.py`` does) and from Planetary
Computer (``pipeline/src/provider_pc.py``) on the same 10 m grid, then reports
grid alignment, NDVI differences and the agreement of the NDVI-increase flag.

Outputs (public, small):
``docs/case-study/data/<case_id>/interop_planetary_computer.json`` and
``docs/case-study/data/<case_id>/fig_interop.png``.

No account is needed. Planetary Computer asset reads use an anonymous,
short-lived SAS token that is kept in memory and never written to disk.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pipeline.src import case_study as cs  # noqa: E402
from pipeline.src import provider_pc as pp  # noqa: E402

PUBLIC_ROOT = REPO / "docs" / "case-study" / "data"
OUT_JSON = "interop_planetary_computer.json"
OUT_FIG = "fig_interop.png"
TOKEN_MARKERS = ("sig=", "se=", "sv=", "token=", "X-Amz-Signature", "Authorization")
CODE_FILES = (
    "pipeline/src/provider_pc.py",
    "pipeline/run_interop_check.py",
    "pipeline/src/case_study.py",
)


def _clean(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, np.generic):
        return _clean(obj.item())
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    return obj


def write_json(path: Path, payload: Any) -> None:
    text = json.dumps(_clean(payload), indent=2, ensure_ascii=False) + "\n"
    for marker in TOKEN_MARKERS:
        if marker in text:
            raise RuntimeError(f"refusing to write {path.name}: contains {marker!r}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))  # LF on every OS


def git_info() -> dict[str, Any]:
    import subprocess

    def run(*a: str) -> str:
        try:
            return subprocess.run(
                ["git", *a], cwd=REPO, capture_output=True, text=True, check=True
            ).stdout.strip()  # nosec B603 B607
        except Exception:
            return "unknown"

    status = run("status", "--porcelain", "--", *CODE_FILES)
    return {
        "commit": run("rev-parse", "HEAD"),
        "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
        "interop_code_dirty": bool(status) if status != "unknown" else None,
    }


def unsigned_access_status(href: str) -> int | None:
    """HTTP status of a range request to a PC asset without a SAS token."""
    import requests

    try:
        r = requests.get(href, headers={"Range": "bytes=0-15"}, timeout=30)
        return int(r.status_code)
    except Exception:
        return None


def scene_comparison(
    es_obs: cs.Observation,
    pc: pp.PCObservation,
    es_meta: dict[str, Any],
    pc_meta: dict[str, Any],
    tolerance: float,
) -> dict[str, Any]:
    pco = pc.observation
    joint = es_obs.valid & pco.valid
    everywhere = np.ones(joint.shape, dtype=bool)
    out: dict[str, Any] = {
        "joint_valid_pixels": int(joint.sum()),
        "valid_pixels_earth_search": int(es_obs.valid.sum()),
        "valid_pixels_planetary_computer": int(pco.valid.sum()),
        "scl_identical_share": float((es_obs.scl == pco.scl).mean()),
        "valid_mask_agreement": pp.flag_agreement(es_obs.valid, pco.valid, everywhere),
        "ndvi_es_minus_pc": pp.difference_stats(
            es_obs.index, pco.index, joint, tolerance
        ),
        "reflectance_es_minus_pc": {
            k: pp.difference_stats(es_obs.bands[k], pco.bands[k], joint, tolerance)
            for k in ("red", "nir")
        },
    }
    # Raw encoding: PC DN minus the DN that Earth Search stores (ES offset is 0, scale 1e-4).
    raw = {}
    for k in ("red", "nir"):
        es_scale = float(es_meta["assets"][k]["scale"])
        es_dn = np.rint(es_obs.bands[k] / es_scale)
        d = pc.dn[k].astype("float64")[joint] - es_dn[joint]
        add = float(pc_meta["calibration"]["boa_add_offset_dn"][k] or 0)
        raw[k] = {
            "pc_boa_add_offset_dn": add,
            "median_dn_pc_minus_es": float(np.median(d)) if d.size else None,
            "share_pc_dn_plus_offset_equals_es_dn": (
                float((d == -add).mean()) if d.size else None
            ),
        }
    out["raw_dn_pc_minus_es"] = raw
    # What happens if the PC offset is ignored (the error the calibration step prevents).
    offsets = [pc_meta["assets"][k]["offset"] for k in ("red", "nir")]
    if any(o != 0 for o in offsets):
        bands0 = {
            k: cs.to_reflectance(
                pc.dn[k],
                pc_meta["assets"][k]["scale"],
                0.0,
                pc_meta["assets"][k]["nodata"],
            )
            for k in ("red", "nir")
        }
        ndvi0 = cs.compute_index("ndvi", bands0)
        out["if_pc_offset_ignored"] = {
            "note": "NDVI_ES minus NDVI computed from PC without BOA_ADD_OFFSET; shows the size of the calibration error avoided.",
            "ndvi_es_minus_pc": pp.difference_stats(
                es_obs.index, ndvi0, joint, tolerance
            ),
        }
    return out


def change_agreement(
    es: dict[str, cs.Observation],
    pc: dict[str, cs.Observation],
    before: str,
    after: str,
    threshold: float,
    min_px: int,
    tolerance: float,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray, np.ndarray]:
    d_es, j_es = cs.difference(
        es[before].index, es[after].index, es[before].valid, es[after].valid
    )
    d_pc, j_pc = cs.difference(
        pc[before].index, pc[after].index, pc[before].valid, pc[after].valid
    )
    common = j_es & j_pc
    inc_es = np.nan_to_num(d_es, nan=0) > threshold
    inc_pc = np.nan_to_num(d_pc, nan=0) > threshold

    def pipeline_like(
        inc: np.ndarray, b: cs.Observation, a: cs.Observation
    ) -> np.ndarray:
        water = (b.scl == 6) | (a.scl == 6)
        return cs.keep_patches_ge(inc & ~water, min_px)

    pl_es = pipeline_like(inc_es, es[before], es[after])
    pl_pc = pipeline_like(inc_pc, pc[before], pc[after])
    px_ha = 0.01  # 10 m pixel = 100 m2 = 0.01 ha
    result = {
        "data_status": "observation_derived_result",
        "threshold_ndvi_increase": threshold,
        "definition": "flag = (NDVI_after - NDVI_before) > threshold, each provider with its own SCL mask (classes 4, 5, 6)",
        "joint_valid_pixels_earth_search": int(j_es.sum()),
        "joint_valid_pixels_planetary_computer": int(j_pc.sum()),
        "pixels_valid_in_all_four": int(common.sum()),
        "delta_ndvi_es_minus_pc": pp.difference_stats(d_es, d_pc, common, tolerance),
        "pixel_flag": {
            "scope": "pixels valid on both dates for both providers; no water exclusion, no patch filter",
            "increase_pixels_earth_search": int((inc_es & common).sum()),
            "increase_pixels_planetary_computer": int((inc_pc & common).sum()),
            **pp.flag_agreement(inc_es, inc_pc, common),
        },
        "pipeline_like_flag": {
            "scope": f"as run_case_study.py: water (SCL 6 on either date) excluded, patches >= {min_px} pixels kept; compared over the whole grid, invalid pixels count as not flagged",
            "increase_area_ha_earth_search": float(pl_es.sum() * px_ha),
            "increase_area_ha_planetary_computer": float(pl_pc.sum() * px_ha),
            **pp.flag_agreement(pl_es, pl_pc, np.ones(common.shape, dtype=bool)),
        },
    }
    return result, d_es, d_pc, common


def interop_figure(
    diffs: list[tuple[str, np.ndarray]],
    d_es: np.ndarray,
    d_pc: np.ndarray,
    common: np.ndarray,
    threshold: float,
    path: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(
        1, len(diffs) + 1, figsize=(4 * (len(diffs) + 1), 3.6), constrained_layout=True
    )
    bins = np.linspace(-0.3, 0.3, 121)
    for ax, (title, d) in zip(axes, diffs):
        v = d[np.isfinite(d)]
        ax.hist(np.clip(v, bins[0], bins[-1]), bins=bins, color="#4d4d4d")
        ax.set_yscale("log")
        ax.set_xlabel("NDVI Earth Search minus NDVI Planetary Computer")
        ax.set_ylabel("pixels (log scale)")
        p99 = float(np.percentile(np.abs(v), 99)) if v.size else float("nan")
        ax.set_title(
            f"{title}\nmedian |diff| {np.median(np.abs(v)):.4f}, p99 {p99:.4f}",
            fontsize=8,
        )
        ax.tick_params(labelsize=7)
        ax.xaxis.label.set_size(7)
        ax.yaxis.label.set_size(7)
    ax = axes[-1]
    lim = (-0.8, 0.8)
    hb = ax.hexbin(
        d_pc[common],
        d_es[common],
        gridsize=80,
        extent=(*lim, *lim),
        bins="log",
        cmap="Greys",
        mincnt=1,
    )
    ax.plot(lim, lim, color="#999999", lw=0.8)
    ax.axvline(threshold, color="k", ls="--", lw=0.8)
    ax.axhline(threshold, color="k", ls="--", lw=0.8)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("delta NDVI 2018-2025, Planetary Computer", fontsize=7)
    ax.set_ylabel("delta NDVI 2018-2025, Earth Search", fontsize=7)
    ax.set_title(f"Change per pixel, flag threshold {threshold:g} (dashed)", fontsize=8)
    ax.tick_params(labelsize=7)
    cb = fig.colorbar(hb, ax=ax)
    cb.set_label("pixels (log)", fontsize=7)
    cb.ax.tick_params(labelsize=7)
    fig.savefig(path, dpi=130)
    plt.close(fig)


def steps_required(
    scenes: list[dict[str, Any]], unsigned_status: int | None
) -> list[str]:
    s0 = scenes[0]
    es_a = s0["earth_search"]["assets"]
    pc_a = s0["planetary_computer"]["assets"]
    steps = [
        f"Second STAC API root: {pp.PC_STAC_URL} (Earth Search: {cs.EARTH_SEARCH_URL}). The collection ID is the same: {pp.PC_COLLECTION}.",
        "Item IDs follow different schemes (Earth Search: platform_tile_date_sequence_level; Planetary Computer: ESA product name without the processing-baseline field). Neither ID can be converted into the other; items were matched on platform, sensing start, relative orbit and MGRS tile parsed from the s2:product_uri property.",
        "The tile is queried with different properties: Earth Search splits it into mgrs:utm_zone, mgrs:latitude_band and mgrs:grid_square; Planetary Computer has s2:mgrs_tile.",
        "Asset keys differ: "
        + ", ".join(f"{k} -> {pc_a[k]['pc_asset_key']}" for k in ("red", "nir", "scl"))
        + " (Earth Search key -> Planetary Computer key).",
        f"Planetary Computer assets need a short-lived SAS token from {pp.PC_SAS_TOKEN_URL.format(collection=pp.PC_COLLECTION)} appended to every asset URL; an unsigned range request returned HTTP {unsigned_status}. Earth Search assets are public S3 objects read without a token.",
        f"Calibration source differs: Earth Search assets publish raster:bands scale {es_a['red']['scale']} and offset {es_a['red']['offset_in_stac_metadata']}, but the pixels already have the offset removed (earthsearch:boa_offset_applied = {s0['earth_search']['earthsearch_boa_offset_applied']}), so offset 0 is used. Planetary Computer assets have no raster:bands entry (raster_bands_in_stac = {pc_a['red']['raster_bands_in_stac']}); scale and offset were read from MTD_MSIL2A.xml (BOA_QUANTIFICATION_VALUE, BOA_ADD_OFFSET), one extra HTTP request per item.",
    ]
    for s in scenes:
        e, p = s["earth_search"], s["planetary_computer"]
        steps.append(
            f"{s['scene']}: item datetime differs for the same acquisition (Earth Search {e['datetime']}, Planetary Computer {p['datetime']}); "
            f"processing baseline Earth Search {e['processing_baseline']} vs Planetary Computer {p['processing_baseline']}; "
            + (
                f"Planetary Computer BOA_ADD_OFFSET red/NIR = {p['calibration']['boa_add_offset_dn']['red']}/{p['calibration']['boa_add_offset_dn']['nir']} DN, applied."
                if p["calibration"]["boa_add_offset_dn"]["red"] is not None
                else "Planetary Computer product has no BOA_ADD_OFFSET (baseline < 04.00), offset 0."
            )
        )
    steps.append(
        f"Platform property spelling differs (Earth Search '{s0['earth_search']['platform']}', Planetary Computer '{s0['planetary_computer']['platform']}')."
    )
    aligned = all(s["grid_alignment"]["aligned"] for s in scenes)
    steps.append(
        "Pixel grids: same CRS and identical 10 m tile transform on both providers, so no resampling was needed."
        if aligned and all(s["grid_alignment"]["identical_transform"] for s in scenes)
        else "Pixel grids are NOT identical between providers; see grid_alignment."
    )
    return steps


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("config")
    p.add_argument("--threshold", type=float, default=0.30)
    p.add_argument("--tolerance", type=float, default=0.01)
    args = p.parse_args(argv)

    t0 = time.perf_counter()
    started = cs.utc_now()
    cfg_path = Path(args.config).resolve()
    cfg = cs.CaseStudyConfig.from_file(cfg_path)
    if cfg.index != "ndvi":
        raise SystemExit("interop check is defined for NDVI case studies")
    scene_ids = [cfg.before_item, cfg.after_item]
    try:
        es_items = cs.fetch_items(scene_ids)
        es_meta = {iid: cs.item_metadata(it) for iid, it in es_items.items()}
        grid = cs.reference_grid(es_meta[cfg.before_item], cfg.bbox)
        print(f"grid {grid.width}x{grid.height} px @ {grid.pixel_size} m, {grid.crs}")
        token = pp.fetch_sas_token()
        token_retrieved = cs.utc_now()
        es_obs: dict[str, cs.Observation] = {}
        pc_obs: dict[str, pp.PCObservation] = {}
        scenes: list[dict[str, Any]] = []
        unsigned_status = None
        for iid in scene_ids:
            print(f"Earth Search {iid}")
            es_obs[iid] = cs.load_observation(es_meta[iid], grid, "ndvi", cfg.valid_scl)
            pc_item, match = pp.find_pc_match(es_meta[iid])
            print(f"  matched Planetary Computer {pc_item.id}")
            pcm = pp.pc_item_metadata(pc_item, token)
            if unsigned_status is None:
                unsigned_status = unsigned_access_status(pcm["assets"]["red"]["href"])
            align = pp.grid_alignment(
                es_meta[iid]["assets"]["red"]["href"],
                pcm["assets"]["red"]["href"],
                grid,
                token,
            )
            pc_obs[iid] = pp.load_pc_ndvi(pcm, grid, cfg.valid_scl, token)
            comp = scene_comparison(
                es_obs[iid], pc_obs[iid], es_meta[iid], pcm, args.tolerance
            )
            em = es_meta[iid]
            scenes.append(
                {
                    "scene": "before" if iid == cfg.before_item else "after",
                    "earth_search": {
                        k: em[k]
                        for k in (
                            "id",
                            "datetime",
                            "platform",
                            "mgrs_tile",
                            "relative_orbit",
                            "processing_baseline",
                            "product_uri",
                            "earthsearch_boa_offset_applied",
                            "stac_item_url",
                        )
                    }
                    | {"assets": {k: em["assets"][k] for k in ("red", "nir", "scl")}},
                    "planetary_computer": pcm,
                    "matching": match,
                    "grid_alignment": align,
                    "data_status": "observation_derived_result",
                    **comp,
                }
            )
    except Exception as exc:  # never let a signed URL reach the console
        raise SystemExit(pp.redact_url(f"{type(exc).__name__}: {exc}")) from None

    min_px = max(1, int(np.ceil(cfg.min_patch_ha * 10_000 / grid.pixel_size**2)))
    change, d_es, d_pc, common = change_agreement(
        es_obs,
        {k: v.observation for k, v in pc_obs.items()},
        cfg.before_item,
        cfg.after_item,
        args.threshold,
        min_px,
        args.tolerance,
    )
    # Cross-check against the published Earth Search run (same items, same grid).
    published = PUBLIC_ROOT / cfg.case_id / "results.json"
    if published.exists():
        res = json.loads(published.read_text(encoding="utf-8"))
        row = next(
            (
                r
                for r in res.get("sensitivity", [])
                if abs(r["threshold"] - args.threshold) < 1e-9
            ),
            None,
        )
        if row is not None and res.get("delta_centering", {}).get("method") == "none":
            mine = int((np.nan_to_num(d_es, nan=0) > args.threshold).sum())
            change["earth_search_reproduces_published_run"] = {
                "published_run_id": res.get("run_id"),
                "published_main_increase_pixels": row["main_increase_pixels"],
                "recomputed_main_increase_pixels": mine,
                "equal": mine == row["main_increase_pixels"],
            }

    pub = PUBLIC_ROOT / cfg.case_id
    pub.mkdir(parents=True, exist_ok=True)
    fig_path = pub / OUT_FIG
    diffs = []
    for s, iid in zip(scenes, scene_ids):
        joint = es_obs[iid].valid & pc_obs[iid].observation.valid
        d = np.where(joint, es_obs[iid].index - pc_obs[iid].observation.index, np.nan)
        diffs.append(
            (
                f"{s['scene']} {pp.parse_earth_search_id(iid)['date']}: ES {s['earth_search']['processing_baseline']} vs PC {s['planetary_computer']['processing_baseline']}",
                d,
            )
        )
    interop_figure(diffs, d_es, d_pc, common, args.threshold, fig_path)

    payload = {
        "schema": "tesis.case_study.interop.v1",
        "case_id": cfg.case_id,
        "data_status": "observation_derived_result",
        "purpose": "Same Sentinel-2 L2A acquisitions read from two public STAC providers on one 10 m grid; differences are provider/processing differences, not surface change.",
        "started_at": started,
        "completed_at": cs.utc_now(),
        "sas_token_retrieved_at": token_retrieved,
        "runtime_seconds": round(time.perf_counter() - t0, 1),
        "command": "python pipeline/run_interop_check.py "
        + Path(args.config).as_posix()
        + (f" --threshold {args.threshold:g}" if args.threshold != 0.30 else "")
        + (f" --tolerance {args.tolerance:g}" if args.tolerance != 0.01 else ""),
        "config_path": cfg_path.relative_to(REPO).as_posix(),
        "config_sha256": cs.sha256_file(cfg_path),
        "code": git_info(),
        "environment": cs.environment_versions(),
        "providers": {
            "earth_search": {
                "stac_api": cs.EARTH_SEARCH_URL,
                "collection": cs.COLLECTION,
                "access": "anonymous, public S3",
            },
            "planetary_computer": {
                "stac_api": pp.PC_STAC_URL,
                "collection": pp.PC_COLLECTION,
                "access": "anonymous SAS token per collection (not stored)",
                "sas_token_endpoint": pp.PC_SAS_TOKEN_URL.format(
                    collection=pp.PC_COLLECTION
                ),
            },
        },
        "aoi": {"bbox_wgs84": list(cfg.bbox), "grid": grid.as_dict()},
        "valid_scl": list(cfg.valid_scl),
        "tolerance_abs_ndvi": args.tolerance,
        "scenes": scenes,
        "change_agreement": change,
        "steps_required": steps_required(scenes, unsigned_status),
        "notes": [
            "Reflectance and NDVI are computed in float32, as in run_case_study.py; differences below about 1e-6 are floating-point rounding, not data differences.",
            "SCL masks are taken from each provider's own product; pixels are compared only where both masks are valid (joint_valid_pixels).",
            "share_pc_dn_plus_offset_equals_es_dn = share of jointly valid pixels where PC DN + BOA_ADD_OFFSET equals the Earth Search DN exactly.",
        ],
        "figure": {
            "path": fig_path.relative_to(REPO).as_posix(),
            "sha256": cs.sha256_file(fig_path),
        },
    }
    out = pub / OUT_JSON
    write_json(out, payload)
    print(
        f"wrote {out.relative_to(REPO).as_posix()} and {fig_path.relative_to(REPO).as_posix()}"
    )
    for s in scenes:
        n = s["ndvi_es_minus_pc"]
        print(
            f"  {s['scene']}: ES {s['earth_search']['processing_baseline']} / PC {s['planetary_computer']['processing_baseline']}, "
            f"joint {s['joint_valid_pixels']}, median|d| {n.get('median_abs_diff')}, p99|d| {n.get('p99_abs_diff')}, share>{args.tolerance} {n.get('share_abs_diff_gt_tolerance')}"
        )
    print(
        f"  flag agreement {change['pixel_flag'].get('agreement_share')}, kappa {change['pixel_flag'].get('cohen_kappa')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
