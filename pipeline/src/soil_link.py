"""Link laboratory soil results to Sentinel-2 bare-soil reflectance.

Purpose (exploratory, not a replacement for the laboratory):
    For each soil sample with coordinates and a sampling date, read the
    Sentinel-2 L2A pixels around the point on cloud-free dates when the field
    was bare, build one spectral feature row per sample, then test whether a
    laboratory property (organic carbon, clay, ...) can be predicted from those
    features better than chance AND better than location alone.

Why the evaluation is strict (independent review, 27 Nov 2026):
    Soil properties and satellite features are both smooth in space. Two maps
    that have nothing to do with each other can then still "predict" each
    other, because nearby samples look alike on both. The review showed the
    first version of this module reporting a signal in 3 of 3 such unrelated
    synthetic landscapes. The evaluation now has these guards:
      1. spatial block cross-validation (whole km x km blocks held out);
      2. a mean-only baseline every model must beat;
      3. a location-only model (coordinates, no spectra): the spectra must add
         skill on top of location, otherwise the "signal" may just be geography;
      4. a restricted permutation test: labels are shuffled only WITHIN local
         strata, so the large-scale spatial pattern survives in the null data,
         and every permutation repeats the model choice (best of all models),
         so picking the best model cannot inflate the result;
      5. Benjamini-Hochberg correction when many features or properties are
         screened;
      6. an area-of-applicability check before any prediction for a new place.

Data status:
    - Features from real STAC scenes: ``observation_derived_result``.
    - Laboratory values belong to whoever provided them. Private results stay
      outside this public repository; only aggregated, non-identifying metrics
      may be published, and only with permission.
    - Synthetic scenarios are labelled ``synthetic_demonstration`` and are
      never evidence about real soil.

Privacy:
    The catalogue search sends only a coarse 0.1 degree cell (about 10 km), not
    the sample coordinate. Reading pixels still fetches byte ranges of public
    image files around each sample, so a log of those requests could reveal
    roughly where samples are. Use a machine and network you are allowed to
    use for the data, and never publish coordinates.

Sentinel-2 sees the top millimetres of the soil surface, and only when the
surface is bare and dry enough. Expect moderate skill at best for organic
carbon, clay and iron, and none for plant-available P and K (use those as
negative controls).
"""

from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence, cast

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
# Cloud shadow, cloud medium/high probability, thin cirrus: buffered.
CLOUDY_SCL = (3, 8, 9, 10)
CLOUD_BUFFER_PX = 2  # 20 m at 10 m pixels
REQUIRED_COLUMNS = ("sample_id", "lat", "lon", "date")
# Columns describing a sample, never evaluated as soil properties.
METADATA_COLUMNS = {
    "depth",
    "depth_cm",
    "depth_top_cm",
    "depth_bottom_cm",
    "method",
    "lab",
    "unit",
    "units",
    "notes",
    "note",
    "comment",
    "crs",
    "field_id",
    "site",
    "x",
    "y",
}
# Bare-soil rule. Published bare-soil composites use low NDVI plus a low NBR2
# (NBR2 rises with moisture and crop residue); exact cut-offs differ between
# studies, so both are parameters and their sensitivity must be reported.
NDVI_MAX = 0.25
NBR2_MAX = 0.125
# At least 3 distinct 20 m SWIR pixels = 12 pixels on the 10 m grid.
MIN_BARE_PIXELS = 12


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
    meta: dict[str, str] = field(default_factory=dict)
    censored: set[str] = field(default_factory=set)


def parse_lab_value(text: str | None) -> tuple[float, bool]:
    """Parse one laboratory cell. Returns (value, censored).

    Accepts a decimal comma ("12,5"). Values below or above a detection limit
    ("<5", ">200") are censored: returned as NaN with censored=True, so they
    are counted and reported instead of silently vanishing.
    """
    if text is None:
        return math.nan, False
    t = text.strip().replace(" ", "").replace(" ", "")
    if t == "" or t.upper() in {"NA", "N/A", "NAN", "-", "ND"}:
        return math.nan, False
    if t[0] in "<>":
        return math.nan, True
    if re.fullmatch(r"-?\d+,\d+", t):
        t = t.replace(",", ".")
    try:
        return float(t), False
    except ValueError:
        raise ValueError(f"cannot read laboratory value {text!r}") from None


def read_samples(path: Path) -> list[Sample]:
    """Read a lab CSV: sample_id, lat, lon, date (YYYY-MM-DD) + property columns.

    Raises on duplicate sample ids, invalid coordinates and unreadable values,
    so nothing is lost silently. Metadata columns (depth, method, unit, ...)
    are kept in ``Sample.meta`` and never treated as properties.
    """
    out: list[Sample] = []
    seen: set[str] = set()
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        cols = reader.fieldnames or []
        missing = [c for c in REQUIRED_COLUMNS if c not in cols]
        if missing:
            raise ValueError(f"{path}: missing required columns {missing}")
        for line, row in enumerate(reader, start=2):
            sid = (row["sample_id"] or "").strip()
            if not sid:
                raise ValueError(f"{path}:{line}: empty sample_id")
            if sid in seen:
                raise ValueError(f"{path}:{line}: duplicate sample_id {sid!r}")
            seen.add(sid)
            lat = parse_lab_value(row["lat"])[0]
            lon = parse_lab_value(row["lon"])[0]
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError(f"sample {sid}: invalid lat/lon")
            vals, meta, cens = {}, {}, set()
            for k, v in row.items():
                if k is None or k in REQUIRED_COLUMNS:
                    continue
                if k.strip().lower() in METADATA_COLUMNS:
                    meta[k] = v or ""
                    continue
                try:
                    val, is_cens = parse_lab_value(v)
                except ValueError as exc:
                    raise ValueError(f"{path}:{line} column {k}: {exc}") from None
                vals[k] = val
                if is_cens:
                    cens.add(k)
            out.append(
                Sample(
                    sid,
                    lat,
                    lon,
                    date.fromisoformat(row["date"].strip()[:10]),
                    vals,
                    meta,
                    cens,
                )
            )
    if not out:
        raise ValueError(f"{path}: no samples")
    return out


def iter_targets(samples: Iterable[Sample]) -> list[str]:
    keys: dict[str, None] = {}
    for s in samples:
        for k in s.values:
            if k.strip().lower() not in METADATA_COLUMNS:
                keys[k] = None
    return list(keys)


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
    cloud_buffer_px: int = CLOUD_BUFFER_PX,
) -> np.ndarray:
    """Pixels that are cloud-free, valid, physically plausible and bare.

    - SCL vegetation / not-vegetated only, and at least ``cloud_buffer_px``
      pixels away from cloud, cloud shadow or cirrus (cloud edges are often
      missed by SCL);
    - every band finite and non-negative (negative reflectance is an artefact);
    - NDVI <= ndvi_max (no green vegetation) and NBR2 <= nbr2_max (no wet soil,
      straw or crop residue).
    """
    from scipy import ndimage

    idx = spectral_indices(bands)
    m = cs.scl_valid_mask(scl, SOIL_SCL)
    cloudy = np.isin(scl, CLOUDY_SCL)
    if cloud_buffer_px > 0 and cloudy.any() and scl.ndim == 2:
        # Square structuring element: diagonal neighbours of a cloud count too.
        cloudy = ndimage.binary_dilation(
            cloudy, structure=np.ones((3, 3), bool), iterations=cloud_buffer_px
        )
    m &= ~cloudy
    for arr in bands.values():
        m &= np.isfinite(arr) & (arr >= 0)
    m &= np.isfinite(idx["ndvi"]) & (idx["ndvi"] <= ndvi_max)
    m &= np.isfinite(idx["nbr2"]) & (idx["nbr2"] <= nbr2_max)
    return m


def composite_features(
    scenes: Sequence[tuple[Mapping[str, np.ndarray], np.ndarray]],
    ndvi_max: float = NDVI_MAX,
    nbr2_max: float = NBR2_MAX,
    min_pixels: int = MIN_BARE_PIXELS,
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
    return {
        "id": item.id,
        "datetime": p.get("datetime"),
        "processing_baseline": p.get("s2:processing_baseline"),
        "sun_elevation": p.get("view:sun_elevation"),
        "assets": assets,
    }


def point_bbox(lat: float, lon: float, half_m: float = 30.0) -> list[float]:
    """WGS84 box of +-half_m around a point. The reader snaps it outward to even
    10 m pixels, so the window read is up to 20 m larger on each axis."""
    dlat = half_m / 111_320.0
    dlon = half_m / (111_320.0 * max(math.cos(math.radians(lat)), 1e-6))
    return [lon - dlon, lat - dlat, lon + dlon, lat + dlat]


def coarse_cell(lat: float, lon: float, step: float = 0.1) -> list[float]:
    """The 0.1 degree grid cell containing the point (privacy for the search)."""
    x0 = math.floor(lon / step) * step
    y0 = math.floor(lat / step) * step
    return [round(x0, 6), round(y0, 6), round(x0 + step, 6), round(y0 + step, 6)]


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


def _item_contains(item: Any, lat: float, lon: float) -> bool:
    geom = getattr(item, "geometry", None)
    if not geom:
        return True
    from shapely.geometry import Point, shape

    return bool(shape(geom).contains(Point(lon, lat)))


def dedupe_overpasses(items: Sequence[Any]) -> list[Any]:
    """One item per acquisition day and tile.

    Earth Search keeps both the original and the reprocessed copy of many
    2017-2021 overpasses (e.g. ..._0_L2A baseline 02.xx and ..._1_L2A baseline
    05.00). Counting both would double-count one day and mix processing
    versions. Keep the highest processing baseline.
    """
    best: dict[tuple[str, str], Any] = {}

    def baseline(it: Any) -> float:
        try:
            return float(it.properties.get("s2:processing_baseline") or 0)
        except (TypeError, ValueError):
            return 0.0

    for it in items:
        p = it.properties
        tile = f"{p.get('mgrs:utm_zone')}{p.get('mgrs:latitude_band')}{p.get('mgrs:grid_square')}"
        key = (str(p["datetime"])[:10], tile)
        if key not in best or baseline(it) > baseline(best[key]):
            best[key] = it
    return list(best.values())


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
        bbox=coarse_cell(lat, lon),
        datetime=f"{(when - timedelta(days=window_days)).isoformat()}/"
        f"{(when + timedelta(days=window_days)).isoformat()}",
        query={"eo:cloud_cover": {"lt": max_cloud}},
        max_items=1000,
    )
    items = [it for it in search.items() if _item_contains(it, lat, lon)]
    return spread_by_month(dedupe_overpasses(items), when, max_items)


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
    covariate next to the spectra. Returns NaN values (and the error) if
    unavailable; the evaluation then reports how many samples lack terrain.
    """
    import rasterio
    from rasterio.warp import transform_bounds
    from rasterio.windows import from_bounds

    out: dict[str, Any] = {"elevation_m": math.nan, "slope_deg": math.nan}
    for attempt in range(3):
        try:
            items = [
                it
                for it in cs.open_catalog()
                .search(
                    collections=[DEM_COLLECTION],
                    bbox=coarse_cell(lat, lon),
                    max_items=20,
                )
                .items()
                if _item_contains(it, lat, lon)
            ]
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
            return out
        except Exception as exc:  # noqa: BLE001 - terrain is optional
            out["terrain_error"] = f"{type(exc).__name__}"
            if attempt < 2:
                import time

                time.sleep(2 * (attempt + 1))
    return out


# ---------------------------------------------------------------------------
# SoilGrids 250 m: a public baseline to beat (not training data, not truth)
# ---------------------------------------------------------------------------

SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
SOILGRIDS_LICENCE = (
    "SoilGrids 2.0, ISRIC - World Soil Information, licence CC-BY 4.0 "
    "(attribution required). Poggio et al. (2021) SOIL 7, 217-240, "
    "doi:10.5194/soil-7-217-2021."
)


def _http_json(url: str, params: Sequence[tuple[str, str]], timeout: float) -> Any:
    import json
    import urllib.parse
    import urllib.request

    req = urllib.request.Request(
        f"{url}?{urllib.parse.urlencode(list(params))}",
        headers={
            "User-Agent": "soil-link-research-client",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def soilgrids_point(
    lat: float,
    lon: float,
    properties: Sequence[str] = ("soc", "clay"),
    depth: str = "0-5cm",
    value: str = "mean",
    transport: Callable[[str, Sequence[tuple[str, str]], float], Any] | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """SoilGrids v2.0 values at one point (public REST API, no key).

    Returns ``{prop: {"value", "unit", "mapped_value", "mapped_unit"}}`` plus
    provenance. Values are converted from SoilGrids' integer "mapped units"
    with the ``d_factor`` that the API returns (soc: dg/kg -> g/kg, clay:
    g/kg -> %), never with a hard-coded factor. Missing cells (sea, towns,
    gaps) come back as NaN.

    SoilGrids values are themselves model predictions at 250 m, not
    measurements: use them as a baseline that the satellite link must beat at
    lab-sampled points, never as ground truth. The query sends the exact
    coordinate to ISRIC; do not send private sample locations without the
    data owner's permission.
    """
    params: list[tuple[str, str]] = [("lon", f"{lon:.6f}"), ("lat", f"{lat:.6f}")]
    params += [("property", p) for p in properties]
    params += [("depth", depth), ("value", value)]
    get = transport or _http_json
    raw = get(SOILGRIDS_URL, params, timeout)
    layers = {
        layer.get("name"): layer
        for layer in (raw.get("properties", {}) or {}).get("layers", []) or []
    }
    out: dict[str, Any] = {
        "data_status": "public_observation",
        "source": "SoilGrids v2.0 REST API (" + SOILGRIDS_URL + ")",
        "licence": SOILGRIDS_LICENCE,
        "depth": depth,
        "statistic": value,
        "values": {},
    }
    for p in properties:
        layer = layers.get(p)
        rec: dict[str, Any] = {
            "value": math.nan,
            "unit": None,
            "mapped_value": None,
            "mapped_unit": None,
        }
        if layer is not None:
            um = layer.get("unit_measure", {}) or {}
            d_factor = float(um.get("d_factor") or 1.0)
            rec["unit"] = um.get("target_units")
            rec["mapped_unit"] = um.get("mapped_units")
            for d in layer.get("depths", []) or []:
                if d.get("label") == depth:
                    v = (d.get("values") or {}).get(value)
                    rec["mapped_value"] = v
                    if v is not None:
                        rec["value"] = float(v) / d_factor
        out["values"][p] = rec
    return out


SceneSearch = Callable[[Sample], list[Any]]
SceneReader = Callable[[Any, Sample], tuple[dict[str, np.ndarray], np.ndarray]]


# ---------------------------------------------------------------------------
# Scene cache: keep the small per-sample band windows, so that the bare-soil
# rule can be re-run offline with other thresholds without downloading again.
# ---------------------------------------------------------------------------


def _safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", str(text))[:120] or "_"


def scene_cache_path(cache_dir: Path, sample_id: str, item_id: str) -> Path:
    return Path(cache_dir) / _safe_name(sample_id) / f"{_safe_name(item_id)}.npz"


def save_scene_cache(
    path: Path,
    bands: Mapping[str, np.ndarray],
    scl: np.ndarray,
    item_id: str,
    when: str,
) -> None:
    """Write one window as .npz (atomic: temp file, then rename)."""
    import os

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp.npz")
    payload: dict[str, Any] = {f"band_{k}": np.asarray(v) for k, v in bands.items()}
    payload.update(
        scl=np.asarray(scl),
        item_id=np.asarray(str(item_id)),
        datetime=np.asarray(str(when)),
    )
    np.savez_compressed(tmp, **payload)
    os.replace(tmp, path)


def load_scene_cache(path: Path) -> dict[str, Any]:
    """Read one cached window: {item_id, datetime, bands, scl}."""
    with np.load(path, allow_pickle=False) as z:
        bands = {k[5:]: z[k] for k in z.files if k.startswith("band_")}
        return {
            "item_id": str(z["item_id"]),
            "datetime": str(z["datetime"]),
            "bands": bands,
            "scl": z["scl"],
        }


def cached_reader(reader: SceneReader, cache_dir: Path) -> SceneReader:
    """Wrap a scene reader: return the cached window if present, else read and store.

    Cache files hold pixel windows around the sample point. For private samples
    they reveal where the samples are, so keep the cache next to the private
    data, never in the repository.
    """

    def read(item: Any, s: Sample) -> tuple[dict[str, np.ndarray], np.ndarray]:
        item_id = getattr(item, "id", str(item))
        path = scene_cache_path(cache_dir, s.sample_id, item_id)
        if path.exists():
            c = load_scene_cache(path)
            return c["bands"], c["scl"]
        bands, scl = reader(item, s)
        props = getattr(item, "properties", {}) or {}
        save_scene_cache(path, bands, scl, item_id, str(props.get("datetime", "")))
        return bands, scl

    return read


def load_cache_dir(
    cache_dir: Path, only: Mapping[str, Iterable[str]] | None = None
) -> dict[str, list[dict[str, Any]]]:
    """All cached windows per sample id (sorted by date).

    ``only`` optionally restricts each sample to a set of item ids (e.g. the
    ``scene_ids`` column of one ``features`` run).
    """
    out: dict[str, list[dict[str, Any]]] = {}
    root = Path(cache_dir)
    wanted = (
        None
        if only is None
        else {_safe_name(k): {_safe_name(i) for i in v} for k, v in only.items()}
    )
    for sdir in sorted(p for p in root.iterdir() if p.is_dir()):
        if wanted is not None and sdir.name not in wanted:
            continue
        scenes = []
        for f in sorted(sdir.glob("*.npz")):
            if ".tmp." in f.name:
                continue
            if wanted is not None and f.stem not in wanted[sdir.name]:
                continue
            scenes.append(load_scene_cache(f))
        out[sdir.name] = sorted(scenes, key=lambda c: c["datetime"])
    return out


def bare_availability(
    cache: Mapping[str, Sequence[Mapping[str, Any]]],
    ndvi_max: float = NDVI_MAX,
    nbr2_max: float = NBR2_MAX,
    min_pixels: int = MIN_BARE_PIXELS,
) -> dict[str, Any]:
    """Offline bare-soil availability from cached windows for one threshold pair.

    Per sample: distinct acquisition dates with at least one bare pixel
    ("bare dates"; two tiles on the same day count once) and whether the
    composite reaches ``min_pixels`` bare pixels ("usable"). By month: how
    many sample-dates were read and how many were bare.
    """
    per: dict[str, dict[str, Any]] = {}
    month_read: dict[str, int] = {}
    month_bare: dict[str, int] = {}
    for sid, scenes in cache.items():
        bare_days: set[str] = set()
        read_days: set[str] = set()
        n_px = 0
        for c in scenes:
            day = str(c["datetime"])[:10]
            read_days.add(day)
            m = bare_soil_mask(c["bands"], c["scl"], ndvi_max, nbr2_max)
            k = int(m.sum())
            n_px += k
            if k:
                bare_days.add(day)
        for day in read_days:
            month_read[day[5:7]] = month_read.get(day[5:7], 0) + 1
        for day in bare_days:
            month_bare[day[5:7]] = month_bare.get(day[5:7], 0) + 1
        per[sid] = {
            "dates_read": len(read_days),
            "bare_dates": len(bare_days),
            "bare_pixels": n_px,
            "usable": n_px >= min_pixels,
            "bare_days": sorted(bare_days),
        }
    n = len(per)
    bare_counts = [p["bare_dates"] for p in per.values()]
    read_counts = [p["dates_read"] for p in per.values()]
    n_any = sum(b > 0 for b in bare_counts)
    n_usable = sum(p["usable"] for p in per.values())
    nan = math.nan
    return {
        "ndvi_max": ndvi_max,
        "nbr2_max": nbr2_max,
        "min_pixels": min_pixels,
        "n_samples": n,
        "share_any_bare_date": n_any / n if n else nan,
        "share_usable": n_usable / n if n else nan,
        "median_bare_dates": float(np.median(bare_counts)) if n else nan,
        "mean_bare_dates": float(np.mean(bare_counts)) if n else nan,
        "median_dates_read": float(np.median(read_counts)) if n else nan,
        "by_month": {
            m: {"dates_read": month_read.get(m, 0), "bare": month_bare.get(m, 0)}
            for m in sorted(month_read)
        },
        "per_sample": per,
    }


def extract_features(
    samples: Sequence[Sample],
    search: SceneSearch | None = None,
    reader: SceneReader | None = None,
    window_days: int = 365,
    max_cloud: float = 20.0,
    max_scenes: int = 12,
    half_m: float = 30.0,
    log: Callable[[str], None] = print,
    terrain: Callable[[float, float], dict[str, float]] | None = terrain_at,
    workers: int = 1,
    ndvi_max: float = NDVI_MAX,
    nbr2_max: float = NBR2_MAX,
    cache_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """One row per sample: features + provenance (scene ids). Never raises per sample.

    The work is network-bound (small windows read from cloud-optimised
    GeoTIFFs), so ``workers`` > 1 runs several samples at once in threads.
    Output order always follows the input order. With ``cache_dir`` every
    window read is stored as .npz (and reused), so the bare-soil rule can be
    re-run offline (``bare_availability``).
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

    if cache_dir is not None:
        reader = cached_reader(reader, Path(cache_dir))

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
        topo = dict(terrain(s.lat, s.lon)) if terrain else {}
        if "terrain_error" in topo:
            errors.append(f"terrain: {topo.pop('terrain_error')}")
        row = {
            "sample_id": s.sample_id,
            **feats,
            **topo,
            "n_bare_pixels": n_px,
            "n_scenes_used": used,
            "n_scenes_read": len(ids),
            "scene_ids": ";".join(ids),
            "errors": " | ".join(errors),
        }
        log(
            f"{s.sample_id}: {used}/{len(ids)} dates bare, {n_px} px"
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


def to_km(
    lat: Sequence[float] | np.ndarray, lon: Sequence[float] | np.ndarray
) -> np.ndarray:
    """Local equirectangular projection to km (fine for study areas < ~500 km)."""
    lat_a, lon_a = np.asarray(lat, float), np.asarray(lon, float)
    lat0 = float(np.mean(lat_a))
    return np.column_stack(
        [lon_a * 111.32 * math.cos(math.radians(lat0)), lat_a * 110.57]
    )


def spatial_blocks(
    lat: Sequence[float], lon: Sequence[float], block_km: float
) -> np.ndarray:
    """Integer block id per sample on a km grid."""
    xy = to_km(lat, lon) / block_km
    keys = [f"{int(math.floor(a))}_{int(math.floor(b))}" for a, b in xy]
    uniq = {k: i for i, k in enumerate(sorted(set(keys)))}
    return np.asarray([uniq[k] for k in keys])


def permutation_strata(
    lat: Sequence[float],
    lon: Sequence[float],
    start_km: float,
    min_median_size: int = 6,
) -> tuple[np.ndarray, float]:
    """Local strata for the restricted permutation test.

    Labels are shuffled only within a stratum. The stratum size starts at
    ``start_km`` and doubles until the median stratum holds at least
    ``min_median_size`` samples, so there is something to shuffle. Returns
    (stratum ids, stratum size in km).
    """
    km = float(start_km)
    n = len(lat)
    for _ in range(12):
        g = spatial_blocks(lat, lon, km)
        sizes = np.bincount(g)
        if np.median(sizes) >= min(min_median_size, n):
            return g, km
        km *= 2
    return np.zeros(n, int), km


def empirical_range_km(
    lat: Sequence[float] | np.ndarray,
    lon: Sequence[float] | np.ndarray,
    y: Sequence[float] | np.ndarray,
    n_bins: int = 15,
) -> float:
    """Distance at which the empirical semivariogram of y first reaches 95 % of
    the sample variance: a rough, model-free estimate of how far spatial
    similarity reaches.

    Returns ``inf`` when similarity persists beyond half the typical distance
    between samples (the study area is too small to see the end of it) and
    NaN when it cannot be estimated (fewer than 20 values).
    """
    y_a = np.asarray(y, float)
    ok = np.isfinite(y_a)
    xy = to_km(np.asarray(lat)[ok], np.asarray(lon)[ok])
    y_a = y_a[ok]
    n = len(y_a)
    if n < 20 or np.var(y_a) == 0:
        return math.nan
    rng = np.random.default_rng(0)
    idx = rng.choice(n, size=min(n, 1500), replace=False)
    xy, y_a = xy[idx], y_a[idx]
    i, j = np.triu_indices(len(y_a), 1)
    d = np.hypot(*(xy[i] - xy[j]).T)
    g = 0.5 * (y_a[i] - y_a[j]) ** 2
    sill = float(np.var(y_a, ddof=1))
    edges = np.linspace(0, np.percentile(d, 50), n_bins + 1)
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (d > lo) & (d <= hi)
        if sel.sum() >= 10 and g[sel].mean() >= 0.95 * sill:
            return float((lo + hi) / 2)
    return math.inf


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
    """Spearman correlation of each feature with the property, FDR-corrected.

    Descriptive only: these p-values assume independent samples, which nearby
    soil samples are not. Never use them as the evidence of a signal.
    """
    from scipy.stats import spearmanr

    rows: list[dict[str, Any]] = []
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


def make_models(seed: int = 0, fast: bool = False) -> dict[str, Any]:
    from sklearn.cross_decomposition import PLSRegression
    from sklearn.dummy import DummyRegressor
    from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import RidgeCV
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    class _PLS(PLSRegression):  # type: ignore[misc]  # PLSRegression has no type stubs
        def predict(
            self, X: Any, copy: bool = True
        ) -> np.ndarray:  # 1-D output like the others
            return cast(np.ndarray, np.ravel(super().predict(X, copy=copy)))

    trees = 100 if fast else 300
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
            n_estimators=trees, min_samples_leaf=3, random_state=seed, n_jobs=-1
        ),
        "gradient_boosting": HistGradientBoostingRegressor(
            max_iter=trees, learning_rate=0.05, min_samples_leaf=10, random_state=seed
        ),
    }


def location_model(seed: int = 0) -> Any:
    """Coordinates-only reference: k nearest neighbours in km space."""
    from sklearn.neighbors import KNeighborsRegressor

    return KNeighborsRegressor(n_neighbors=10, weights="distance")


def cross_validated_predictions(
    model: Any, X: np.ndarray, y: np.ndarray, groups: np.ndarray, n_splits: int
) -> np.ndarray:
    from sklearn.base import clone
    from sklearn.model_selection import GroupKFold

    pred = np.full(len(y), np.nan)
    k = min(n_splits, len(np.unique(groups)))
    for tr, te in GroupKFold(n_splits=k).split(X, y, groups):
        m = clone(model).fit(X[tr], y[tr])
        pred[te] = np.ravel(m.predict(X[te]))
    return pred


def nested_cv_predictions(
    models: Mapping[str, Any],
    candidates: Sequence[str],
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    n_splits: int,
    inner_splits: int = 4,
) -> tuple[np.ndarray, list[str]]:
    """Spatial-block CV in which the model choice is part of the training.

    In every outer fold the candidate models are compared by an inner spatial
    block CV on the training blocks only; the winner is refitted on all
    training blocks and predicts the held-out block. The held-out data never
    influence which model is chosen, so the resulting R2 is not inflated by
    picking the best of several models (unlike the maximum of per-model CV R2).
    Returns (predictions, model chosen in each outer fold).
    """
    from sklearn.base import clone
    from sklearn.model_selection import GroupKFold

    pred = np.full(len(y), np.nan)
    chosen: list[str] = []
    k = min(n_splits, len(np.unique(groups)))
    for tr, te in GroupKFold(n_splits=k).split(X, y, groups):
        g_tr = groups[tr]
        k_in = min(inner_splits, len(np.unique(g_tr)))
        if k_in >= 2 and len(candidates) > 1:
            scores = {
                c: _metrics(
                    y[tr],
                    cross_validated_predictions(models[c], X[tr], y[tr], g_tr, k_in),
                )["r2"]
                for c in candidates
            }
            pick = max(
                candidates,
                key=lambda c: scores[c] if np.isfinite(scores[c]) else -np.inf,
            )
        else:  # too few training blocks to compare: first candidate, recorded
            pick = candidates[0]
        chosen.append(pick)
        m = clone(models[pick]).fit(X[tr], y[tr])
        pred[te] = np.ravel(m.predict(X[te]))
    return pred, chosen


def _permute_within(
    y: np.ndarray, strata: np.ndarray, rng: np.random.Generator
) -> np.ndarray:
    out = y.copy()
    for s in np.unique(strata):
        idx = np.nonzero(strata == s)[0]
        if len(idx) > 1:
            out[idx] = y[rng.permutation(idx)]
    return out


def detrend(v: np.ndarray, xy_km: np.ndarray) -> np.ndarray:
    """Residuals of a quadratic surface fitted to the coordinates (per column)."""
    c = (xy_km - xy_km.mean(axis=0)) / (xy_km.std(axis=0) + 1e-12)
    D = np.column_stack(
        [
            np.ones(len(c)),
            c[:, 0],
            c[:, 1],
            c[:, 0] ** 2,
            c[:, 1] ** 2,
            c[:, 0] * c[:, 1],
        ]
    )
    V = v.reshape(len(c), -1)
    coef, *_ = np.linalg.lstsq(D, V, rcond=None)
    out = V - D @ coef
    return cast(np.ndarray, out.ravel() if v.ndim == 1 else out)


class SpectralSurrogates:
    """Moran spectral randomization (Wagner & Dray 2015, random-sign variant).

    The soil map is written as a sum of spatial patterns (eigenvectors of a
    doubly centred distance-weight matrix, from broad to fine). A surrogate
    keeps the size of every pattern but flips its sign at random. It is
    therefore exactly as smooth as the real map, at every scale, yet no longer
    aligned with the features. Two unrelated smooth maps score no better than
    the real map's surrogates; a genuine relationship does.
    Cost: one eigen-decomposition, O(n^3); fine up to a few thousand samples.
    """

    def __init__(self, xy_km: np.ndarray, bandwidth_km: float | None = None) -> None:
        from scipy.spatial.distance import cdist

        n = len(xy_km)
        d = cdist(xy_km, xy_km)
        if bandwidth_km is None or not np.isfinite(bandwidth_km) or bandwidth_km <= 0:
            nn = np.sort(d, axis=1)[:, 1] if n > 1 else np.array([1.0])
            bandwidth_km = max(float(np.median(nn)) * 3, 1e-6)
        W = np.exp(-d / bandwidth_km)
        np.fill_diagonal(W, 0.0)
        C = np.eye(n) - 1.0 / n
        _, self.V = np.linalg.eigh(C @ W @ C)

    def __call__(self, y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        m = y.mean()
        a = self.V.T @ (y - m)
        return m + self.V @ (a * rng.choice([-1.0, 1.0], size=len(a)))


def evaluate_property(
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    names: Sequence[str],
    lat: Sequence[float] | None = None,
    lon: Sequence[float] | None = None,
    n_splits: int = 5,
    n_permutations: int = 99,
    seed: int = 0,
    models: Mapping[str, Any] | None = None,
    strata: np.ndarray | None = None,
    min_added_r2: float = 0.02,
    min_independent_areas: int = 10,
) -> dict[str, Any]:
    """Spatial-block CV and a spatial null model.

    Verdict "signal_above_chance" requires ALL of:
      - the best model beats the mean baseline (nested CV R2 > 0 and > the
        baseline's CV R2; the model choice is made inside each training set);
      - with coordinates (always use them): after removing a quadratic trend
        in the coordinates from soil values and features, the best model still
        reaches CV R2 >= ``min_added_r2``, and beats >= 95 % of spectral
        surrogates of the soil map that are equally smooth (p <= 0.05);
      - without coordinates: a within-block permutation test (weaker).
    Verdict "inconclusive_spatial_scale" when soil values and features both
    stay similar over distances so large that the study area holds fewer than
    max(``min_independent_areas``, 2.5 x features) independent areas; with so
    little independent information no test can decide.
    """
    lat_a = None if lat is None else np.asarray(lat, float)
    lon_a = None if lon is None else np.asarray(lon, float)
    ok = np.isfinite(y) & np.all(np.isfinite(X), axis=1)
    X, y, groups = X[ok], y[ok], np.asarray(groups)[ok]
    if lat_a is not None and lon_a is not None:
        lat_a, lon_a = lat_a[ok], lon_a[ok]
    n_groups = len(np.unique(groups))
    k = min(n_splits, n_groups)
    if len(y) < 20 or k < 2:
        return {
            "status": "too_few_samples",
            "n": int(len(y)),
            "n_blocks": int(n_groups),
        }
    models = dict(models or make_models(seed))
    candidates = [m for m in models if m != "baseline_mean"]
    if "baseline_mean" not in models:
        from sklearn.dummy import DummyRegressor

        models["baseline_mean"] = DummyRegressor(strategy="mean")
    preds = {
        name: cross_validated_predictions(m, X, y, groups, k)
        for name, m in models.items()
    }
    results = {name: _metrics(y, pr) for name, pr in preds.items()}
    best = max(candidates, key=lambda n: results[n]["r2"])
    # Plain CV R2 of the best of several models is biased upwards (the choice
    # saw the test blocks). The R2 reported for "the best model" therefore
    # comes from nested CV, where the choice is made inside each training set.
    nested_pred, chosen = nested_cv_predictions(
        models, candidates, X, y, groups, k, inner_splits=max(2, k - 1)
    )
    nested = _metrics(y, nested_pred)
    real = nested["r2"]

    rng = np.random.default_rng(seed)

    def best_r2(Xm: np.ndarray, target: np.ndarray) -> float:
        # The whole model choice is repeated for every null sample, so picking
        # the best of several models cannot inflate the result.
        return max(
            _metrics(
                target, cross_validated_predictions(models[c], Xm, target, groups, k)
            )["r2"]
            for c in candidates
        )

    location: dict[str, Any] = {"status": "no_coordinates"}
    if lat_a is not None and lon_a is not None:
        # Spatial null model. Soil values and features are first detrended
        # (quadratic surface in the coordinates), so a shared regional trend
        # cannot pass as a signal. The null distribution then comes from
        # spectral surrogates of the detrended soil map that keep its
        # smoothness at every scale but break its alignment with the features.
        xy = to_km(lat_a, lon_a)
        loc_r2 = _metrics(
            y, cross_validated_predictions(location_model(), xy, y, groups, k)
        )["r2"]
        Xd, yd = detrend(X, xy), detrend(y, xy)
        # Effective sample size guard. Chance correlation between two maps
        # needs BOTH to be spatially smooth. If soil values and the typical
        # feature stay similar over distances comparable to the study area,
        # there are too few independent areas for any test to tell a real
        # relationship from coincidence, so no verdict is given.
        range_y = empirical_range_km(lat_a, lon_a, yd)
        ranges_x = [
            empirical_range_km(lat_a, lon_a, Xd[:, c]) for c in range(Xd.shape[1])
        ]
        finite_x = [r for r in ranges_x if not math.isnan(r)]
        range_x = float(np.median(finite_x)) if finite_x else math.nan
        scale = min(
            range_y if not math.isnan(range_y) else 0.0,
            range_x if not math.isnan(range_x) else 0.0,
        )
        extent = np.maximum(xy.max(axis=0) - xy.min(axis=0), 1e-9)
        if math.isinf(scale):
            n_indep = 1.0
        elif scale > 0:
            # independent areas = study extent measured in correlation lengths
            n_indep = float(min(len(y), np.prod(np.maximum(extent / scale, 1.0))))
        else:
            n_indep = float(len(y))
        # Calibrated on synthetic unrelated smooth maps (27 Nov 2026, 17
        # features, 200 samples, 10 seeds each): the spectral-randomization
        # test gave 0/10 false signals with ~38-67 independent areas, 4/10 with
        # ~19-38 and 10/10 with ~14-27. So below ~2.5 areas per feature no
        # verdict is given.
        needed = max(min_independent_areas, int(math.ceil(2.5 * X.shape[1])))
        stat = best_r2(Xd, yd)
        surrogate = SpectralSurrogates(xy)
        null_a = np.asarray(
            [best_r2(Xd, surrogate(yd, rng)) for _ in range(n_permutations)]
        )
        p_val = (int(np.sum(null_a >= stat)) + 1) / (n_permutations + 1)
        test = {
            "kind": "Moran spectral randomization of the detrended soil map; "
            "best of all models each time",
            "statistic": "CV R2 of detrended soil from detrended features",
            "statistic_value": stat,
        }
        location = {
            "location_only_r2": loc_r2,
            "detrended_r2_from_spectra": stat,
            "min_detrended_r2": min_added_r2,
            "spatial_range_soil_km": range_y,
            "spatial_range_features_km_median": range_x,
            "independent_areas": round(n_indep, 1),
            "independent_areas_needed": needed,
            "rule": "at least max(10, 2.5 x number of features) independent areas",
        }
        signal_ok = p_val <= 0.05 and stat >= min_added_r2
        inconclusive = n_indep < needed
    else:
        strata = groups if strata is None else strata
        null_a = np.asarray(
            [best_r2(X, _permute_within(y, strata, rng)) for _ in range(n_permutations)]
        )
        # Unchanged test: the best plain CV R2, compared with the best plain CV
        # R2 of every permutation (the choice is repeated on both sides).
        plain_best = results[best]["r2"]
        p_val = (int(np.sum(null_a >= plain_best)) + 1) / (n_permutations + 1)
        test = {
            "kind": "permutation within blocks (no coordinates given: weaker)",
            "statistic": "best plain CV R2 (model choice repeated per permutation)",
            "statistic_value": plain_best,
        }
        signal_ok = p_val <= 0.05
        inconclusive = False
    beats_baseline = real > results["baseline_mean"]["r2"] and real > 0
    if inconclusive:
        verdict = "inconclusive_spatial_scale"
    elif signal_ok and beats_baseline:
        verdict = "signal_above_chance"
    else:
        verdict = "no_evidence_of_signal"
    return {
        "status": "ok",
        "n": int(len(y)),
        "n_blocks": int(n_groups),
        "cv_folds": int(k),
        "models": results,
        "models_note": "Per-model spatial-block CV. The maximum over models is "
        "optimistic; use best_model_cv (nested CV) as the skill of the best model.",
        "best_model": best,
        "best_model_cv": {
            **nested,
            "method": "nested spatial-block CV: model chosen by inner CV on the "
            "training blocks of each outer fold",
            "chosen_per_fold": chosen,
        },
        "models_beating_baseline": sorted(
            c for c in candidates if results[c]["r2"] > results["baseline_mean"]["r2"]
        ),
        "interval_80_halfwidth": prediction_interval_halfwidth(y, nested_pred, 0.8),
        "permutation": {
            **test,
            "n_permutations": n_permutations,
            "null_r2_p95": float(np.percentile(null_a, 95)),
            "p_value": p_val,
        },
        "location_check": location,
        "screen": univariate_screen(X, y, names),
        "verdict": verdict,
    }


def area_of_applicability(
    X_train: np.ndarray,
    X_new: np.ndarray,
    groups: np.ndarray | None = None,
    k_search: int = 50,
) -> dict[str, Any]:
    """Dissimilarity index (Meyer & Pebesma 2021, simplified, unweighted).

    For a new location, DI = distance to the nearest training sample in
    standardised feature space, divided by the mean distance between training
    samples. The threshold is the upper whisker (Q3 + 1.5 IQR) of the training
    DIs, each computed against samples outside its own block. New locations
    above it are outside the area of applicability: the model has never seen
    anything like them and its prediction there should not be used.

    Missing values are replaced by the training median of that feature.
    Memory stays linear in the number of samples (nearest-neighbour search,
    mean distance estimated from at most 600 samples).
    """
    from sklearn.neighbors import NearestNeighbors

    Xt = np.asarray(X_train, float)
    Xn = np.asarray(X_new, float)
    med = np.nanmedian(Xt, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    Xt = np.where(np.isfinite(Xt), Xt, med)
    Xn = np.where(np.isfinite(Xn), Xn, med)
    mu, sd = Xt.mean(axis=0), Xt.std(axis=0)
    sd[sd == 0] = 1.0
    A, B = (Xt - mu) / sd, (Xn - mu) / sd
    n = len(A)
    rng = np.random.default_rng(0)
    sub = A[rng.choice(n, size=min(n, 600), replace=False)]
    i, j = np.triu_indices(len(sub), 1)
    mean_d = (
        float(np.hypot.reduce(sub[i] - sub[j], axis=1).mean()) if len(sub) > 1 else 1.0
    )
    nn = NearestNeighbors().fit(A)
    g = np.arange(n) if groups is None else np.asarray(groups)
    kk = min(n, k_search)
    dist, ind = nn.kneighbors(A, n_neighbors=kk)
    di_train = np.full(n, np.nan)
    for r in range(n):
        other = g[ind[r]] != g[r]
        if other.any():
            di_train[r] = dist[r][other][0] / mean_d
        else:  # all k nearest share the block: exact search for this row
            mask = g != g[r]
            if mask.any():
                di_train[r] = np.sqrt(((A[mask] - A[r]) ** 2).sum(1)).min() / mean_d
    q1, q3 = np.nanpercentile(di_train, [25, 75])
    thr = float(q3 + 1.5 * (q3 - q1))
    d_new = (
        nn.kneighbors(B, n_neighbors=1)[0][:, 0] / mean_d if len(B) else np.array([])
    )
    return {
        "threshold": thr,
        "di_train": di_train,
        "di_new": d_new,
        "inside": d_new <= thr,
        "share_inside": float(np.mean(d_new <= thr)) if len(d_new) else math.nan,
    }


def prediction_interval_halfwidth(
    y: np.ndarray, pred: np.ndarray, coverage: float = 0.8
) -> float:
    """Split-conformal style: the |residual| quantile from spatial CV.

    Predicted value +- this number covers about ``coverage`` of new samples
    from areas similar to the training data. Under spatial dependence and
    outside the area of applicability, real coverage can be lower.
    """
    r = np.abs(y - pred)
    r = r[np.isfinite(r)]
    n = len(r)
    k = min(n, int(math.ceil((n + 1) * coverage)))
    return float(np.sort(r)[k - 1]) if n else math.nan


def samples_needed(
    r: float,
    alpha: float = 0.05,
    power: float = 0.8,
    n_tests: int = 1,
    bare_share: float = 1.0,
    design_effect: float = 1.0,
) -> int:
    """Lab samples to collect to detect a correlation r (two-sided, Fisher z).

    - ``n_tests``: properties tested; Bonferroni-adjusts alpha.
    - ``bare_share``: share of samples expected to have bare-soil imagery
      (1 of 3 in the 27 Nov test near Beja); inflates the count.
    - ``design_effect``: >1 for spatially clustered sampling (nearby samples
      carry less independent information). Unknown until a variogram exists;
      1.5-2 is a cautious planning value.
    This is a planning number for independent samples; it is optimistic.
    """
    from scipy.stats import norm

    if not 0 < abs(r) < 1:
        raise ValueError("r must be in (0, 1)")
    if not 0 < bare_share <= 1:
        raise ValueError("bare_share must be in (0, 1]")
    a = alpha / max(1, n_tests)
    z = norm.ppf(1 - a / 2) + norm.ppf(power)
    n = (z / math.atanh(abs(r))) ** 2 + 3
    return int(math.ceil(n * design_effect / bare_share))


# ---------------------------------------------------------------------------
# Synthetic scenarios (labelled; used to prove the method finds a planted
# signal and does NOT invent one in realistic spatial settings)
# ---------------------------------------------------------------------------

SCENARIOS = (
    "planted_signal",
    "planted_signal_patchy_features",
    "iid_noise",
    "unrelated_smooth_fields",
    "shared_trend",
)
EXPECTED = {
    "planted_signal": "signal_above_chance",
    "planted_signal_patchy_features": "signal_above_chance",
    "iid_noise": "no_evidence_of_signal",
    "unrelated_smooth_fields": "inconclusive_spatial_scale",
    "shared_trend": "no_evidence_of_signal",
}


def smooth_field(
    xy_km: np.ndarray,
    rng: np.random.Generator,
    range_km: float = 20.0,
    n_waves: int = 40,
) -> np.ndarray:
    """A smooth random field (random Fourier features), unit variance.
    ``range_km`` sets the typical distance over which values stay similar."""
    freqs = rng.normal(0, 1.0 / range_km, size=(n_waves, 2))
    phase = rng.uniform(0, 2 * math.pi, n_waves)
    f = np.cos(xy_km @ freqs.T + phase).sum(axis=1)
    return (f - f.mean()) / (f.std() or 1.0)


def synthetic_dataset(
    n: int = 200,
    signal: float = 1.0,
    seed: int = 0,
    scenario: str | None = None,
) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray, np.ndarray]:
    """Fake samples in a 60 x 60 km area near 38 N.

    Scenarios:
      planted_signal          soil depends on one spectral feature (+ noise)
      planted_signal_patchy_features
                              same, but every feature is spatially patterned
                              at field scale (~3 km), as real images are
      iid_noise               soil unrelated; features spatially random
      unrelated_smooth_fields soil and all features are smooth random fields,
                              independent of each other (the trap found by the
                              independent review)
      shared_trend            soil and one feature share a regional trend but
                              are otherwise independent (location confound)
    ``signal`` is kept for backward compatibility: 1.0 -> planted_signal,
    0.0 -> iid_noise, when ``scenario`` is not given.
    """
    if scenario is None:
        scenario = "planted_signal" if signal else "iid_noise"
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}")
    rng = np.random.default_rng(seed)
    lat = 38.0 + rng.uniform(0, 0.54, n)
    lon = -8.2 + rng.uniform(0, 0.68, n)
    xy = to_km(lat, lon)
    p = len(FEATURE_NAMES)
    j = FEATURE_NAMES.index("swir16")
    if scenario == "planted_signal_patchy_features":
        X = np.column_stack(
            [0.25 + 0.05 * smooth_field(xy, rng, range_km=3.0) for _ in range(p)]
        )
        soc = 12 + 40 * (X[:, j] - 0.25) + smooth_field(xy, rng) + rng.normal(0, 0.5, n)
        return X, {"soc_g_kg": soc}, lat, lon
    if scenario == "unrelated_smooth_fields":
        X = np.column_stack([0.25 + 0.05 * smooth_field(xy, rng) for _ in range(p)])
        soc = 12 + 3 * smooth_field(xy, rng) + rng.normal(0, 0.3, n)
    elif scenario == "shared_trend":
        trend = (xy[:, 1] - xy[:, 1].mean()) / xy[:, 1].std()
        X = rng.normal(0.25, 0.05, size=(n, p))
        X[:, j] = 0.25 + 0.04 * trend + rng.normal(0, 0.02, n)
        soc = 12 + 3 * trend + 2 * smooth_field(xy, rng) + rng.normal(0, 0.5, n)
    else:
        X = rng.normal(0.25, 0.05, size=(n, p))
        local = smooth_field(xy, rng)
        if scenario == "planted_signal":
            soc = 12 + 40 * (X[:, j] - 0.25) + local + rng.normal(0, 0.5, n)
        else:
            soc = 12 + local + rng.normal(0, 0.5, n)
    return X, {"soc_g_kg": soc}, lat, lon
