"""Independent re-computation of a published case-study result.

A deliberately small second implementation that shares NO code with
pipeline/src/case_study.py or pipeline/run_case_study.py. It reads the
config and the published results, fetches the STAC items with plain HTTP,
reads the public COGs itself, recomputes every headline number, and
compares them with docs/case-study/data/<case>/results.json.

Usage:  python pipeline/verify_independent.py pipeline/case_studies/alqueva_olive.json
Exit 0 if everything matches, 1 otherwise. Writes independent_check.json.

What it shares with the main pipeline on purpose (inputs, not logic): the
config file, and the AOI grid bounds recorded in results.json.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
import requests
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
from scipy import ndimage

STAC = "https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/"
REPO = Path(__file__).resolve().parents[1]


def item(item_id: str) -> dict:
    r = requests.get(STAC + item_id, timeout=60)
    r.raise_for_status()
    return r.json()


def band(it: dict, key: str, bounds, shape) -> np.ndarray:
    """Reflectance (or SCL class) on the published 10 m grid; nodata -> NaN."""
    a = it["assets"][key]
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", AWS_NO_SIGN_REQUEST="YES"):
        with rasterio.open(a["href"]) as ds:
            dn = ds.read(1, window=from_bounds(*bounds, transform=ds.transform), out_shape=shape, resampling=Resampling.nearest)
    if key == "scl":
        return dn
    rb = a["raster:bands"][0]
    # Pixels already carry the BOA offset correction when Earth Search says so.
    offset = 0.0 if it["properties"].get("earthsearch:boa_offset_applied") else rb.get("offset", 0.0)
    out = dn.astype("float64") * rb["scale"] + offset
    out[dn == 0] = np.nan
    return out


def index(it: dict, name: str, bounds, shape, valid_scl) -> tuple[np.ndarray, np.ndarray]:
    r = lambda k: band(it, k, bounds, shape)  # noqa: E731
    if name == "ndvi":
        nir, red = r("nir"), r("red")
        num, den = nir - red, nir + red
    else:  # bsi
        swir, red, nir, blue = r("swir16"), r("red"), r("nir"), r("blue")
        num, den = (swir + red) - (nir + blue), (swir + red) + (nir + blue)
    with np.errstate(divide="ignore", invalid="ignore"):
        idx = np.where(np.abs(den) > 1e-6, num / den, np.nan)
    idx = np.clip(idx, -1, 1)
    scl = band(it, "scl", bounds, shape)
    valid = np.isin(scl, valid_scl) & np.isfinite(idx)
    return idx, valid


def area_in_patches(mask: np.ndarray, min_px: int) -> int:
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    if n == 0:
        return 0
    sizes = np.bincount(lab.ravel())[1:]
    return int(sizes[sizes >= min_px].sum())


def main(cfg_path: str) -> int:
    t0 = time.time()
    cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
    pub = REPO / "docs" / "case-study" / "data" / cfg["case_id"]
    res = json.loads((pub / "results.json").read_text(encoding="utf-8"))
    g = res["aoi"]["grid"]
    bounds, shape = g["bounds"], (g["height"], g["width"])
    px_area = g["pixel_size_m"] ** 2
    ids = {k: cfg[k] for k in ("before_item", "after_item", "control_before_item", "control_after_item")}
    items = {k: item(v) for k, v in ids.items()}
    ix = {k: index(items[k], cfg["index"], bounds, shape, cfg.get("valid_scl", [4, 5, 6])) for k in ids}

    def diff(a: str, b: str) -> np.ndarray:
        (ia, va), (ib, vb) = ix[a], ix[b]
        return np.where(va & vb, ib - ia, np.nan)

    delta, control = diff("before_item", "after_item"), diff("control_before_item", "control_after_item")
    if cfg.get("center_delta") == "median":
        delta, control = delta - np.nanmedian(delta), control - np.nanmedian(control)

    grid = sorted(cfg["thresholds"])
    p99 = float(np.nanpercentile(np.abs(control), 99))
    t = cfg["primary_threshold"] if not isinstance(cfg["primary_threshold"], str) else min(x for x in grid if x >= p99)

    inc, dec = np.nan_to_num(delta) > t, np.nan_to_num(delta) < -t
    if cfg.get("exclude_water_from_change"):
        water = (band(items["before_item"], "scl", bounds, shape) == 6) | (band(items["after_item"], "scl", bounds, shape) == 6)
        inc, dec = inc & ~water, dec & ~water
    min_px = math.ceil(cfg.get("min_patch_ha", 1.0) * 10_000 / px_area)
    ctrl_valid = np.isfinite(control)

    mine = {
        "joint_valid_pixels_main": int(np.isfinite(delta).sum()),
        "joint_valid_pixels_control": int(ctrl_valid.sum()),
        "threshold": float(t),
        "increase_area_ha": area_in_patches(inc, min_px) * px_area / 10_000,
        "decrease_area_ha": area_in_patches(dec, min_px) * px_area / 10_000,
        "control_flagged_share_at_threshold": float((np.abs(control[ctrl_valid]) > t).mean()),
    }
    published = {
        "joint_valid_pixels_main": res["coverage"]["joint_valid_pixels_main"],
        "joint_valid_pixels_control": res["coverage"]["joint_valid_pixels_control"],
        "threshold": res["threshold"]["value"],
        "increase_area_ha": res["change"]["increase_area_ha"],
        "decrease_area_ha": res["change"]["decrease_area_ha"],
        "control_flagged_share_at_threshold": res["change"]["control_flagged_share_at_threshold"],
    }
    rows, ok = [], True
    for k in mine:
        same = math.isclose(mine[k], published[k], rel_tol=1e-6, abs_tol=1e-9)
        ok &= same
        rows.append({"quantity": k, "independent": mine[k], "published": published[k], "match": same})
        print(f"{'OK ' if same else 'BAD'} {k:38} independent={mine[k]:<14.6g} published={published[k]:.6g}")

    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()  # nosec B603 B607
    except Exception:
        commit = "unknown"
    report = {
        "schema": "tesis.case_study.independent_check.v1",
        "data_status": "observation_derived_result",
        "case_id": cfg["case_id"],
        "checked_run_id": res["run_id"],
        "checked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "code_commit": commit,
        "command": "python pipeline/verify_independent.py " + Path(cfg_path).as_posix(),
        "method": "Second implementation sharing no code with the pipeline; reads STAC items over plain HTTP and the public COGs directly.",
        "shared_inputs": ["config file", "AOI grid bounds from results.json"],
        "all_match": bool(ok),
        "comparisons": rows,
        "runtime_seconds": round(time.time() - t0, 1),
    }
    (pub / "independent_check.json").write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print("ALL MATCH" if ok else "MISMATCH", f"({report['runtime_seconds']} s)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
