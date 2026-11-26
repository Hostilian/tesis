"""Reproducible Sentinel-2 change case study for public Portuguese study areas.

Pipeline stages
---------------
1. Catalogue: resolve pinned STAC item IDs (Earth Search, ``sentinel-2-l2a``)
   and record their metadata. ``discover_items`` lists candidates so the
   selection rule can be re-run and audited.
2. Acquisition: windowed reads of public Cloud-Optimised GeoTIFFs for the
   study-area bounding box. 20 m bands are resampled (nearest) onto the 10 m
   grid of the same MGRS tile. No bulk download, no credentials.
3. Preprocessing: digital numbers -> surface reflectance using the
   ``raster:bands`` scale/offset published with each asset (this handles the
   processing-baseline 04.00 BOA offset), nodata handling and a Scene
   Classification Layer (SCL) mask.
4. Change analysis: per-pixel index difference (after - before) on pixels that
   are valid on both dates, a short-interval control pair that estimates the
   no-change noise level, threshold sensitivity and connected-patch statistics.
5. Outputs: run manifest, results JSON, sensitivity CSV, figures and a
   web-map overlay. Every output carries a ``data_status`` category.

Data-status vocabulary (used in every public artifact)
------------------------------------------------------
``public_observation``           unmodified catalogue metadata / imagery
``observation_derived_result``   numbers computed from those observations
``unverified_interpretation``    a reading of a result whose cause is not
                                 independently confirmed
``synthetic_demonstration``      fixtures and mock data, never evidence

The module separates pure array functions (unit-tested offline) from network
I/O so that the method can be checked without access to the catalogue.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

EARTH_SEARCH_URL = "https://earth-search.aws.element84.com/v1"
COLLECTION = "sentinel-2-l2a"
SENTINEL_LICENSE_URL = (
    "https://sentinel.esa.int/documents/247904/690755/Sentinel_Data_Legal_Notice"
)

# Sen2Cor Scene Classification Layer codes (ESA Sentinel-2 L2A product spec).
SCL_LABELS: dict[int, str] = {
    0: "no_data",
    1: "saturated_or_defective",
    2: "dark_area_pixels",
    3: "cloud_shadows",
    4: "vegetation",
    5: "not_vegetated",
    6: "water",
    7: "unclassified",
    8: "cloud_medium_probability",
    9: "cloud_high_probability",
    10: "thin_cirrus",
    11: "snow_or_ice",
}
DEFAULT_VALID_SCL: tuple[int, ...] = (4, 5, 6)

INDEX_BANDS: dict[str, tuple[str, ...]] = {
    "ndvi": ("red", "nir"),
    "bsi": ("blue", "red", "nir", "swir16"),
}

DATA_STATUS = (
    "public_observation",
    "observation_derived_result",
    "unverified_interpretation",
    "synthetic_demonstration",
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CaseStudyConfig:
    """Declarative description of one case study (loaded from JSON)."""

    case_id: str
    title: str
    bbox: tuple[
        float, float, float, float
    ]  # lon_min, lat_min, lon_max, lat_max (WGS84)
    index: str
    before_item: str
    after_item: str
    control_before_item: str
    control_after_item: str
    primary_threshold: (
        float | str
    )  # number, or "control_p99" (rule applied at run time)
    thresholds: tuple[float, ...]
    min_patch_ha: float = 1.0
    min_joint_valid_fraction: float = 0.8
    valid_scl: tuple[int, ...] = DEFAULT_VALID_SCL
    seasonal_item: str | None = None
    seasonal_amplitude_threshold: float = 0.15
    description: str = ""
    selection_rationale: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "CaseStudyConfig":
        bbox = tuple(float(v) for v in raw["bbox"])
        validate_bbox(bbox)
        index = str(raw["index"]).lower()
        if index not in INDEX_BANDS:
            raise ValueError(
                f"Unsupported index {index!r}; choose one of {sorted(INDEX_BANDS)}"
            )
        thresholds = tuple(sorted(float(t) for t in raw["thresholds"]))
        primary_raw = raw["primary_threshold"]
        primary: float | str
        if isinstance(primary_raw, str):
            if primary_raw != "control_p99":
                raise ValueError('primary_threshold must be a number or "control_p99"')
            primary = primary_raw
        else:
            primary = float(primary_raw)
            if primary not in thresholds:
                raise ValueError("primary_threshold must be one of thresholds")
        if any(t <= 0 for t in thresholds):
            raise ValueError("thresholds must be positive magnitudes")
        known = {f for f in cls.__dataclass_fields__}
        extra = {k: v for k, v in raw.items() if k not in known}
        return cls(
            case_id=str(raw["case_id"]),
            title=str(raw["title"]),
            bbox=bbox,  # type: ignore[arg-type]
            index=index,
            before_item=str(raw["before_item"]),
            after_item=str(raw["after_item"]),
            control_before_item=str(raw["control_before_item"]),
            control_after_item=str(raw["control_after_item"]),
            primary_threshold=primary,
            thresholds=thresholds,
            min_patch_ha=float(raw.get("min_patch_ha", 1.0)),
            min_joint_valid_fraction=float(raw.get("min_joint_valid_fraction", 0.8)),
            valid_scl=tuple(int(v) for v in raw.get("valid_scl", DEFAULT_VALID_SCL)),
            seasonal_item=raw.get("seasonal_item"),
            seasonal_amplitude_threshold=float(
                raw.get("seasonal_amplitude_threshold", 0.15)
            ),
            description=str(raw.get("description", "")),
            selection_rationale=str(raw.get("selection_rationale", "")),
            extra=extra,
        )

    @classmethod
    def from_file(cls, path: Path) -> "CaseStudyConfig":
        return cls.from_mapping(json.loads(Path(path).read_text(encoding="utf-8")))

    def item_ids(self) -> list[str]:
        ids = [
            self.before_item,
            self.after_item,
            self.control_before_item,
            self.control_after_item,
        ]
        if self.seasonal_item:
            ids.append(self.seasonal_item)
        return list(dict.fromkeys(ids))


def validate_bbox(bbox: Sequence[float]) -> None:
    if len(bbox) != 4 or not all(math.isfinite(v) for v in bbox):
        raise ValueError("bbox must be four finite numbers")
    lon_min, lat_min, lon_max, lat_max = bbox
    if not (-180 <= lon_min < lon_max <= 180 and -90 <= lat_min < lat_max <= 90):
        raise ValueError(
            "bbox must be lon_min, lat_min, lon_max, lat_max in WGS84 degrees"
        )


# ---------------------------------------------------------------------------
# Pure array functions (unit-tested without network access)
# ---------------------------------------------------------------------------


def to_reflectance(
    dn: np.ndarray, scale: float, offset: float, nodata: int | None = 0
) -> np.ndarray:
    """Convert L2A digital numbers to surface reflectance; nodata -> NaN."""
    out = dn.astype("float32") * np.float32(scale) + np.float32(offset)
    if nodata is not None:
        out[dn == nodata] = np.nan
    return out


def normalized_difference(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """(a - b) / (a + b) with NaN where the denominator is ~0 or inputs are NaN."""
    num = a - b
    den = a + b
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(np.abs(den) > 1e-6, num / den, np.nan)
    return np.clip(out, -1.0, 1.0).astype("float32")


def compute_index(index: str, bands: Mapping[str, np.ndarray]) -> np.ndarray:
    if index == "ndvi":
        return normalized_difference(bands["nir"], bands["red"])
    if index == "bsi":
        # Bare Soil Index: ((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue))
        return normalized_difference(
            bands["swir16"] + bands["red"], bands["nir"] + bands["blue"]
        )
    raise ValueError(f"Unsupported index {index!r}")


def scl_valid_mask(
    scl: np.ndarray, valid_classes: Iterable[int] = DEFAULT_VALID_SCL
) -> np.ndarray:
    return np.isin(scl, np.asarray(list(valid_classes), dtype=scl.dtype))


def scl_class_counts(scl: np.ndarray) -> dict[str, int]:
    values, counts = np.unique(scl, return_counts=True)
    return {
        SCL_LABELS.get(int(v), f"class_{int(v)}"): int(c)
        for v, c in zip(values, counts)
    }


def difference(
    before: np.ndarray,
    after: np.ndarray,
    valid_before: np.ndarray,
    valid_after: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (after - before, joint-valid mask). Invalid pixels are NaN."""
    joint = valid_before & valid_after & np.isfinite(before) & np.isfinite(after)
    delta = np.full(before.shape, np.nan, dtype="float32")
    delta[joint] = after[joint] - before[joint]
    return delta, joint


def summarize(values: np.ndarray) -> dict[str, float | int]:
    v = values[np.isfinite(values)]
    if v.size == 0:
        return {"n": 0}
    q = np.percentile(v, [1, 5, 25, 50, 75, 95, 99])
    return {
        "n": int(v.size),
        "mean": float(v.mean()),
        "std": float(v.std(ddof=1)) if v.size > 1 else 0.0,
        "p01": float(q[0]),
        "p05": float(q[1]),
        "p25": float(q[2]),
        "median": float(q[3]),
        "p75": float(q[4]),
        "p95": float(q[5]),
        "p99": float(q[6]),
    }


def threshold_table(
    main_delta: np.ndarray, control_delta: np.ndarray, thresholds: Iterable[float]
) -> list[dict[str, float | int]]:
    """Flagged share of the main pair vs the no-change control pair per threshold.

    The control share is read as an empirical false-alarm proxy: under the
    assumption that little real change happens between the two control dates,
    pixels it flags are noise (atmosphere, illumination, registration, phenology).
    """
    m = main_delta[np.isfinite(main_delta)]
    c = control_delta[np.isfinite(control_delta)]
    rows = []
    for t in thresholds:
        main_inc = int((m > t).sum())
        main_dec = int((m < -t).sum())
        ctrl_flag = int((np.abs(c) > t).sum())
        rows.append(
            {
                "threshold": float(t),
                "main_valid_pixels": int(m.size),
                "main_increase_pixels": main_inc,
                "main_decrease_pixels": main_dec,
                "main_flagged_share": (
                    (main_inc + main_dec) / m.size if m.size else float("nan")
                ),
                "control_valid_pixels": int(c.size),
                "control_flagged_pixels": ctrl_flag,
                "control_flagged_share": ctrl_flag / c.size if c.size else float("nan"),
            }
        )
    return rows


def resolve_threshold(
    rule: float | str, thresholds: Sequence[float], control_delta: np.ndarray
) -> tuple[float, str]:
    """Pick the change threshold.

    ``control_p99``: smallest grid threshold that is >= the 99th percentile of
    |delta| in the short-interval control pair, i.e. at most ~1 % of control
    pixels would be flagged. Fixed before looking at the main pair's map.
    """
    if not isinstance(rule, str):
        return float(rule), "fixed in config"
    c = np.abs(control_delta[np.isfinite(control_delta)])
    if c.size == 0:
        raise ValueError("Control pair has no valid pixels; cannot derive threshold")
    p99 = float(np.percentile(c, 99))
    for t in sorted(thresholds):
        if t >= p99:
            return (
                float(t),
                f"control_p99: smallest grid value >= p99(|control delta|) = {p99:.4f}",
            )
    # Fail loudly instead of silently using a threshold that breaks the stated rule.
    raise ValueError(
        f"control p99 |delta| = {p99:.4f} exceeds every threshold in the grid {sorted(thresholds)}; extend the grid"
    )


def label_patches(mask: np.ndarray) -> tuple[np.ndarray, int]:
    from scipy import ndimage

    structure = np.ones((3, 3), dtype=bool)  # 8-connectivity
    labels, n = ndimage.label(mask, structure=structure)
    return labels, int(n)


def patch_statistics(
    mask: np.ndarray, pixel_area_m2: float, min_patch_ha: float
) -> dict[str, Any]:
    """Connected-patch summary of a boolean change mask."""
    labels, n = label_patches(mask)
    if n == 0:
        return {
            "patches_total": 0,
            "patches_ge_min": 0,
            "flagged_pixels": 0,
            "share_of_flagged_in_patches_ge_min": float("nan"),
        }
    sizes = np.bincount(labels.ravel())[1:]
    min_px = max(1, int(math.ceil(min_patch_ha * 10_000 / pixel_area_m2)))
    big = sizes[sizes >= min_px]
    areas_ha = big * pixel_area_m2 / 10_000
    return {
        "patches_total": n,
        "min_patch_pixels": min_px,
        "patches_ge_min": int(big.size),
        "flagged_pixels": int(sizes.sum()),
        "share_of_flagged_in_patches_ge_min": float(big.sum() / sizes.sum()),
        "area_ge_min_ha": float(areas_ha.sum()) if big.size else 0.0,
        "patch_area_ha_median": (
            float(np.median(areas_ha)) if big.size else float("nan")
        ),
        "patch_area_ha_p90": (
            float(np.percentile(areas_ha, 90)) if big.size else float("nan")
        ),
        "patch_area_ha_max": float(areas_ha.max()) if big.size else float("nan"),
    }


def keep_patches_ge(mask: np.ndarray, min_pixels: int) -> np.ndarray:
    labels, n = label_patches(mask)
    if n == 0:
        return np.zeros_like(mask, dtype=bool)
    sizes = np.bincount(labels.ravel())
    keep = sizes >= min_pixels
    keep[0] = False
    return np.asarray(keep[labels], dtype=bool)


def resolution_table(
    target_area_ha: float, resolutions_m: Iterable[float] = (3, 10, 20, 30, 60)
) -> list[dict[str, float]]:
    """How many whole pixels fit in a square target of the given area.

    Interior (pure) pixels assume a square target aligned with the grid and a
    one-pixel mixed border; it is a best case, not a measurement.
    """
    side = math.sqrt(target_area_ha * 10_000)
    rows = []
    for r in resolutions_m:
        total = (side / r) ** 2
        interior = max(0.0, side / r - 2) ** 2
        rows.append(
            {
                "resolution_m": float(r),
                "pixels_total": total,
                "pixels_interior": interior,
            }
        )
    return rows


def seasonal_split(
    increase_mask: np.ndarray,
    after_summer: np.ndarray,
    after_other_season: np.ndarray,
    other_valid: np.ndarray,
    amplitude_threshold: float,
) -> dict[str, int]:
    """Split NDVI-increase pixels by within-year stability of the after year.

    Permanent tree crops keep green canopy across the season; irrigated annual
    crops (e.g. maize) are low in late spring and high in summer. Stable pixels
    are *consistent with* a permanent crop; this is an interpretation, not a
    land-use label.
    """
    usable = increase_mask & other_valid & np.isfinite(after_other_season)
    amp = after_summer - after_other_season
    stable = usable & (np.abs(amp) <= amplitude_threshold)
    seasonal = usable & (np.abs(amp) > amplitude_threshold)
    return {
        "increase_pixels": int(increase_mask.sum()),
        "with_valid_second_date": int(usable.sum()),
        "stable_within_year": int(stable.sum()),
        "strongly_seasonal": int(seasonal.sum()),
    }


# ---------------------------------------------------------------------------
# Catalogue and acquisition (network)
# ---------------------------------------------------------------------------


def _relative_orbit(item_props: Mapping[str, Any]) -> str | None:
    m = re.search(r"_R(\d{3})_", str(item_props.get("s2:product_uri", "")))
    return m.group(1) if m else None


def _mgrs_tile(item_props: Mapping[str, Any]) -> str:
    return f"{item_props.get('mgrs:utm_zone')}{item_props.get('mgrs:latitude_band')}{item_props.get('mgrs:grid_square')}"


def effective_offset(stac_offset: float, boa_offset_applied: bool) -> float:
    """Additive reflectance offset to apply when reading Earth Search COGs.

    Processing baseline >= 04.00 adds +1000 DN (BOA_ADD_OFFSET) to L2A pixels.
    Earth Search v1 advertises ``raster:bands.offset = -0.1`` for those items,
    but where ``earthsearch:boa_offset_applied`` is true the stored pixels have
    already been shifted back. Checked on 2026-11-26 for one acquisition
    (2018-08-18, tile 29SNC, AOI alqueva_olive): red-band median DN 1638 in the
    reprocessed item S2A_29SNC_20180818_1_L2A (baseline 05.00, applied=true)
    vs 1632 in S2A_29SNC_20180818_0_L2A (baseline 02.08, no offset). Applying
    -0.1 again pushed 19-40 % of red pixels below zero and saturated NDVI at 1.
    """
    return 0.0 if boa_offset_applied else float(stac_offset)


def item_metadata(item: Any) -> dict[str, Any]:
    p = item.properties
    offset_in_data = bool(p.get("earthsearch:boa_offset_applied"))
    assets = {}
    for key in ("blue", "green", "red", "nir", "swir16", "scl"):
        if key in item.assets:
            a = item.assets[key]
            rb = (a.extra_fields.get("raster:bands") or [{}])[0]
            if key != "scl" and ("scale" not in rb or "offset" not in rb):
                # Never guess calibration: a silent scale=1/offset=0 would change the physical meaning.
                raise ValueError(
                    f"{item.id}/{key}: raster:bands scale/offset missing; refusing to guess reflectance calibration"
                )
            meta_offset = float(rb.get("offset", 0.0) or 0.0)
            assets[key] = {
                "href": a.href,
                "scale": rb.get("scale", 1.0),
                "offset": effective_offset(meta_offset, offset_in_data),
                "offset_in_stac_metadata": meta_offset,
                "nodata": rb.get("nodata"),
                "gsd_m": rb.get("spatial_resolution") or a.extra_fields.get("gsd"),
            }
    return {
        "id": item.id,
        "datetime": p.get("datetime"),
        "platform": p.get("platform"),
        "mgrs_tile": _mgrs_tile(p),
        "relative_orbit": _relative_orbit(p),
        "processing_baseline": p.get("s2:processing_baseline"),
        "product_uri": p.get("s2:product_uri"),
        "eo_cloud_cover": p.get("eo:cloud_cover"),
        "earthsearch_boa_offset_applied": p.get("earthsearch:boa_offset_applied"),
        "epsg": p.get("proj:epsg") or p.get("proj:code"),
        "assets": assets,
        "stac_item_url": f"{EARTH_SEARCH_URL}/collections/{COLLECTION}/items/{item.id}",
        "license": SENTINEL_LICENSE_URL,
        "data_status": "public_observation",
    }


def open_catalog(url: str = EARTH_SEARCH_URL) -> Any:
    from pystac_client import Client

    return Client.open(url)


def fetch_items(item_ids: Sequence[str], url: str = EARTH_SEARCH_URL) -> dict[str, Any]:
    collection = open_catalog(url).get_collection(COLLECTION)
    items = {}
    for iid in item_ids:
        item = collection.get_item(iid)
        if item is None:
            raise LookupError(f"STAC item not found: {iid}")
        items[iid] = item
    return items


def discover_items(
    bbox: Sequence[float],
    start: str,
    end: str,
    max_cloud: float = 5.0,
    url: str = EARTH_SEARCH_URL,
) -> list[dict[str, Any]]:
    """List candidate scenes so the date-selection rule can be audited."""
    search = open_catalog(url).search(
        collections=[COLLECTION],
        bbox=list(bbox),
        datetime=f"{start}/{end}",
        query={"eo:cloud_cover": {"lt": max_cloud}},
        max_items=200,
    )
    rows = []
    for item in search.items():
        p = item.properties
        rows.append(
            {
                "id": item.id,
                "datetime": p.get("datetime"),
                "mgrs_tile": _mgrs_tile(p),
                "relative_orbit": _relative_orbit(p),
                "processing_baseline": p.get("s2:processing_baseline"),
                "eo_cloud_cover": p.get("eo:cloud_cover"),
            }
        )
    return sorted(rows, key=lambda r: r["datetime"])


@dataclass
class Grid:
    crs: Any
    transform: Any
    width: int
    height: int
    window_bounds: tuple[float, float, float, float]

    @property
    def pixel_size(self) -> float:
        return float(abs(self.transform.a))

    def as_dict(self) -> dict[str, Any]:
        return {
            "crs": str(self.crs),
            "transform": list(self.transform)[:6],
            "width": self.width,
            "height": self.height,
            "pixel_size_m": self.pixel_size,
            "bounds": list(self.window_bounds),
        }


def _gdal_env() -> Any:
    import rasterio

    return rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        AWS_NO_SIGN_REQUEST="YES",
        CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
        GDAL_HTTP_MAX_RETRY="4",
        GDAL_HTTP_RETRY_DELAY="2",
    )


def reference_grid(item_meta: Mapping[str, Any], bbox: Sequence[float]) -> Grid:
    """10 m grid of the item's tile clipped to the AOI (snapped to tile pixels)."""
    import rasterio
    from rasterio.warp import transform_bounds
    from rasterio.windows import from_bounds

    with _gdal_env(), rasterio.open(item_meta["assets"]["red"]["href"]) as ds:
        b = transform_bounds("EPSG:4326", ds.crs, *bbox, densify_pts=21)
        raw = from_bounds(*b, transform=ds.transform)
        # Snap to even 10 m pixels so that 20 m assets (SCL, SWIR) share pixel edges.
        col0 = int(math.floor(raw.col_off / 2) * 2)
        row0 = int(math.floor(raw.row_off / 2) * 2)
        col1 = int(math.ceil((raw.col_off + raw.width) / 2) * 2)
        row1 = int(math.ceil((raw.row_off + raw.height) / 2) * 2)
        win = rasterio.windows.Window(col0, row0, col1 - col0, row1 - row0)
        win = win.intersection(rasterio.windows.Window(0, 0, ds.width, ds.height))
        tr = ds.window_transform(win)
        bounds = rasterio.windows.bounds(win, ds.transform)
        return Grid(ds.crs, tr, int(win.width), int(win.height), tuple(bounds))


def read_band(
    asset: Mapping[str, Any], grid: Grid, resampling: str = "nearest", attempts: int = 3
) -> np.ndarray:
    """Read one asset on the reference grid, retrying transient HTTP short reads."""
    import time

    from rasterio.errors import RasterioIOError

    for attempt in range(1, attempts + 1):
        try:
            return _read_band_once(asset, grid, resampling)
        except RasterioIOError:
            if attempt == attempts:
                raise
            time.sleep(2 * attempt)
    raise AssertionError("unreachable")


def _read_band_once(
    asset: Mapping[str, Any], grid: Grid, resampling: str
) -> np.ndarray:
    """Read one asset on the reference grid; asserts CRS/grid compatibility."""
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.windows import from_bounds

    with _gdal_env(), rasterio.open(asset["href"]) as ds:
        if ds.crs != grid.crs:
            raise ValueError(
                f"CRS mismatch {ds.crs} vs {grid.crs}; items must share an MGRS tile"
            )
        win = from_bounds(*grid.window_bounds, transform=ds.transform)
        # Pixel edges must coincide (all S2 tile grids are multiples of 10 m from the same origin).
        if (
            abs(win.col_off - round(win.col_off)) > 1e-6
            or abs(win.row_off - round(win.row_off)) > 1e-6
        ):
            raise ValueError("Grid misalignment between assets")
        data = ds.read(
            1,
            window=win,
            out_shape=(grid.height, grid.width),
            resampling=getattr(Resampling, resampling),
        )
        return np.asarray(data)


@dataclass
class Observation:
    meta: dict[str, Any]
    bands: dict[str, np.ndarray]
    scl: np.ndarray
    valid: np.ndarray
    index: np.ndarray


def load_observation(
    item_meta: Mapping[str, Any],
    grid: Grid,
    index: str,
    valid_scl: Sequence[int],
    rgb: bool = False,
) -> Observation:
    needed = set(INDEX_BANDS[index]) | ({"red", "green", "blue"} if rgb else set())
    bands = {}
    for key in sorted(needed):
        a = item_meta["assets"][key]
        dn = read_band(a, grid)
        bands[key] = to_reflectance(dn, a["scale"], a["offset"], a.get("nodata", 0))
    scl = read_band(item_meta["assets"]["scl"], grid)
    valid = scl_valid_mask(scl, valid_scl)
    for arr in bands.values():
        valid &= np.isfinite(arr)
    idx = compute_index(index, bands)
    return Observation(dict(item_meta), bands, scl, valid, idx)


# ---------------------------------------------------------------------------
# Run bookkeeping
# ---------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_state(repo: Path) -> dict[str, Any]:
    def run(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", *args], cwd=repo, capture_output=True, text=True, check=True
            ).stdout.strip()  # nosec B603 B607
        except Exception:
            return "unknown"

    status = run(
        "status",
        "--porcelain",
        "--",
        "pipeline/src/case_study.py",
        "pipeline/run_case_study.py",
        "pipeline/case_studies",
    )
    return {
        "commit": run("rev-parse", "HEAD"),
        "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
        "case_study_code_dirty": bool(status) if status != "unknown" else None,
    }


def environment_versions() -> dict[str, str]:
    import importlib.metadata as md

    out = {"python": sys.version.split()[0], "platform": platform.platform()}
    for pkg in ("numpy", "scipy", "rasterio", "pystac-client", "pyproj", "matplotlib"):
        try:
            out[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            out[pkg] = "not-installed"
    try:
        import rasterio

        out["gdal"] = rasterio.__gdal_version__
    except Exception:  # pragma: no cover
        pass
    return out


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def config_hash(cfg_raw: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(cfg_raw, sort_keys=True).encode("utf-8")
    ).hexdigest()
