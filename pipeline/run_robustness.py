"""Robustness evidence for a Sentinel-2 case study (threshold curve, bootstrap, second pair).

Usage (from the repository root)::

    python pipeline/run_robustness.py pipeline/case_studies/alqueva_olive.json \
        --alt-before S2B_29SNC_20180823_1_L2A --alt-after S2A_29SNC_20250823_0_L2A \
        --alt-control-before S2A_29SNC_20250803_0_L2A

Reads the scenes live from Earth Search and the COS polygons live from the DGT
OGC API, as ``run_case_study.py`` does. It does not touch the main case
outputs: it writes ``robustness.json``, ``fig_threshold_curve.png`` and
``fig_bootstrap.png`` to ``docs/case-study/data/<case_id>/``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pipeline import run_case_study as rcs  # noqa: E402
from pipeline.src import case_study as cs  # noqa: E402
from pipeline.src import reference_cos as rc  # noqa: E402
from pipeline.src import robustness as rb  # noqa: E402

PUBLIC_ROOT = REPO / "docs" / "case-study" / "data"
CODE_PATHS = (
    "pipeline/src/robustness.py",
    "pipeline/run_robustness.py",
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


def _grid_matches(a: cs.Grid, b: cs.Grid) -> bool:
    return (
        str(a.crs) == str(b.crs)
        and a.width == b.width
        and a.height == b.height
        and np.allclose(list(a.transform)[:6], list(b.transform)[:6])
    )


def local_delta_check(
    manifest: dict[str, Any], index: str, delta: np.ndarray
) -> dict[str, Any]:
    """Compare the recomputed difference with the run's local GeoTIFF, if present."""
    rel = next(
        (
            p
            for p in manifest.get("local_outputs_not_in_git", [])
            if p.endswith(f"delta_{index}.tif")
        ),
        None,
    )
    if rel is None or not (REPO / rel).exists():
        return {"path": rel, "found": False}
    local = rcs._read_local(REPO / rel)
    both = np.isfinite(local) & np.isfinite(delta)
    return {
        "path": rel,
        "found": True,
        "same_valid_mask": bool(np.array_equal(np.isfinite(local), np.isfinite(delta))),
        "max_abs_difference": float(np.max(np.abs(local[both] - delta[both]))),
    }


def pair_summary(
    pair: rb.PairResult,
    cfg: cs.CaseStudyConfig,
    min_px: int,
    pix_area: float,
    ref: np.ndarray,
    domain: np.ndarray,
    cos: rb.CosReference,
    poly_min_px: int,
    extra_thresholds: list[float],
    curve_grid: list[float],
) -> tuple[dict[str, Any], np.ndarray]:
    exclude = pair.water_either if cfg.extra.get("exclude_water_from_change") else None
    inc = rb.change_mask(pair.delta, pair.threshold, min_px, exclude, "increase")
    dec = rb.change_mask(pair.delta, pair.threshold, min_px, exclude, "decrease")
    c = np.abs(pair.control[np.isfinite(pair.control)])
    joint = int(pair.joint.sum())
    # Same control_p99 rule, applied to the finer robustness grid.
    t_fine, rule_fine = cs.resolve_threshold("control_p99", curve_grid, pair.control)
    extra_thresholds = [*extra_thresholds, t_fine]
    out: dict[str, Any] = {
        "data_status": "observation_derived_result",
        "items": {
            "before": pair.before_id,
            "after": pair.after_id,
            "control_before": pair.control_before_id,
            "control_after": pair.control_after_id,
        },
        "dates": pair.dates,
        "joint_valid_pixels": joint,
        "joint_valid_fraction": joint / pair.joint.size,
        "delta_centering": {
            "method": pair.centering,
            "raw_median_delta": pair.raw_median_delta,
        },
        "abs_delta_control_p99": float(np.percentile(c, 99)),
        "threshold": {
            "value": pair.threshold,
            "rule": pair.threshold_rule,
            "grid": pair.threshold_grid,
        },
        "threshold_rule_on_curve_grid": {
            "value": float(t_fine),
            "rule": rule_fine,
            "note": "Not used for the main result; shows how much the selected value depends on the spacing of the config grid.",
        },
        "control_flagged_share_at_threshold": float((c > pair.threshold).mean()),
        "increase_pixels_in_patches": int(inc.sum()),
        "increase_area_ha": float(inc.sum() * pix_area / 10_000),
        "decrease_area_ha": float(dec.sum() * pix_area / 10_000),
        "cos_agreement": {},
    }
    for t in dict.fromkeys([pair.threshold, *extra_thresholds]):
        flags = (
            inc
            if t == pair.threshold
            else rb.change_mask(pair.delta, t, min_px, exclude, "increase")
        )
        row: dict[str, Any] = {
            "pixel_level": rb.confusion(flags, ref, domain),
            "increase_area_ha": float(flags.sum() * pix_area / 10_000),
        }
        if cfg.index == "ndvi":
            row["polygon_level"] = rc.polygon_agreement(
                cos.units25,
                flags & domain,
                ref & domain,
                domain,
                min_pixels=poly_min_px,
            )
        out["cos_agreement"][f"{t:g}"] = row
    return out, inc


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------


def curve_figure(
    cfg: cs.CaseStudyConfig,
    curves: dict[str, list[dict[str, Any]]],
    thresholds: dict[str, float],
    ref_label: str,
    path: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"precision": "#1b7837", "recall": "#762a83", "f1": "#444444"}
    styles = {"main_pair": "-", "second_pair": "--"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), constrained_layout=True)
    for name, rows in curves.items():
        x = [r["threshold"] for r in rows]
        for k, col in colors.items():
            y = [np.nan if r[k] is None else r[k] for r in rows]
            axes[0].plot(
                x,
                y,
                styles[name],
                color=col,
                marker="o",
                ms=2.5,
                lw=1.3,
                label=f"{k} ({name.replace('_', ' ')})",
            )
        cshare = [r["control_flagged_share"] for r in rows]
        axes[1].plot(
            x,
            np.maximum(cshare, 1e-6),
            styles[name],
            color="#2166ac",
            marker="o",
            ms=2.5,
            label=f"control pair of {name.replace('_', ' ')}",
        )
    for name, t in thresholds.items():
        for ax in axes:
            ax.axvline(t, color="#999999", ls=styles[name], lw=0.9)
    axes[1].axhline(0.01, color="#d6604d", lw=0.9, label="1 % of control pixels")
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel("score against COS")
    axes[0].set_title(f"(a) agreement with COS: {ref_label}", fontsize=9)
    axes[0].legend(fontsize=7, ncol=2, loc="lower left")
    axes[1].set_yscale("log")
    axes[1].set_ylabel("share of control pixels with |delta| > threshold")
    axes[1].set_title(
        "(b) control pair: no-change noise flagged at each threshold", fontsize=9
    )
    axes[1].legend(fontsize=7)
    for ax in axes:
        ax.set_xlabel(f"{cfg.index.upper()} change threshold (grey lines: selected)")
        ax.tick_params(labelsize=7)
        ax.grid(alpha=0.3, lw=0.5)
    fig.suptitle(
        f"{cfg.case_id}: threshold sensitivity (observation-derived result)",
        fontsize=10,
    )
    fig.savefig(path, dpi=110)
    plt.close(fig)


def bootstrap_figure(
    cfg: cs.CaseStudyConfig, boots: dict[str, dict[str, Any]], path: Path
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = list(boots)
    fig, axes = plt.subplots(
        len(names),
        2,
        figsize=(9, 2.3 * len(names) + 0.6),
        constrained_layout=True,
        squeeze=False,
    )
    for i, name in enumerate(names):
        b = boots[name]
        for j, k in enumerate(("precision", "recall")):
            ax = axes[i][j]
            d = b["_draws"][k]
            d = d[np.isfinite(d)]
            ax.hist(d, bins=40, color="#9ecae1", edgecolor="#4292c6", lw=0.4)
            s = b[k]
            if s["estimate"] is not None:
                ax.axvline(s["estimate"], color="#08306b", lw=1.2)
            for v in (s["ci_low"], s["ci_high"]):
                if v is not None:
                    ax.axvline(v, color="#cb181d", ls="--", lw=1)
            ax.set_title(
                f"{name}: {k} {s['estimate']:.3f} "
                f"[{s['ci_low']:.3f}, {s['ci_high']:.3f}] (n units {b['units']})",
                fontsize=8,
            )
            ax.tick_params(labelsize=7)
    fig.suptitle(
        f"{cfg.case_id}: bootstrap distributions, {boots[names[0]]['iterations']} draws, "
        f"seed {boots[names[0]]['seed']} (red: 95 % percentile CI)",
        fontsize=9,
    )
    fig.savefig(path, dpi=110)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------


def run(args: argparse.Namespace) -> int:
    t0 = time.perf_counter()
    started = cs.utc_now()
    cfg_path = Path(args.config).resolve()
    cfg_raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg = cs.CaseStudyConfig.from_mapping(cfg_raw)
    pub = PUBLIC_ROOT / cfg.case_id
    results_path, manifest_path = pub / "results.json", pub / "manifest.json"
    cos_path = pub / "reference_cos.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    published_cos = (
        json.loads(cos_path.read_text(encoding="utf-8")) if cos_path.exists() else None
    )

    fine = rb.grid_values(*args.fine_grid)
    curve_grid = rb.union_grid(cfg.thresholds, fine)

    # Grid: same rule as the main run (10 m grid of the before item's tile).
    print(f"[{cfg.case_id}] resolving STAC items")
    items_main = [
        cfg.before_item,
        cfg.after_item,
        cfg.control_before_item,
        cfg.control_after_item,
    ]
    alt_ctrl_after = args.alt_control_after or args.alt_after
    items_alt = [
        args.alt_before,
        args.alt_after,
        args.alt_control_before,
        alt_ctrl_after,
    ]
    cache = rb.ObservationCache(cfg)
    cache.add_items(items_main + items_alt)
    grid = cs.reference_grid(cache.meta[cfg.before_item], cfg.bbox)
    published_grid = rcs._grid_from_results(results)
    if not _grid_matches(grid, published_grid):
        raise SystemExit("Recomputed grid differs from the published results.json grid")
    cache.grid = grid
    pix_area = grid.pixel_size**2
    min_px = max(1, int(np.ceil(cfg.min_patch_ha * 10_000 / pix_area)))

    print(f"[{cfg.case_id}] main pair")
    main = rb.compute_pair(cache, *items_main, cfg.thresholds)
    print(f"[{cfg.case_id}] second pair")
    alt = rb.compute_pair(cache, *items_alt, cfg.thresholds, fallback_grid=curve_grid)

    print(f"[{cfg.case_id}] COS reference")
    cos = rb.load_cos(cfg.bbox, grid)
    valid = np.isfinite(main.delta)
    ref, domain, ref_desc = rb.reference_definition(cfg.index, cos, valid)
    # The second pair has its own valid pixels; evaluate it on its own domain.
    ref_alt, domain_alt, _ = rb.reference_definition(
        cfg.index, cos, np.isfinite(alt.delta)
    )
    exclude_main = (
        main.water_either if cfg.extra.get("exclude_water_from_change") else None
    )
    exclude_alt = (
        alt.water_either if cfg.extra.get("exclude_water_from_change") else None
    )

    print(f"[{cfg.case_id}] threshold curves ({len(curve_grid)} thresholds)")
    curves = {
        "main_pair": rb.threshold_curve(
            main.delta,
            main.control,
            ref,
            domain,
            curve_grid,
            min_px,
            pix_area,
            exclude_main,
        ),
        "second_pair": rb.threshold_curve(
            alt.delta,
            alt.control,
            ref_alt,
            domain_alt,
            curve_grid,
            min_px,
            pix_area,
            exclude_alt,
        ),
    }

    main_sum, inc_main = pair_summary(
        main,
        cfg,
        min_px,
        pix_area,
        ref,
        domain,
        cos,
        args.polygon_min_pixels,
        [],
        curve_grid,
    )
    alt_sum, inc_alt = pair_summary(
        alt,
        cfg,
        min_px,
        pix_area,
        ref_alt,
        domain_alt,
        cos,
        args.polygon_min_pixels,
        [main.threshold],
        curve_grid,
    )
    inc_alt_at_main_t = rb.change_mask(
        alt.delta, main.threshold, min_px, exclude_alt, "increase"
    )

    # Reproduction checks against the published outputs of the main run.
    checks: dict[str, Any] = {
        "threshold_matches_results_json": main.threshold
        == float(results["threshold"]["value"]),
        "increase_area_ha_matches_results_json": abs(
            main_sum["increase_area_ha"] - float(results["change"]["increase_area_ha"])
        )
        < 1e-6,
        "local_delta_geotiff": local_delta_check(manifest, cfg.index, main.delta),
    }
    if published_cos and "new_permanent_crop_vs_ndvi_increase" in published_cos:
        pub_px = published_cos["new_permanent_crop_vs_ndvi_increase"]["pixel_level"]
        mine = main_sum["cos_agreement"][f"{main.threshold:g}"]["pixel_level"]
        checks["pixel_counts_match_reference_cos_json"] = all(
            pub_px[k] == mine[k] for k in ("tp", "fp", "fn", "tn")
        )
        pub_poly = published_cos["new_permanent_crop_vs_ndvi_increase"]["polygon_level"]
        mine_poly = main_sum["cos_agreement"][f"{main.threshold:g}"]["polygon_level"]
        checks["polygon_counts_match_reference_cos_json"] = all(
            pub_poly[k] == mine_poly[k] for k in ("tp", "fp", "fn", "tn")
        )
    elif published_cos and cfg.index == "bsi":
        row = next(
            r
            for r in published_cos["agreement_matrix"]
            if r["reference_category"].startswith("mining_2025")
        )
        mine = main_sum["cos_agreement"][f"{main.threshold:g}"]["pixel_level"]
        checks["precision_recall_match_reference_cos_json_mining_row"] = bool(
            abs(mine["precision"] - row["share_of_all_increase_flags_in_category"])
            < 1e-12
            and abs(mine["recall"] - row["share_flagged_increase"]) < 1e-12
        )

    print(f"[{cfg.case_id}] bootstrap ({args.iterations} iterations, seed {args.seed})")
    boots: dict[str, dict[str, Any]] = {}
    for bm in args.block_m:
        bpx = int(round(bm / grid.pixel_size))
        b = rb.block_bootstrap(inc_main, ref, domain, bpx, args.iterations, args.seed)
        b["block_m"] = float(bm)
        boots[f"pixel, {bm:g} m blocks"] = b
    if cfg.index == "ndvi":
        up, ur = rb.polygon_unit_labels(
            cos.units25,
            inc_main & domain,
            ref & domain,
            domain,
            args.polygon_min_pixels,
        )
        b = rb.unit_bootstrap(up, ur, args.iterations, args.seed)
        b["unit"] = "COS2025v1 polygon clipped to the AOI"
        b["min_unit_pixels"] = args.polygon_min_pixels
        b["majority_share"] = 0.5
        boots["polygon, COS units"] = b

    curve_png = pub / "fig_threshold_curve.png"
    boot_png = pub / "fig_bootstrap.png"
    curve_figure(
        cfg,
        curves,
        {"main_pair": main.threshold, "second_pair": alt.threshold},
        ref_desc["reference_positive"].split(":")[0].split(";")[0],
        curve_png,
    )
    bootstrap_figure(cfg, boots, boot_png)

    completed = cs.utc_now()
    out: dict[str, Any] = {
        "schema": "tesis.case_study.robustness.v1",
        "data_status": "observation_derived_result",
        "case_id": cfg.case_id,
        "main_run_id": manifest["run_id"],
        "reference": {
            **ref_desc,
            "source": rc.COS_ATTRIBUTION,
            "license": rc.COS_LICENSE,
            "collections": [c for c, _ in rc.COLLECTIONS.values()],
        },
        "threshold_curve": {
            "data_status": "observation_derived_result",
            "thresholds": curve_grid,
            "config_grid": list(cfg.thresholds),
            "fine_grid": {
                "start": args.fine_grid[0],
                "stop": args.fine_grid[1],
                "step": args.fine_grid[2],
            },
            "min_patch_pixels": min_px,
            "water_excluded": bool(cfg.extra.get("exclude_water_from_change")),
            "note": "Flags are increase pixels in 8-connected patches >= min_patch_ha. control_flagged_share is the share of valid control-pair pixels with |delta| > threshold before the patch filter (same definition as sensitivity.csv).",
            "main_pair": curves["main_pair"],
            "second_pair": curves["second_pair"],
        },
        "bootstrap": {
            "data_status": "observation_derived_result",
            "threshold": main.threshold,
            "date_pair": "main_pair",
            "method": "Percentile bootstrap. Pixel level: square blocks of the 10 m grid (only blocks with at least one domain pixel) are drawn with replacement, as many as there are, and their tp/fp/fn counts summed. Polygon level: COS2025v1 polygons drawn with replacement.",
            "caveat": "Blocks and polygons are still spatially correlated with their neighbours, so the intervals are likely too narrow rather than too wide. They describe sampling variation over this AOI, not error in COS itself.",
            "results": rb.strip_draws(boots),
        },
        "date_pairs": {
            "note": "Second pair chosen by the same rule (relative orbit 037, scene cloud < 1 %, peak summer, processing baseline 05.xx) with dates a few days from the main pair. Its control pair is a 20-day pair ending on the second pair's after date where available.",
            "main_pair": main_sum,
            "second_pair": alt_sum,
            "increase_overlap_main_vs_second": {
                "data_status": "observation_derived_result",
                "note": "a = main-pair increase flags at its threshold, b = second-pair increase flags.",
                "each_pair_at_own_threshold": rb.mask_overlap(inc_main, inc_alt),
                f"both_at_main_threshold_{main.threshold:g}": rb.mask_overlap(
                    inc_main, inc_alt_at_main_t
                ),
            },
        },
        "checks": checks,
    }
    out["manifest"] = {
        "command": "python " + " ".join([Path(sys.argv[0]).as_posix(), *sys.argv[1:]]),
        "started_at": started,
        "completed_at": completed,
        "runtime_seconds": round(time.perf_counter() - t0, 1),
        "random_seed": args.seed,
        "iterations": args.iterations,
        "code": git_state(),
        "environment": cs.environment_versions(),
        "config_path": cfg_path.relative_to(REPO).as_posix(),
        "config_sha256": cs.config_hash(cfg_raw),
        "inputs": {
            "stac": {
                "url": cs.EARTH_SEARCH_URL,
                "collection": cs.COLLECTION,
                "retrieved_at": cache.retrieved_at,
                "items": [
                    {
                        "id": iid,
                        "datetime": m["datetime"],
                        "platform": m["platform"],
                        "relative_orbit": m["relative_orbit"],
                        "processing_baseline": m["processing_baseline"],
                        "eo_cloud_cover": m["eo_cloud_cover"],
                        "stac_item_url": m["stac_item_url"],
                    }
                    for iid, m in cache.meta.items()
                ],
            },
            "cos": {
                "service": rc.OGC_API,
                "collections": [c for c, _ in rc.COLLECTIONS.values()],
                "retrieved_at": cos.retrieved_at,
                "polygons_2018": cos.polygons_2018,
                "polygons_2025": cos.polygons_2025,
            },
            "published_files_read": {
                p.relative_to(REPO).as_posix(): cs.sha256_file(p)
                for p in (results_path, manifest_path, cos_path)
                if p.exists()
            },
        },
        "outputs": {
            p.relative_to(REPO).as_posix(): {
                "sha256": cs.sha256_file(p),
                "data_status": "observation_derived_result",
            }
            for p in (curve_png, boot_png)
        },
    }
    rcs.write_json(pub / "robustness.json", out)
    print(json.dumps(rb.strip_draws(checks), indent=1, default=rcs._json_default))
    print(f"[{cfg.case_id}] wrote {(pub / 'robustness.json').relative_to(REPO)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("config")
    p.add_argument("--alt-before", required=True, help="STAC id, second pair before")
    p.add_argument("--alt-after", required=True, help="STAC id, second pair after")
    p.add_argument(
        "--alt-control-before",
        required=True,
        help="STAC id, start of the second pair's control pair",
    )
    p.add_argument(
        "--alt-control-after",
        default=None,
        help="STAC id, end of the second pair's control pair (default: --alt-after)",
    )
    p.add_argument(
        "--fine-grid",
        type=float,
        nargs=3,
        default=(0.05, 0.50, 0.025),
        metavar=("START", "STOP", "STEP"),
    )
    p.add_argument("--block-m", type=float, nargs="+", default=list(rb.DEFAULT_BLOCK_M))
    p.add_argument("--iterations", type=int, default=rb.DEFAULT_ITERATIONS)
    p.add_argument("--seed", type=int, default=rb.DEFAULT_SEED)
    p.add_argument("--polygon-min-pixels", type=int, default=50)
    return run(p.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
