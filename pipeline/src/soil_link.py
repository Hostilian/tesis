"""Link laboratory soil results to Sentinel-2 bare-soil reflectance.

Purpose (exploratory, not a replacement for the laboratory):
    For each soil sample with coordinates and a sampling date, read the
    Sentinel-2 L2A pixels around the point on cloud-free dates when the field
    was bare, build one spectral feature row per sample, then test whether any
    laboratory property (organic carbon, clay, pH, ...) can be predicted from
    those features better than chance.

Why the evaluation is strict:
    Satellite pixels close to each other look alike, and soil samples close
    to each other are alike too. Ordinary random cross-validation then
    "predicts" a sample from its neighbour and reports inflated scores.
    This module therefore uses
      1. spatial block cross-validation (whole blocks of km x km are held out),
      2. a mean-only baseline every model must beat,
      3. a permutation test: the labels are shuffled many times and the model
         is re-evaluated; the real score must beat almost all shuffled scores,
      4. Benjamini-Hochberg correction when many feature-property pairs are
         screened, so that 1 in 20 random "significant" pairs is not reported.

Data status:
    - Features from real STAC scenes: ``observation_derived_result``.
    - Laboratory values belong to whoever provided them. Private results
      (e.g. a farm's laboratory reports) stay outside this public repository;
      only aggregated, non-identifying metrics may be published, and only with
      permission.
    - ``synthetic_demo`` data is labelled ``synthetic_demonstration`` and is
      never evidence.

Sentinel-2 sees the top millimetres of the soil surface, and only when the
surface is bare and dry enough. Expect moderate skill at best for organic
carbon and clay, and little or none for nutrients such as N, P and K.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np

from . import case_study as cs

SOIL_BANDS = (
    "blue",
    "green",
    "red",
    "rededge1",
    "rededge2",
    "rededge3",
    "nir",
    "nir08",
    "swir16",
    "swir22",
)
INDEX_NAMES = ("ndvi", "nbr2", "bsi", "clay_ratio", "iron_ratio")
FEATURE_NAMES = SOIL_BANDS + INDEX_NAMES
TERRAIN_NAMES = ("elevation_m", "slope_deg")
# SCL classes: 4 vegetation, 5 not vegetated. Bare soil is then decided by
# NDVI and NBR2 thresholds, not by SCL alone.
SOIL_SCL = (4, 5)
REQUIRED_COLUMNS = ("sample_id", "lat", "lon", "date")
# Bare-soil rule. Published bare-soil composites use low NDVI plus a low NBR2
# (NBR2 rises with moisture and crop residue); exact cut-offs differ between
# studies, so both are parameters and their sensitivity must be reported.
NDVI_MAX = 0.25
NBR2_MAX = 0.125


# ---------------------------------------------------------------------------
# Input: laboratory samples
# ---------------------------------------------------------------------------


@dataclass
class Sample:
    sample_id: str
    lat: float
    lon: float
    when: date
    values: dict[str, float] = field(default_factory=dict)


def read_samples(path: Path) -> list[Sample]:
    """Read a lab CSV: sample_id, lat, lon, date (YYYY-MM-DD) + numeric columns.

    Non-numeric or empty property cells become missing (NaN), never zero.
    """
    out = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: missing required columns {missing}")
        for row in reader:
            lat, lon = float(row["lat"]), float(row["lon"])
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError(f"sample {row['sample_id']}: invalid lat/lon")
            vals = {}
            for k, v in row.items():
                if k in REQUIRED_COLUMNS or k is None:
                    continue
                try:
                    vals[k] = float(v) if v not in ("", None) else math.nan
                except ValueError:
                    vals[k] = math.nan
            out.append(
                Sample(
                    row["sample_id"],
                    lat,
                    lon,
                    date.fromisoformat(row["date"][:10]),
                    vals,
                )
            )
    if not out:
        raise ValueError(f"{path}: no samples")
    return out


# ---------------------------------------------------------------------------
# Pure spectral functions (offline-testable)
# ---------------------------------------------------------------------------


def spectral_indices(b: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    nd = cs.normalized_difference
    with np.errstate(divide="ignore", invalid="ignore"):
        clay = np.where(b["swir22"] > 1e-6, b["swir16"] / b["swir22"], np.nan)
        iron = np.where(b["blue"] > 1e-6, b["red"] / b["blue"], np.nan)
    return {
        "ndvi": nd(b["nir"], b["red"]),
        "nbr2": nd(b["swir16"], b["swir22"]),
        "bsi": nd(b["swir16"] + b["red"], b["nir"] + b["blue"]),
        "clay_ratio": clay.astype("float32"),
        "iron_ratio": iron.astype("float32"),
    }


def bare_soil_mask(
    bands: Mapping[str, np.ndarray],
    scl: np.ndarray,
    ndvi_max: float = NDVI_MAX,
    nbr2_max: float = NBR2_MAX,
) -> np.ndarray:
    """Pixels that are cloud-free, valid and bare (low NDVI, low NBR2).

    Low NDVI removes green vegetation; low NBR2 also removes wet soil and
    crop residue. Both cut-offs are parameters so their sensitivity can be
    reported.
    """
    idx = spectral_indices(bands)
    m = cs.scl_valid_mask(scl, SOIL_SCL)
    for arr in bands.values():
        m &= np.isfinite(arr)
    m &= np.isfinite(idx["ndvi"]) & (idx["ndvi"] <= ndvi_max)
    m &= np.isfinite(idx["nbr2"]) & (idx["nbr2"] <= nbr2_max)
    return m


def composite_features(
    scenes: Sequence[tuple[Mapping[str, np.ndarray], np.ndarray]],
    ndvi_max: float = NDVI_MAX,
    nbr2_max: float = NBR2_MAX,
    min_pixels: int = 3,
) -> tuple[dict[str, float], int, int]:
    """Median of bare-soil pixels over all scenes -> one feature row.

    Returns (features, n_bare_pixels, n_scenes_used). Features are NaN when
    fewer than ``min_pixels`` bare pixels were found (never filled with zero).
    """
    stacks: dict[str, list[np.ndarray]] = {k: [] for k in SOIL_BANDS}
    used = 0
    for bands, scl in scenes:
        m = bare_soil_mask(bands, scl, ndvi_max, nbr2_max)
        if m.any():
            used += 1
            for k in SOIL_BANDS:
                stacks[k].append(bands[k][m])
    n = int(sum(len(v) for v in stacks["red"]))
    if n < min_pixels:
        return {k: math.nan for k in FEATURE_NAMES}, n, used
    med = {
        k: np.asarray([float(np.median(np.concatenate(stacks[k])))]) for k in SOIL_BANDS
    }
    feats = {k: float(v[0]) for k, v in med.items()}
    for k, v in spectral_indices(med).items():
        feats[k] = float(v[0])
    return feats, n, used


# ---------------------------------------------------------------------------
# Network: Sentinel-2 scenes around each sample (Earth Search, no key)
# ---------------------------------------------------------------------------


def soil_item_meta(item: Any) -> dict[str, Any]:
    """Like case_study.item_metadata, for all soil bands. Never guesses calibration."""
    p = item.properties
    applied = bool(p.get("earthsearch:boa_offset_applied"))
    assets = {}
    for key in SOIL_BANDS + ("scl",):
        if key not in item.assets:
            raise ValueError(f"{item.id}: asset {key} missing")
        a = item.assets[key]
        rb = (a.extra_fields.get("raster:bands") or [{}])[0]
        if key != "scl" and ("scale" not in rb or "offset" not in rb):
            raise ValueError(
                f"{item.id}/{key}: scale/offset missing; refusing to guess"
            )
        assets[key] = {
            "href": a.href,
            "scale": rb.get("scale", 1.0),
            "offset": cs.effective_offset(float(rb.get("offset", 0.0) or 0.0), applied),
            "nodata": rb.get("nodata"),
        }
    return {"id": item.id, "datetime": p.get("datetime"), "assets": assets}


def point_bbox(lat: float, lon: float, half_m: float = 30.0) -> list[float]:
    dlat = half_m / 111_320.0
    dlon = half_m / (111_320.0 * max(math.cos(math.radians(lat)), 1e-6))
    return [lon - dlon, lat - dlat, lon + dlon, lat + dlat]


def read_point_scene(
    meta: Mapping[str, Any], lat: float, lon: float, half_m: float = 30.0
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    grid = cs.reference_grid(meta, point_bbox(lat, lon, half_m))
    bands = {}
    for k in SOIL_BANDS:
        a = meta["assets"][k]
        bands[k] = cs.to_reflectance(
            cs.read_band(a, grid), a["scale"], a["offset"], a.get("nodata", 0)
        )
    scl = cs.read_band(meta["assets"]["scl"], grid)
    return bands, scl


def search_scenes(
    lat: float,
    lon: float,
    when: date,
    window_days: int,
    max_cloud: float,
    max_items: int,
) -> list[Any]:
    search = cs.open_catalog().search(
        collections=[cs.COLLECTION],
        intersects={"type": "Point", "coordinates": [lon, lat]},
        datetime=f"{(when - timedelta(days=window_days)).isoformat()}/"
        f"{(when + timedelta(days=window_days)).isoformat()}",
        query={"eo:cloud_cover": {"lt": max_cloud}},
        max_items=500,
    )
    items = list(search.items())
    return spread_by_month(items, when, max_items)


def spread_by_month(
    items: Sequence[Any], when: date, max_items: int, per_month: int = 2
) -> list[Any]:
    """Closest dates first, but at most ``per_month`` scenes per calendar month.

    Checked on 2026-11-27 at three dryland points near Castro Verde: in July
    and August the surface is SCL "not vegetated" with NDVI about 0.2, but NBR2
    is 0.22-0.27, i.e. dry straw and stubble rather than bare soil. Bare soil
    appears after tillage, usually in autumn. Taking only the scenes closest
    to a summer sampling date would therefore find no bare soil at all;
    spreading the scenes over the year gives every season a chance.
    """

    def key(it: Any) -> int:
        return abs(
            (date.fromisoformat(str(it.properties["datetime"])[:10]) - when).days
        )

    chosen: list[Any] = []
    per: dict[str, int] = {}
    for it in sorted(items, key=key):
        month = str(it.properties["datetime"])[:7]
        if per.get(month, 0) < per_month:
            chosen.append(it)
            per[month] = per.get(month, 0) + 1
        if len(chosen) >= max_items:
            break
    return chosen


DEM_COLLECTION = "cop-dem-glo-30"


def terrain_at(lat: float, lon: float, half_m: float = 60.0) -> dict[str, float]:
    """Elevation and slope from the Copernicus DEM GLO-30 (Earth Search, no key).

    Terrain controls erosion, water and soil depth, so it is a standard soil
    covariate next to the spectra. Returns NaN values if unavailable.
    """
    import rasterio
    from rasterio.warp import transform_bounds
    from rasterio.windows import from_bounds

    out = {"elevation_m": math.nan, "slope_deg": math.nan}
    try:
        items = list(
            cs.open_catalog()
            .search(
                collections=[DEM_COLLECTION],
                intersects={"type": "Point", "coordinates": [lon, lat]},
                max_items=1,
            )
            .items()
        )
        if not items:
            return out
        href = items[0].assets["data"].href
        with cs._gdal_env(), rasterio.open(href) as ds:
            b = transform_bounds("EPSG:4326", ds.crs, *point_bbox(lat, lon, half_m))
            z = ds.read(
                1,
                window=from_bounds(*b, transform=ds.transform),
                boundless=True,
                fill_value=np.nan,
            ).astype(float)
            if z.size == 0 or not np.isfinite(z).any():
                return out
            px = abs(ds.transform.a) * 111_320.0 * math.cos(math.radians(lat))
            py = abs(ds.transform.e) * 111_320.0
            if z.shape[0] > 1 and z.shape[1] > 1:
                gy, gx = np.gradient(z, py, px)
                out["slope_deg"] = float(
                    np.nanmedian(np.degrees(np.arctan(np.hypot(gx, gy))))
                )
            out["elevation_m"] = float(np.nanmedian(z))
    except Exception:  # noqa: BLE001 - terrain is optional
        pass
    return out


SceneSearch = Callable[[Sample], list[Any]]
SceneReader = Callable[[Any, Sample], tuple[dict[str, np.ndarray], np.ndarray]]


def extract_features(
    samples: Sequence[Sample],
    search: SceneSearch | None = None,
    reader: SceneReader | None = None,
    window_days: int = 60,
    max_cloud: float = 20.0,
    max_scenes: int = 8,
    half_m: float = 30.0,
    log: Callable[[str], None] = print,
    terrain: Callable[[float, float], dict[str, float]] | None = terrain_at,
    workers: int = 1,
    ndvi_max: float = NDVI_MAX,
    nbr2_max: float = NBR2_MAX,
) -> list[dict[str, Any]]:
    """One row per sample: features + provenance (scene ids). Never raises per sample.

    The work is network-bound (small windows read from cloud-optimised
    GeoTIFFs), so ``workers`` > 1 runs several samples at once in threads.
    Output order always follows the input order.
    """
    if search is None:

        def search(s: Sample) -> list[Any]:  # noqa: E306
            return search_scenes(
                s.lat, s.lon, s.when, window_days, max_cloud, max_scenes
            )

    if reader is None:

        def reader(
            item: Any, s: Sample
        ) -> tuple[dict[str, np.ndarray], np.ndarray]:  # noqa: E306
            return read_point_scene(soil_item_meta(item), s.lat, s.lon, half_m)

    def one(s: Sample) -> dict[str, Any]:
        scenes, ids, errors = [], [], []
        try:
            for item in search(s):
                try:
                    scenes.append(reader(item, s))
                    ids.append(getattr(item, "id", str(item)))
                except Exception as exc:  # noqa: BLE001 - record and continue
                    errors.append(f"{getattr(item, 'id', item)}: {type(exc).__name__}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"search: {type(exc).__name__}: {exc}"[:200])
        feats, n_px, used = composite_features(scenes, ndvi_max, nbr2_max)
        topo = terrain(s.lat, s.lon) if terrain else {}
        row = {
            "sample_id": s.sample_id,
            **feats,
            **topo,
            "n_bare_pixels": n_px,
            "n_scenes_used": used,
            "scene_ids": ";".join(ids),
            "errors": " | ".join(errors),
        }
        log(
            f"{s.sample_id}: {used} bare scenes, {n_px} px"
            + (f", {len(errors)} errors" if errors else "")
        )
        return row

    if workers <= 1:
        return [one(s) for s in samples]
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(one, samples))


# ---------------------------------------------------------------------------
# Statistics (offline-testable)
# ---------------------------------------------------------------------------


def spatial_blocks(
    lat: Sequence[float], lon: Sequence[float], block_km: float
) -> np.ndarray:
    """Integer block id per sample on an approx. equal-distance km grid."""
    lat_a, lon_a = np.asarray(lat, float), np.asarray(lon, float)
    lat0 = float(np.mean(lat_a))
    y = lat_a * 111.32 / block_km
    x = lon_a * 111.32 * math.cos(math.radians(lat0)) / block_km
    keys = [f"{int(math.floor(a))}_{int(math.floor(b))}" for a, b in zip(x, y)]
    uniq = {k: i for i, k in enumerate(sorted(set(keys)))}
    return np.asarray([uniq[k] for k in keys])


def fdr_bh(pvals: Sequence[float]) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values (q-values)."""
    p = np.asarray(pvals, float)
    n = len(p)
    if n == 0:
        return p
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.clip(q, 0, 1)
    return out


def univariate_screen(
    X: np.ndarray, y: np.ndarray, names: Sequence[str]
) -> list[dict[str, float | str]]:
    """Spearman correlation of each feature with the property, FDR-corrected."""
    from scipy.stats import spearmanr

    rows = []
    for j, name in enumerate(names):
        ok = np.isfinite(X[:, j]) & np.isfinite(y)
        if ok.sum() < 5 or np.nanstd(X[ok, j]) == 0:
            rows.append(
                {"feature": name, "n": int(ok.sum()), "rho": math.nan, "p": math.nan}
            )
            continue
        r = spearmanr(X[ok, j], y[ok])
        rows.append(
            {
                "feature": name,
                "n": int(ok.sum()),
                "rho": float(r.statistic),
                "p": float(r.pvalue),
            }
        )
    finite = [i for i, r in enumerate(rows) if np.isfinite(r["p"])]
    q = fdr_bh([rows[i]["p"] for i in finite])
    for i, qi in zip(finite, q):
        rows[i]["q_fdr"] = float(qi)
    return rows


def _metrics(y: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    resid = y - pred
    ss_res = float(np.sum(resid**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    rmse = math.sqrt(ss_res / len(y))
    iqr = float(np.subtract(*np.percentile(y, [75, 25])))
    return {
        "r2": 1 - ss_res / ss_tot if ss_tot > 0 else math.nan,
        "rmse": rmse,
        "mae": float(np.mean(np.abs(resid))),
        "rpiq": iqr / rmse if rmse > 0 else math.nan,
    }


def make_models(seed: int = 0) -> dict[str, Any]:
    from sklearn.dummy import DummyRegressor
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import RidgeCV
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    from sklearn.cross_decomposition import PLSRegression
    from sklearn.ensemble import HistGradientBoostingRegressor

    class _PLS(PLSRegression):
        def predict(self, X, copy=True):  # 1-D output like the others
            return np.ravel(super().predict(X, copy=copy))

    # Four different families, so the result does not hinge on one model:
    # linear (ridge), latent-factor (PLS, the classic in soil spectroscopy),
    # bagged trees (random forest), boosted trees (gradient boosting).
    return {
        "baseline_mean": DummyRegressor(strategy="mean"),
        "ridge": make_pipeline(
            StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13))
        ),
        "pls": make_pipeline(StandardScaler(), _PLS(n_components=3)),
        "random_forest": RandomForestRegressor(
            n_estimators=300, min_samples_leaf=3, random_state=seed, n_jobs=-1
        ),
        "gradient_boosting": HistGradientBoostingRegressor(
            max_iter=200, learning_rate=0.05, min_samples_leaf=10, random_state=seed
        ),
    }


def cross_validated_predictions(
    model: Any, X: np.ndarray, y: np.ndarray, groups: np.ndarray, n_splits: int
) -> np.ndarray:
    from sklearn.base import clone
    from sklearn.model_selection import GroupKFold

    pred = np.full(len(y), np.nan)
    for tr, te in GroupKFold(n_splits=n_splits).split(X, y, groups):
        m = clone(model).fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
    return pred


def evaluate_property(
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    names: Sequence[str],
    n_splits: int = 5,
    n_permutations: int = 99,
    seed: int = 0,
    models: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Spatial-block CV for each model + permutation test on the best model."""
    ok = np.isfinite(y) & np.all(np.isfinite(X), axis=1)
    X, y, groups = X[ok], y[ok], groups[ok]
    n_groups = len(np.unique(groups))
    k = min(n_splits, n_groups)
    if len(y) < 20 or k < 2:
        return {
            "status": "too_few_samples",
            "n": int(len(y)),
            "n_blocks": int(n_groups),
        }
    models = dict(models or make_models(seed))
    preds = {
        name: cross_validated_predictions(m, X, y, groups, k)
        for name, m in models.items()
    }
    results = {name: _metrics(y, pr) for name, pr in preds.items()}
    candidates = {n: r for n, r in results.items() if n != "baseline_mean"}
    best = max(candidates, key=lambda n: candidates[n]["r2"])
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(n_permutations):
        yp = rng.permutation(y)
        null.append(
            _metrics(yp, cross_validated_predictions(models[best], X, yp, groups, k))[
                "r2"
            ]
        )
    null_a = np.asarray(null)
    real = results[best]["r2"]
    p_perm = (int(np.sum(null_a >= real)) + 1) / (n_permutations + 1)
    beats_baseline = real > results["baseline_mean"]["r2"]
    return {
        "status": "ok",
        "n": int(len(y)),
        "n_blocks": int(n_groups),
        "cv_folds": int(k),
        "models": results,
        "best_model": best,
        "interval_80_halfwidth": prediction_interval_halfwidth(y, preds[best], 0.8),
        "models_beating_baseline": sorted(
            n for n, r in candidates.items() if r["r2"] > results["baseline_mean"]["r2"]
        ),
        "permutation": {
            "n_permutations": n_permutations,
            "null_r2_p95": float(np.percentile(null_a, 95)),
            "p_value": p_perm,
        },
        "screen": univariate_screen(X, y, names),
        "verdict": (
            "signal_above_chance"
            if (p_perm <= 0.05 and beats_baseline and real > 0)
            else "no_evidence_of_signal"
        ),
    }


def area_of_applicability(
    X_train: np.ndarray, X_new: np.ndarray, groups: np.ndarray | None = None
) -> dict[str, Any]:
    """Dissimilarity index (Meyer & Pebesma 2021, simplified, unweighted).

    For a new location, DI = distance to the nearest training sample in
    standardised feature space, divided by the mean distance between training
    samples. The threshold is the upper whisker (Q3 + 1.5 IQR) of the training
    DIs, each computed against samples outside its own block. New locations
    above it are outside the area of applicability: the model has never seen
    anything like them and its prediction there should not be used.
    """
    mu = np.nanmean(X_train, axis=0)
    sd = np.nanstd(X_train, axis=0)
    sd[sd == 0] = 1.0
    A = (X_train - mu) / sd
    B = (X_new - mu) / sd
    d_train = np.sqrt(((A[:, None, :] - A[None, :, :]) ** 2).sum(-1))
    n = len(A)
    mean_d = float(d_train[np.triu_indices(n, 1)].mean()) if n > 1 else 1.0
    g = np.arange(n) if groups is None else np.asarray(groups)
    di_train = np.empty(n)
    for i in range(n):
        other = g != g[i]
        di_train[i] = d_train[i, other].min() / mean_d if other.any() else np.nan
    q1, q3 = np.nanpercentile(di_train, [25, 75])
    thr = float(q3 + 1.5 * (q3 - q1))
    d_new = np.sqrt(((B[:, None, :] - A[None, :, :]) ** 2).sum(-1)).min(axis=1) / mean_d
    return {
        "threshold": thr,
        "di_new": d_new,
        "inside": d_new <= thr,
        "share_inside": float(np.mean(d_new <= thr)) if len(d_new) else math.nan,
    }


def prediction_interval_halfwidth(
    y: np.ndarray, pred: np.ndarray, coverage: float = 0.8
) -> float:
    """Split-conformal style: the |residual| quantile from spatial CV.
    Predicted value +- this number covers about ``coverage`` of new samples
    (from areas similar to the training data)."""
    r = np.abs(y - pred)
    r = r[np.isfinite(r)]
    n = len(r)
    k = min(n, int(math.ceil((n + 1) * coverage)))
    return float(np.sort(r)[k - 1]) if n else math.nan


def samples_needed(r: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """Samples needed to detect a correlation r (two-sided, Fisher z)."""
    from scipy.stats import norm

    if not 0 < abs(r) < 1:
        raise ValueError("r must be in (0, 1)")
    z = norm.ppf(1 - alpha / 2) + norm.ppf(power)
    return int(math.ceil((z / math.atanh(abs(r))) ** 2 + 3))


# ---------------------------------------------------------------------------
# Synthetic demonstration (labelled; used to prove the method can find a
# planted signal and does NOT invent one when there is none)
# ---------------------------------------------------------------------------


def synthetic_dataset(
    n: int = 200, signal: float = 1.0, seed: int = 0
) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray, np.ndarray]:
    """Spatially clustered fake samples. ``signal=0`` gives a property that is
    pure spatial noise, unrelated to the spectra: a correct method must then
    report no evidence of signal."""
    rng = np.random.default_rng(seed)
    centres = rng.uniform([38.0, -8.2], [38.6, -7.6], size=(max(n // 10, 2), 2))
    c = rng.integers(0, len(centres), n)
    lat = centres[c, 0] + rng.normal(0, 0.01, n)
    lon = centres[c, 1] + rng.normal(0, 0.01, n)
    X = rng.normal(0.25, 0.05, size=(n, len(FEATURE_NAMES)))
    cluster_effect = rng.normal(0, 1, len(centres))[c]
    soc = (
        12
        + signal * 40 * (X[:, FEATURE_NAMES.index("swir16")] - 0.25)
        + cluster_effect
        + rng.normal(0, 0.5, n)
    )
    return X, {"soc_g_kg": soc}, lat, lon


def iter_targets(samples: Iterable[Sample]) -> list[str]:
    keys: dict[str, None] = {}
    for s in samples:
        for k in s.values:
            keys[k] = None
    return list(keys)
