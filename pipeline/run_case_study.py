"""Run a Portuguese Sentinel-2 change case study end to end.

Usage (from the repository root)::

    python pipeline/run_case_study.py run pipeline/case_studies/alqueva_olive.json
    python pipeline/run_case_study.py run pipeline/case_studies/neves_corvo_mine.json
    python pipeline/run_case_study.py screen --item S2A_29SNC_20180818_1_L2A --item S2B_29SNC_20240821_0_L2A
    python pipeline/run_case_study.py discover --bbox -8.042 37.907 -7.928 37.997 --start 2025-07-15 --end 2025-09-10

Inputs are read live from the public Earth Search STAC catalogue (no account,
no token). Public, small outputs go to ``docs/case-study/data/<case_id>/``;
full-resolution GeoTIFFs go to ``pipeline/data/case_studies/`` (git-ignored).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from pipeline.src import case_study as cs  # noqa: E402

PUBLIC_ROOT = REPO / "docs" / "case-study" / "data"
LOCAL_ROOT = REPO / "pipeline" / "data" / "case_studies"

STYLE = {
    "ndvi": {
        "label": "NDVI",
        "increase": ("#1a9850", "NDVI increase (greener in after date)"),
        "decrease": ("#d95f02", "NDVI decrease (less green in after date)"),
        "cmap": "BrBG",
    },
    "bsi": {
        "label": "BSI",
        "increase": ("#b2182b", "BSI increase (more bare surface in after date)"),
        "decrease": ("#2166ac", "BSI decrease (less bare surface in after date)"),
        "cmap": "RdBu_r",
    },
}


def _json_default(o: Any) -> Any:
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, float) and not np.isfinite(o):
        return None
    raise TypeError(type(o))


def _clean(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    if isinstance(obj, np.generic):
        return _clean(obj.item())
    return obj


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # LF on every OS: the manifest hashes these bytes, and Git normalises line endings.
    text = (
        json.dumps(_clean(payload), indent=2, ensure_ascii=False, default=_json_default)
        + "\n"
    )
    path.write_bytes(text.encode("utf-8"))


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def true_color(obs: cs.Observation, gain: float = 3.2) -> np.ndarray:
    rgb = np.dstack([obs.bands["red"], obs.bands["green"], obs.bands["blue"]])
    rgb = np.clip(rgb * gain, 0, 1)
    rgb = np.where(np.isfinite(rgb), rgb, 0)
    return rgb ** (1 / 1.4)


def to_wgs84(
    arr: np.ndarray, grid: cs.Grid, resampling: str = "nearest", nodata: float = np.nan
) -> tuple[np.ndarray, list[float]]:
    """Reproject a grid array to EPSG:4326 for a Leaflet image overlay."""
    from rasterio.enums import Resampling
    from rasterio.warp import calculate_default_transform, reproject

    src = arr if arr.ndim == 3 else arr[np.newaxis]
    dst_tr, w, h = calculate_default_transform(
        grid.crs, "EPSG:4326", grid.width, grid.height, *grid.window_bounds
    )
    out = np.full((src.shape[0], h, w), nodata, dtype=src.dtype)
    for i in range(src.shape[0]):
        reproject(
            src[i],
            out[i],
            src_transform=grid.transform,
            src_crs=grid.crs,
            dst_transform=dst_tr,
            dst_crs="EPSG:4326",
            resampling=getattr(Resampling, resampling),
            src_nodata=nodata,
            dst_nodata=nodata,
        )
    west, north = dst_tr * (0, 0)
    east, south = dst_tr * (w, h)
    return (out if arr.ndim == 3 else out[0]), [south, west, north, east]


def save_rgb_overlay(rgb: np.ndarray, grid: cs.Grid, path: Path) -> list[float]:
    from PIL import Image

    chw = np.moveaxis(rgb.astype("float32"), 2, 0)
    out, bounds = to_wgs84(chw, grid, "bilinear", nodata=0.0)
    img = (np.clip(np.moveaxis(out, 0, 2), 0, 1) * 255).astype("uint8")
    Image.fromarray(img).save(path, quality=88)
    return bounds


def save_class_overlay(
    classes: np.ndarray, grid: cs.Grid, style: dict[str, Any], path: Path
) -> list[float]:
    from PIL import Image
    from matplotlib.colors import to_rgb

    out, bounds = to_wgs84(classes.astype("float32"), grid, "nearest", nodata=0.0)
    rgba = np.zeros(out.shape + (4,), dtype="uint8")
    for value, key in ((1, "increase"), (2, "decrease")):
        r, g, b = (int(c * 255) for c in to_rgb(style[key][0]))
        rgba[out == value] = (r, g, b, 220)
    Image.fromarray(rgba, "RGBA").save(path, optimize=True)
    return bounds


def save_delta_overlay(
    delta: np.ndarray, grid: cs.Grid, style: dict[str, Any], vmax: float, path: Path
) -> list[float]:
    from PIL import Image
    import matplotlib

    out, bounds = to_wgs84(delta.astype("float32"), grid, "nearest", nodata=np.nan)
    cmap = matplotlib.colormaps[style["cmap"]]
    norm = np.clip((out + vmax) / (2 * vmax), 0, 1)
    rgba = (cmap(np.nan_to_num(norm, nan=0.5)) * 255).astype("uint8")
    rgba[..., 3] = np.where(np.isfinite(out), 200, 0)
    Image.fromarray(rgba, "RGBA").quantize(64, method=Image.Quantize.FASTOCTREE).save(
        path, optimize=True
    )
    return bounds


def overview_figure(
    cfg: cs.CaseStudyConfig,
    before: cs.Observation,
    after: cs.Observation,
    delta: np.ndarray,
    classes: np.ndarray,
    threshold: float,
    grid: cs.Grid,
    path: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    st = STYLE[cfg.index]
    km = grid.pixel_size / 1000
    extent = [0, grid.width * km, 0, grid.height * km]
    fig, axes = plt.subplots(2, 2, figsize=(11, 10.5), constrained_layout=True)
    d0 = before.meta["datetime"][:10]
    d1 = after.meta["datetime"][:10]
    axes[0, 0].imshow(true_color(before), extent=extent)
    axes[0, 0].set_title(
        f"(a) Observation: Sentinel-2 L2A true colour, {d0}\n{before.meta['id']}",
        fontsize=9,
    )
    axes[0, 1].imshow(true_color(after), extent=extent)
    axes[0, 1].set_title(
        f"(b) Observation: Sentinel-2 L2A true colour, {d1}\n{after.meta['id']}",
        fontsize=9,
    )
    vmax = 0.5 if cfg.index == "ndvi" else 0.25
    im = axes[1, 0].imshow(delta, cmap=st["cmap"], vmin=-vmax, vmax=vmax, extent=extent)
    axes[1, 0].set_title(
        f"(c) Derived: {st['label']} difference ({d1} minus {d0})\nwhite/grey = masked or no change",
        fontsize=9,
    )
    fig.colorbar(im, ax=axes[1, 0], shrink=0.8, label=f"delta {st['label']}")
    cmap = ListedColormap(["#f2f2f2", st["increase"][0], st["decrease"][0], "#9e9e9e"])
    shown = np.where(np.isnan(delta), 3, classes)
    axes[1, 1].imshow(
        shown, cmap=cmap, vmin=0, vmax=3, interpolation="nearest", extent=extent
    )
    axes[1, 1].set_title(
        f"(d) Derived: candidate change, |delta| > {threshold:g}, patches >= {cfg.min_patch_ha:g} ha\ncause not verified",
        fontsize=9,
    )
    axes[1, 1].legend(
        handles=[
            Patch(color=st["increase"][0], label=st["increase"][1]),
            Patch(color=st["decrease"][0], label=st["decrease"][1]),
            Patch(color="#9e9e9e", label="masked (SCL cloud/shadow/other or nodata)"),
        ],
        loc="lower left",
        fontsize=7,
        framealpha=0.9,
    )
    for ax in axes.ravel():
        ax.set_xlabel("km (UTM easting from AOI west edge)", fontsize=8)
        ax.set_ylabel("km", fontsize=8)
        ax.tick_params(labelsize=7)
    fig.suptitle(
        cfg.title + "\nContains modified Copernicus Sentinel data (2018, 2025)",
        fontsize=10,
    )
    fig.savefig(path, dpi=110)
    plt.close(fig)


def histogram_figure(
    cfg: cs.CaseStudyConfig,
    delta: np.ndarray,
    control: np.ndarray,
    threshold: float,
    path: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    st = STYLE[cfg.index]
    lim = 0.8 if cfg.index == "ndvi" else 0.4
    bins = np.linspace(-lim, lim, 161)
    fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
    ax.hist(
        delta[np.isfinite(delta)],
        bins=bins,
        density=True,
        alpha=0.6,
        label="main pair (multi-year)",
        color="#4d4d4d",
    )
    ax.hist(
        control[np.isfinite(control)],
        bins=bins,
        density=True,
        alpha=0.6,
        label="control pair (20 days, same summer)",
        color="#80cdc1",
    )
    for t in (threshold, -threshold):
        ax.axvline(t, color="k", ls="--", lw=1)
    ax.set_yscale("log")
    ax.set_xlabel(f"delta {st['label']} (after minus before)")
    ax.set_ylabel("density (log scale)")
    ax.set_title(
        f"{cfg.case_id}: distribution of {st['label']} differences, threshold +/-{threshold:g}",
        fontsize=9,
    )
    ax.legend(fontsize=8)
    fig.savefig(path, dpi=130)
    plt.close(fig)


def sensitivity_figure(
    cfg: cs.CaseStudyConfig, rows: list[dict[str, Any]], threshold: float, path: Path
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t = [r["threshold"] for r in rows]
    fig, ax = plt.subplots(figsize=(6.5, 4), constrained_layout=True)
    ax.plot(
        t,
        [100 * r["main_flagged_share"] for r in rows],
        "o-",
        color="#4d4d4d",
        label="main pair: flagged share",
    )
    ax.plot(
        t,
        [100 * r["control_flagged_share"] for r in rows],
        "s--",
        color="#35978f",
        label="control pair: flagged share (false-alarm proxy)",
    )
    ax.axvline(
        threshold, color="k", ls=":", lw=1, label=f"selected threshold {threshold:g}"
    )
    ax.set_xlabel(f"|delta {STYLE[cfg.index]['label']}| threshold")
    ax.set_ylabel("% of jointly valid pixels flagged")
    ax.set_yscale("log")
    ax.set_title(f"{cfg.case_id}: threshold sensitivity", fontsize=9)
    ax.legend(fontsize=8)
    fig.savefig(path, dpi=130)
    plt.close(fig)


def write_geotiff(
    path: Path, arr: np.ndarray, grid: cs.Grid, nodata: float | int | None
) -> None:
    import rasterio

    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=grid.height,
        width=grid.width,
        count=1,
        dtype=arr.dtype,
        crs=grid.crs,
        transform=grid.transform,
        nodata=nodata,
        compress="deflate",
        tiled=True,
    ) as dst:
        dst.write(arr, 1)


def patches_geojson(
    mask: np.ndarray,
    delta: np.ndarray,
    grid: cs.Grid,
    extra_layers: dict[str, np.ndarray],
    min_pixels: int,
    change_class: str,
) -> list[dict[str, Any]]:
    from pyproj import Transformer
    from rasterio import features
    from shapely.geometry import mapping, shape
    from shapely.ops import transform as shp_transform

    labels, n = cs.label_patches(mask)
    if n == 0:
        return []
    sizes = np.bincount(labels.ravel())
    to_ll = Transformer.from_crs(grid.crs, "EPSG:4326", always_xy=True).transform
    feats = []
    keep = np.where(sizes >= min_pixels)[0]
    keep = keep[keep > 0]
    lab = np.where(np.isin(labels, keep), labels, 0).astype("int32")
    for geom, value in features.shapes(
        lab, mask=lab > 0, transform=grid.transform, connectivity=8
    ):
        value = int(value)
        sel = labels == value
        poly = shape(geom).simplify(grid.pixel_size, preserve_topology=True)
        props = {
            "patch_id": f"{change_class}-{value}",
            "change_class": change_class,
            "area_ha": round(float(sizes[value] * grid.pixel_size**2 / 10_000), 2),
            "mean_delta": round(float(np.nanmean(delta[sel])), 3),
            "data_status": "observation_derived_result",
        }
        for name, layer in extra_layers.items():
            vals = layer[sel]
            props[name] = (
                round(float(np.nanmean(vals)), 3) if np.isfinite(vals).any() else None
            )
        feats.append(
            {
                "type": "Feature",
                "geometry": mapping(shp_transform(to_ll, poly)),
                "properties": props,
            }
        )
    return feats


def _round_geom(geom: dict[str, Any], nd: int = 5) -> dict[str, Any]:
    def r(c: Any) -> Any:
        if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
            return [round(float(x), nd) for x in c]
        return [r(x) for x in c]

    return {"type": geom["type"], "coordinates": r(geom["coordinates"])}


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_run(args: argparse.Namespace) -> int:
    t0 = time.perf_counter()
    cfg_path = Path(args.config).resolve()
    cfg_raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg = cs.CaseStudyConfig.from_mapping(cfg_raw)
    started = cs.utc_now()
    run_id = f"{cfg.case_id}-{started.replace(':', '').replace('-', '')}"
    print(f"[{run_id}] resolving {len(cfg.item_ids())} STAC items")
    items = cs.fetch_items(cfg.item_ids())
    retrieved = cs.utc_now()
    meta = {iid: cs.item_metadata(it) for iid, it in items.items()}

    tiles = {m["mgrs_tile"] for m in meta.values()}
    if len(tiles) != 1:
        raise SystemExit(
            f"Items span several MGRS tiles {tiles}; pixel grids would not be comparable"
        )
    grid = cs.reference_grid(meta[cfg.before_item], cfg.bbox)
    print(
        f"[{run_id}] grid {grid.width}x{grid.height} px @ {grid.pixel_size} m, {grid.crs}"
    )

    obs: dict[str, cs.Observation] = {}
    for iid in cfg.item_ids():
        rgb = iid in (cfg.before_item, cfg.after_item)
        print(f"[{run_id}] reading {iid}")
        o = cs.load_observation(meta[iid], grid, cfg.index, cfg.valid_scl, rgb=rgb)
        if cfg.seasonal_item and cfg.index != "ndvi" and iid == cfg.seasonal_item:
            raise SystemExit("seasonal split is defined for NDVI only")
        obs[iid] = o

    before, after = obs[cfg.before_item], obs[cfg.after_item]
    delta, joint = cs.difference(before.index, after.index, before.valid, after.valid)
    cb, ca = obs[cfg.control_before_item], obs[cfg.control_after_item]
    control, control_joint = cs.difference(cb.index, ca.index, cb.valid, ca.valid)
    raw_delta_median = float(np.nanmedian(delta))
    centering = cfg.extra.get("center_delta")
    if centering == "median":
        # Scene-wide inter-annual shift (soil moisture, pasture phenology, sensor/atmosphere)
        # that a 20-day control pair cannot capture. Valid only if most of the AOI is unchanged.
        delta = delta - np.float32(raw_delta_median)
        control = control - np.float32(np.nanmedian(control))
    elif centering is not None:
        raise SystemExit(f"unknown center_delta {centering!r}")

    total_px = grid.width * grid.height
    joint_frac = joint.sum() / total_px
    status = "ok"
    if joint_frac < cfg.min_joint_valid_fraction:
        status = "insufficient_valid_coverage"
        print(
            f"[{run_id}] WARNING joint valid fraction {joint_frac:.3f} < {cfg.min_joint_valid_fraction}"
        )

    threshold, threshold_reason = cs.resolve_threshold(
        cfg.primary_threshold, cfg.thresholds, control
    )
    sens = cs.threshold_table(delta, control, cfg.thresholds)
    pix_area = grid.pixel_size**2
    min_px = max(1, int(np.ceil(cfg.min_patch_ha * 10_000 / pix_area)))

    inc, dec = cs.flag_changes(delta, threshold)
    water_either = (before.scl == 6) | (after.scl == 6)
    water_flagged = int(((inc | dec) & water_either).sum())
    if cfg.extra.get("exclude_water_from_change", False):
        # NDVI over open water swings with algae, turbidity and water level; it is not vegetation change.
        inc &= ~water_either
        dec &= ~water_either
    inc_k = cs.keep_patches_ge(inc, min_px)
    dec_k = cs.keep_patches_ge(dec, min_px)
    classes = np.zeros(delta.shape, dtype="uint8")
    classes[inc_k] = 1
    classes[dec_k] = 2

    results: dict[str, Any] = {
        "schema": "tesis.case_study.results.v1",
        "run_id": run_id,
        "case_id": cfg.case_id,
        "title": cfg.title,
        "status": status,
        "index": cfg.index,
        "dates": {
            "before": before.meta["datetime"],
            "after": after.meta["datetime"],
            "control_before": cb.meta["datetime"],
            "control_after": ca.meta["datetime"],
        },
        "aoi": {
            "bbox_wgs84": list(cfg.bbox),
            "grid": grid.as_dict(),
            "area_km2": total_px * pix_area / 1e6,
        },
        "coverage": {
            "data_status": "observation_derived_result",
            "grid_pixels": total_px,
            "valid_pixels_per_item": {
                iid: int(o.valid.sum()) for iid, o in obs.items()
            },
            "scl_class_counts_per_item": {
                iid: cs.scl_class_counts(o.scl) for iid, o in obs.items()
            },
            "joint_valid_pixels_main": int(joint.sum()),
            "joint_valid_fraction_main": float(joint_frac),
            "joint_valid_pixels_control": int(control_joint.sum()),
            "excluded_pixels_main": int(total_px - joint.sum()),
        },
        "index_summary": {
            "data_status": "observation_derived_result",
            "before": cs.summarize(np.where(before.valid, before.index, np.nan)),
            "after": cs.summarize(np.where(after.valid, after.index, np.nan)),
            "delta_main": cs.summarize(delta),
            "delta_control": cs.summarize(control),
            "abs_delta_control_p95": float(np.nanpercentile(np.abs(control), 95)),
            "abs_delta_control_p99": float(np.nanpercentile(np.abs(control), 99)),
        },
        "threshold": {"value": threshold, "rule": threshold_reason},
        "delta_centering": {
            "method": centering or "none",
            "raw_median_delta_main": raw_delta_median,
        },
        "sensitivity": sens,
        "change": {
            "data_status": "observation_derived_result",
            "min_patch_ha": cfg.min_patch_ha,
            "min_patch_pixels": min_px,
            "increase_pixels_raw": int(inc.sum()),
            "decrease_pixels_raw": int(dec.sum()),
            "increase_pixels_in_patches": int(inc_k.sum()),
            "decrease_pixels_in_patches": int(dec_k.sum()),
            "increase_area_ha": float(inc_k.sum() * pix_area / 10_000),
            "decrease_area_ha": float(dec_k.sum() * pix_area / 10_000),
            "increase_share_of_valid": (
                float(inc_k.sum() / joint.sum()) if joint.sum() else None
            ),
            "decrease_share_of_valid": (
                float(dec_k.sum() / joint.sum()) if joint.sum() else None
            ),
            "increase_patches": cs.patch_statistics(inc, pix_area, cfg.min_patch_ha),
            "decrease_patches": cs.patch_statistics(dec, pix_area, cfg.min_patch_ha),
            "water_pixels_either_date": int((water_either & joint).sum()),
            "water_pixels_flagged_before_exclusion": water_flagged,
            "water_excluded_from_change": bool(
                cfg.extra.get("exclude_water_from_change", False)
            ),
            "control_flagged_share_at_threshold": next(
                r["control_flagged_share"] for r in sens if r["threshold"] == threshold
            ),
        },
    }

    seasonal_layer = None
    if cfg.seasonal_item:
        so = obs[cfg.seasonal_item]
        split = cs.seasonal_split(
            inc_k,
            after.index,
            so.index,
            so.valid & after.valid,
            cfg.seasonal_amplitude_threshold,
        )
        results["seasonal_split"] = {
            "data_status": "unverified_interpretation",
            "second_date": so.meta["datetime"],
            "item": so.meta["id"],
            "amplitude_threshold": cfg.seasonal_amplitude_threshold,
            "note": "Within-year NDVI stability of increase pixels in the after year (late May vs August). Stable pixels are consistent with evergreen permanent crops (e.g. olive, almond) and strongly seasonal ones with irrigated annual crops; this is not a land-use label.",
            **split,
        }
        seasonal_layer = np.where(
            so.valid & after.valid, after.index - so.index, np.nan
        )
        stability = np.zeros(
            delta.shape, dtype="uint8"
        )  # 1 stable within year, 2 strongly seasonal
        usable = inc_k & np.isfinite(seasonal_layer)
        stability[
            usable & (np.abs(seasonal_layer) <= cfg.seasonal_amplitude_threshold)
        ] = 1
        stability[
            usable & (np.abs(seasonal_layer) > cfg.seasonal_amplitude_threshold)
        ] = 2
        write_geotiff(
            LOCAL_ROOT / cfg.case_id / run_id / "increase_stability.tif",
            stability,
            grid,
            None,
        )

    if args.resolution_target_ha:
        target = args.resolution_target_ha
    else:
        target = (
            results["change"]["increase_patches"].get("patch_area_ha_median") or 1.0
        )
    results["resolution"] = {
        "data_status": "observation_derived_result",
        "target_area_ha": target,
        "target_source": (
            "median area of increase patches >= min_patch_ha in this run"
            if not args.resolution_target_ha
            else "command-line argument"
        ),
        "rows": cs.resolution_table(float(target)),
    }

    # ---- outputs -------------------------------------------------------------
    pub = PUBLIC_ROOT / cfg.case_id
    pub.mkdir(parents=True, exist_ok=True)
    loc = LOCAL_ROOT / cfg.case_id / run_id
    st = STYLE[cfg.index]

    outputs: dict[str, Path] = {}
    write_geotiff(loc / f"delta_{cfg.index}.tif", delta, grid, np.nan)
    write_geotiff(loc / "change_classes.tif", classes, grid, None)
    outputs["overview_png"] = pub / "fig_overview.png"
    overview_figure(
        cfg, before, after, delta, classes, threshold, grid, outputs["overview_png"]
    )
    outputs["histogram_png"] = pub / "fig_histogram.png"
    histogram_figure(cfg, delta, control, threshold, outputs["histogram_png"])
    outputs["sensitivity_png"] = pub / "fig_sensitivity.png"
    sensitivity_figure(cfg, sens, threshold, outputs["sensitivity_png"])

    overlays = {}
    outputs["overlay_before_jpg"] = pub / "overlay_before.jpg"
    overlays["before"] = save_rgb_overlay(
        true_color(before), grid, outputs["overlay_before_jpg"]
    )
    outputs["overlay_after_jpg"] = pub / "overlay_after.jpg"
    overlays["after"] = save_rgb_overlay(
        true_color(after), grid, outputs["overlay_after_jpg"]
    )
    outputs["overlay_delta_png"] = pub / "overlay_delta.png"
    overlays["delta"] = save_delta_overlay(
        delta,
        grid,
        st,
        0.5 if cfg.index == "ndvi" else 0.25,
        outputs["overlay_delta_png"],
    )
    outputs["overlay_change_png"] = pub / "overlay_change.png"
    overlays["change"] = save_class_overlay(
        classes, grid, st, outputs["overlay_change_png"]
    )

    extra = {"seasonal_amplitude": seasonal_layer} if seasonal_layer is not None else {}
    feats = patches_geojson(
        inc_k, delta, grid, extra, min_px, "increase"
    ) + patches_geojson(dec_k, delta, grid, extra, min_px, "decrease")
    for f in feats:
        f["geometry"] = _round_geom(f["geometry"])
    outputs["patches_geojson"] = pub / "patches.geojson"
    write_json(
        outputs["patches_geojson"],
        {
            "type": "FeatureCollection",
            "name": f"{cfg.case_id} candidate change patches",
            "data_status": "observation_derived_result",
            "run_id": run_id,
            "features": feats,
        },
    )

    outputs["sensitivity_csv"] = pub / "sensitivity.csv"
    with open(outputs["sensitivity_csv"], "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sens[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(sens)

    results["web"] = {
        "overlay_bounds_latlng": overlays,  # [south, west, north, east]
        "legend": {
            "increase": {"color": st["increase"][0], "label": st["increase"][1]},
            "decrease": {"color": st["decrease"][0], "label": st["decrease"][1]},
        },
        "index_label": st["label"],
    }
    outputs["results_json"] = pub / "results.json"
    write_json(outputs["results_json"], results)

    completed = cs.utc_now()
    manifest = {
        "schema": "tesis.case_study.manifest.v1",
        "run_id": run_id,
        "case_id": cfg.case_id,
        "status": status,
        "started_at": started,
        "completed_at": completed,
        "runtime_seconds": round(time.perf_counter() - t0, 1),
        "command": "python " + " ".join([Path(sys.argv[0]).as_posix(), *sys.argv[1:]]),
        "config_path": cfg_path.relative_to(REPO).as_posix(),
        "config_sha256": cs.config_hash(cfg_raw),
        "config": cfg_raw,
        "code": cs.git_state(REPO),
        "environment": cs.environment_versions(),
        "catalogue": {
            "url": cs.EARTH_SEARCH_URL,
            "collection": cs.COLLECTION,
            "retrieved_at": retrieved,
            "access": "live, anonymous HTTPS range reads of public COGs (no credentials, no signed URLs)",
            "license": cs.SENTINEL_LICENSE_URL,
            "attribution": "Contains modified Copernicus Sentinel data 2018, 2025",
        },
        "inputs": [
            {
                **meta[iid],
                "role": [
                    r
                    for r, v in (
                        ("before", cfg.before_item),
                        ("after", cfg.after_item),
                        ("control_before", cfg.control_before_item),
                        ("control_after", cfg.control_after_item),
                        ("seasonal", cfg.seasonal_item),
                    )
                    if v == iid
                ],
            }
            for iid in cfg.item_ids()
        ],
        "processing": {
            "grid": grid.as_dict(),
            "reflectance": "DN * raster:bands.scale + raster:bands.offset (per asset); DN 0 = nodata",
            "resampling_20m": "nearest (SCL, SWIR16) onto the 10 m grid of the same tile",
            "mask": {
                "valid_scl_classes": {str(c): cs.SCL_LABELS[c] for c in cfg.valid_scl}
            },
            "index": cfg.index,
            "threshold": {"value": threshold, "rule": threshold_reason},
            "min_patch": {"ha": cfg.min_patch_ha, "pixels": min_px, "connectivity": 8},
            "random_seed": None,
        },
        "outputs": {
            k: {
                "path": p.relative_to(REPO).as_posix(),
                "sha256": cs.sha256_file(p),
                "data_status": (
                    "public_observation"
                    if "before" in k or "after" in k
                    else "observation_derived_result"
                ),
            }
            for k, p in outputs.items()
        },
        "local_outputs_not_in_git": [
            p.relative_to(REPO).as_posix() for p in sorted(loc.glob("*.tif"))
        ],
    }
    write_json(pub / "manifest.json", manifest)
    write_json(loc / "manifest.json", manifest)
    update_index(cfg, results, manifest)
    print(
        f"[{run_id}] done in {manifest['runtime_seconds']} s; status={status}; threshold={threshold}; "
        f"joint valid={joint.sum()} px ({joint_frac:.1%}); increase {results['change']['increase_area_ha']:.1f} ha, decrease {results['change']['decrease_area_ha']:.1f} ha"
    )
    return 0 if status == "ok" else 2


def update_index(
    cfg: cs.CaseStudyConfig, results: dict[str, Any], manifest: dict[str, Any]
) -> None:
    path = PUBLIC_ROOT / "index.json"
    idx = (
        json.loads(path.read_text(encoding="utf-8"))
        if path.exists()
        else {"schema": "tesis.case_study.index.v1", "cases": {}}
    )
    b = cfg.bbox
    idx["cases"][cfg.case_id] = {
        "title": cfg.title,
        "description": cfg.description,
        "selection_rationale": cfg.selection_rationale,
        "run_id": manifest["run_id"],
        "completed_at": manifest["completed_at"],
        "status": manifest["status"],
        "bbox": list(b),
        "center": [(b[1] + b[3]) / 2, (b[0] + b[2]) / 2],
        "dates": results["dates"],
        "index": cfg.index,
        "path": f"data/{cfg.case_id}/",
    }
    write_json(path, idx)


def cmd_screen(args: argparse.Namespace) -> int:
    """Coarse tile-wide screening used to choose a study area (documents AOI selection)."""
    import rasterio
    from pyproj import Transformer

    items = cs.fetch_items(args.item)
    a, b = (cs.item_metadata(items[i]) for i in args.item)
    if a["mgrs_tile"] != b["mgrs_tile"]:
        raise SystemExit("Screening needs two items of the same tile")

    def nd(m: dict[str, Any]) -> tuple[np.ndarray, Any, Any]:
        out = {}
        for k in ("red", "nir"):
            with cs._gdal_env(), rasterio.open(
                m["assets"][k]["href"], overview_level=args.overview_level
            ) as ds:
                out[k] = cs.to_reflectance(
                    ds.read(1), m["assets"][k]["scale"], m["assets"][k]["offset"]
                )
                tr, crs = ds.transform, ds.crs
        return cs.normalized_difference(out["nir"], out["red"]), tr, crs

    n0, tr, crs = nd(a)
    n1, _, _ = nd(b)
    d = n1 - n0
    px = int(round(args.block_m / tr.a))
    to_ll = Transformer.from_crs(crs, "EPSG:4326", always_xy=True).transform
    rows = []
    for i in range(0, d.shape[0] - px + 1, px // 2):
        for j in range(0, d.shape[1] - px + 1, px // 2):
            blk = d[i : i + px, j : j + px]
            valid = np.isfinite(blk)
            if valid.mean() < 0.9:
                continue
            lon, lat = to_ll(*(tr * (j + px / 2, i + px / 2)))
            rows.append(
                {
                    "center_lat": round(lat, 4),
                    "center_lon": round(lon, 4),
                    "share_increase_gt": float((blk[valid] > args.threshold).mean()),
                    "share_decrease_lt": float((blk[valid] < -args.threshold).mean()),
                }
            )
    rows.sort(key=lambda r: r["share_increase_gt"], reverse=True)
    out = {
        "schema": "tesis.case_study.screening.v1",
        "data_status": "observation_derived_result",
        "purpose": "AOI selection screen (coarse overview, no cloud mask); not a result",
        "created_at": cs.utc_now(),
        "items": [a["id"], b["id"]],
        "overview_level": args.overview_level,
        "pixel_size_m": float(tr.a),
        "block_m": args.block_m,
        "threshold": args.threshold,
        "blocks_evaluated": len(rows),
        "top_blocks": rows[:15],
    }
    path = PUBLIC_ROOT / f"screening_{a['mgrs_tile']}.json"
    write_json(path, out)
    print(json.dumps(out["top_blocks"][:5], indent=1))
    print(f"wrote {path.relative_to(REPO)}")
    return 0


def _grid_from_results(results: dict[str, Any]) -> cs.Grid:
    from affine import Affine
    from rasterio.crs import CRS

    g = results["aoi"]["grid"]
    return cs.Grid(CRS.from_string(g["crs"]), Affine(*g["transform"]), g["width"], g["height"], tuple(g["bounds"]))  # type: ignore[arg-type]


def _read_local(path: Path) -> np.ndarray:
    import rasterio

    with rasterio.open(path) as ds:
        return ds.read(1)


def cmd_evaluate_cos(args: argparse.Namespace) -> int:
    """Compare the latest run's change flags with DGT COS 2018v4 -> 2025v1."""
    from shapely.geometry import box, mapping, shape

    from pipeline.src import reference_cos as rc

    cfg = cs.CaseStudyConfig.from_file(Path(args.config))
    pub = PUBLIC_ROOT / cfg.case_id
    results = json.loads((pub / "results.json").read_text(encoding="utf-8"))
    manifest = json.loads((pub / "manifest.json").read_text(encoding="utf-8"))
    run_dir = LOCAL_ROOT / cfg.case_id / manifest["run_id"]
    if not (run_dir / "change_classes.tif").exists():
        raise SystemExit(
            f"Local outputs of run {manifest['run_id']} not found in {run_dir}; re-run the case study first"
        )
    grid = _grid_from_results(results)
    flags = _read_local(run_dir / "change_classes.tif")
    delta = _read_local(run_dir / f"delta_{cfg.index}.tif")
    valid = np.isfinite(delta)
    pix_area = grid.pixel_size**2

    fetched_at = cs.utc_now()
    layers: dict[str, Any] = {}
    aoi_box = box(*cfg.bbox)
    for year, (coll, prefix) in rc.COLLECTIONS.items():
        feats = rc.fetch_features(coll, cfg.bbox)
        raster, codes = rc.rasterize_classes(feats, prefix, grid)
        layers[year] = {
            "features": feats,
            "prefix": prefix,
            "raster": raster,
            "codes": codes,
            "collection": coll,
        }
        clipped = []
        for f in feats:
            g = shape(f["geometry"]).intersection(aoi_box)
            if g.is_empty:
                continue
            props = {
                k: v
                for k, v in f["properties"].items()
                if k.endswith(("_n4_c", "_n4_l", "_n3_c", "_n2_c", "_n1_c"))
            }
            clipped.append(
                {
                    "type": "Feature",
                    "geometry": _round_geom(mapping(g)),
                    "properties": props,
                }
            )
        write_json(
            pub / f"reference_{coll}.geojson",
            {
                "type": "FeatureCollection",
                "name": f"{coll} clipped to {cfg.case_id} AOI",
                "data_status": "public_observation",
                "attribution": rc.COS_ATTRIBUTION,
                "license": rc.COS_LICENSE,
                "source": f"{rc.OGC_API}/collections/{coll}/items",
                "retrieved_at": fetched_at,
                "features": clipped,
            },
        )

    r18, r25 = layers["2018"], layers["2025"]
    perm18 = rc.code_mask(
        r18["raster"], r18["codes"], lambda c: c.startswith(rc.PERMANENT_CROP_PREFIX)
    )
    perm25 = rc.code_mask(
        r25["raster"], r25["codes"], lambda c: c.startswith(rc.PERMANENT_CROP_PREFIX)
    )
    covered = (r18["raster"] > 0) & (r25["raster"] > 0)
    water25 = rc.code_mask(r25["raster"], r25["codes"], lambda c: c.startswith("9."))
    mining25 = rc.code_mask(
        r25["raster"], r25["codes"], lambda c: c.startswith(rc.MINING_PREFIXES)
    )
    mining18 = rc.code_mask(
        r18["raster"], r18["codes"], lambda c: c.startswith(rc.MINING_PREFIXES)
    )
    ev_valid = valid & covered
    reference = {
        "new_permanent_crop (non-permanent 2018 -> permanent 2025)": ~perm18 & perm25,
        "stable_permanent_crop": perm18 & perm25,
        "lost_permanent_crop (permanent 2018 -> other 2025)": perm18 & ~perm25,
        "stable_non_permanent (excluding water)": ~perm18 & ~perm25 & ~water25,
        "water_2025": water25,
        "industry_logistics_2025 (COS 1.2.1.x)": rc.code_mask(
            r25["raster"], r25["codes"], lambda c: c.startswith("1.2.1.")
        ),
        "mining_2025 (COS 1.6.x)": mining25,
        "new_mining (not 1.6.x in 2018)": mining25 & ~mining18,
    }
    out: dict[str, Any] = {
        "schema": "tesis.case_study.reference_cos.v1",
        "data_status": "observation_derived_result",
        "case_id": cfg.case_id,
        "run_id": manifest["run_id"],
        "reference": {
            "name": rc.COS_ATTRIBUTION,
            "license": rc.COS_LICENSE,
            "dataset_page": rc.COS_DATASET_PAGE,
            "service": rc.OGC_API,
            "collections": [r18["collection"], r25["collection"]],
            "retrieved_at": fetched_at,
            "polygons_2018": len(r18["features"]),
            "polygons_2025": len(r25["features"]),
            "class_codes_2025": r25["codes"],
            "independence": "Produced by DGT from orthophoto interpretation; not derived from this pipeline and not used to choose thresholds.",
        },
        "evaluated_pixels": int(ev_valid.sum()),
        "agreement_matrix": rc.agreement_matrix(flags, reference, ev_valid, pix_area),
        "caveats": [
            "COS is a photo-interpreted map with its own errors; agreement is not ground-truth accuracy.",
            "Generalisation: COS mapping units are >= 0.5 ha (COS2018v4 and COS2025v1 share one specification); internal roads, gaps and field margins are absorbed into polygons.",
            "Reference dates are the COS reference years, not the exact Sentinel-2 acquisition dates.",
            "Pixel counts are spatially autocorrelated; they are not independent samples.",
        ],
    }
    if cfg.index == "ndvi":
        ref_pos = ~perm18 & perm25
        pred = flags == 1
        dom = (
            ev_valid & ~perm18
        )  # only land that was not a permanent crop in 2018 can become a new one
        out["new_permanent_crop_vs_ndvi_increase"] = {
            "domain": "pixels that are not permanent crop in COS2018v4, have a valid NDVI difference and are covered by both COS layers",
            "pixel_level": rc.binary_agreement(pred[dom], ref_pos[dom]),
            "polygon_level": rc.polygon_agreement(
                rc.polygon_units(r25["features"], r25["prefix"], grid),
                pred & dom,
                ref_pos & dom,
                dom,
                min_pixels=50,
            ),
        }
        stab_path = run_dir / "increase_stability.tif"
        if stab_path.exists():
            stab = _read_local(stab_path)
            rows = {}
            for name, code in (("stable_within_year", 1), ("strongly_seasonal", 2)):
                m = (stab == code) & ev_valid
                rows[name] = {
                    "pixels": int(m.sum()),
                    "share_in_permanent_crop_2025": (
                        float(perm25[m].mean()) if m.any() else None
                    ),
                    "share_in_new_permanent_crop": (
                        float(ref_pos[m].mean()) if m.any() else None
                    ),
                }
            out["stability_split_vs_cos"] = {
                "data_status": "observation_derived_result",
                "note": "Tests the within-year stability rule against COS 2025 permanent-crop classes.",
                **rows,
            }
    write_json(pub / "reference_cos.json", out)
    reference_figure(
        cfg, grid, flags, perm18, perm25, covered, pub / "fig_reference_cos.png"
    )
    print(
        json.dumps(
            {k: v for k, v in out.items() if k not in ("reference", "caveats")},
            indent=1,
            default=_json_default,
        )[:3500]
    )
    return 0


def reference_figure(
    cfg: cs.CaseStudyConfig,
    grid: cs.Grid,
    flags: np.ndarray,
    perm18: np.ndarray,
    perm25: np.ndarray,
    covered: np.ndarray,
    path: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    km = grid.pixel_size / 1000
    extent = [0, grid.width * km, 0, grid.height * km]
    cat = np.zeros(flags.shape, dtype="uint8")
    cat[perm18 & perm25] = 1
    cat[~perm18 & perm25] = 2
    cat[perm18 & ~perm25] = 3
    cat[~covered] = 4
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.4), constrained_layout=True)
    cmap = ListedColormap(["#f2f2f2", "#a6dba0", "#008837", "#c2a5cf", "#bdbdbd"])
    axes[0].imshow(
        cat, cmap=cmap, vmin=0, vmax=4, interpolation="nearest", extent=extent
    )
    axes[0].set_title(
        "(a) Independent reference: DGT COS 2018v4 -> 2025v1\npermanent crops = vineyards, orchards, olive groves (2.2.x)",
        fontsize=9,
    )
    axes[0].legend(
        handles=[
            Patch(color="#a6dba0", label="permanent crop both years"),
            Patch(color="#008837", label="new permanent crop by 2025"),
            Patch(color="#c2a5cf", label="permanent crop lost by 2025"),
            Patch(color="#f2f2f2", label="other land use"),
        ],
        fontsize=7,
        loc="lower left",
    )
    st = STYLE[cfg.index]
    cmap2 = ListedColormap(["#f2f2f2", st["increase"][0], st["decrease"][0]])
    axes[1].imshow(
        flags, cmap=cmap2, vmin=0, vmax=2, interpolation="nearest", extent=extent
    )
    axes[1].set_title(
        "(b) Derived: Sentinel-2 candidate change (this pipeline)", fontsize=9
    )
    for ax in axes:
        ax.set_xlabel("km", fontsize=8)
        ax.tick_params(labelsize=7)
    fig.suptitle(
        f"{cfg.case_id}: Sentinel-2 change flags vs official land-use map (COS, DGT, CC-BY)",
        fontsize=10,
    )
    fig.savefig(path, dpi=110)
    plt.close(fig)


def cmd_discover(args: argparse.Namespace) -> int:
    rows = cs.discover_items(args.bbox, args.start, args.end, args.max_cloud)
    for r in rows:
        print(
            f"{r['datetime'][:10]}  {r['id']:<28} R{r['relative_orbit']}  baseline {r['processing_baseline']}  cloud {r['eo_cloud_cover']:.2f}%"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a case study from a JSON config")
    r.add_argument("config")
    r.add_argument("--resolution-target-ha", type=float, default=None)
    r.set_defaults(func=cmd_run)
    s = sub.add_parser("screen", help="coarse tile-wide screening for AOI selection")
    s.add_argument("--item", action="append", required=True)
    s.add_argument("--overview-level", type=int, default=3)
    s.add_argument("--block-m", type=float, default=10_000)
    s.add_argument("--threshold", type=float, default=0.2)
    s.set_defaults(func=cmd_screen)
    e = sub.add_parser(
        "evaluate-cos",
        help="compare latest run with DGT COS 2018v4 -> 2025v1 (independent reference)",
    )
    e.add_argument("config")
    e.set_defaults(func=cmd_evaluate_cos)
    d = sub.add_parser("discover", help="list candidate scenes")
    d.add_argument("--bbox", type=float, nargs=4, required=True)
    d.add_argument("--start", required=True)
    d.add_argument("--end", required=True)
    d.add_argument("--max-cloud", type=float, default=5.0)
    d.set_defaults(func=cmd_discover)
    args = p.parse_args(argv)
    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
