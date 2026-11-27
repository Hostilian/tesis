"""Independent reference: Portuguese land-use/land-cover map (COS, DGT).

COS Série 2 (COS2018v4, COS2025v1) is produced by the Direção-Geral do
Território by visual interpretation of very high resolution orthophotos (minimum mapping unit
0.5 ha for both COS2018v4 and COS2025v1, which share one specification; DGT, July 2026) and is
published as open data under CC-BY via an OGC API - Features service.

It is used here as an *independent* reference for the Sentinel-2 change
flags: it was not derived from this pipeline and it was not used to tune it.
Agreement with COS is not ground truth accuracy: COS has its own
interpretation errors, generalisation (MMU) and reference-date mismatch.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

OGC_API = "https://ogcapi.dgterritorio.gov.pt"
COS_LICENSE = "CC-BY (dados.gov.pt: 'Carta de Uso e Ocupação do Solo (COS) - Série 2 - (2018v4 - 2025v1)')"
COS_ATTRIBUTION = "Carta de Uso e Ocupação do Solo (COS) 2018v4 / 2025v1, Direção-Geral do Território (DGT)"
COS_DATASET_PAGE = "https://dados.gov.pt/datasets/carta-de-uso-e-ocupacao-do-solo-cos-serie-2-2018v4-2025v1"

COLLECTIONS = {
    "2018": ("cos2018v4", "cos18v4"),
    "2025": ("cos2025v1", "cos25v1"),
}

PERMANENT_CROP_PREFIX = "2.2."  # 2.2.1 vineyards, 2.2.2 orchards, 2.2.3 olive groves
MINING_PREFIXES = (
    "1.6.",
)  # 1.6.x mines and quarries (e.g. 1.6.1.1 "Minas a céu aberto") in COS Série 2


def fetch_features(
    collection: str, bbox: Sequence[float], page_size: int = 500, timeout: int = 120
) -> list[dict[str, Any]]:
    """Page through an OGC API - Features collection for a WGS84 bbox."""
    import requests

    url: str | None = f"{OGC_API}/collections/{collection}/items"
    params: dict[str, Any] | None = {
        "f": "json",
        "limit": page_size,
        "bbox": ",".join(f"{v:.6f}" for v in bbox),
    }
    feats: list[dict[str, Any]] = []
    while url:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        d = r.json()
        feats.extend(d.get("features", []))
        nxt = [link["href"] for link in d.get("links", []) if link.get("rel") == "next"]
        url, params = (nxt[0], None) if nxt else (None, None)
    return feats


def class_codes(features: Iterable[Mapping[str, Any]], prefix: str) -> list[str]:
    return sorted({str(f["properties"][f"{prefix}_n4_c"]) for f in features})


def rasterize_classes(
    features: Sequence[Mapping[str, Any]], prefix: str, grid: Any
) -> tuple[NDArray[Any], list[str]]:
    """Burn level-4 class codes onto the case-study grid; returns (index raster, code list)."""
    from pyproj import Transformer
    from rasterio import features as rfeatures
    from shapely.geometry import mapping, shape
    from shapely.ops import transform as shp_transform

    codes = class_codes(features, prefix)
    lookup = {c: i + 1 for i, c in enumerate(codes)}  # 0 = no reference polygon
    to_grid = Transformer.from_crs("EPSG:4326", grid.crs, always_xy=True).transform
    shapes = []
    for f in features:
        geom = shp_transform(to_grid, shape(f["geometry"]))
        shapes.append((mapping(geom), lookup[str(f["properties"][f"{prefix}_n4_c"])]))
    raster = rfeatures.rasterize(
        shapes,
        out_shape=(grid.height, grid.width),
        transform=grid.transform,
        fill=0,
        dtype="uint16",
        all_touched=False,
    )
    return raster, codes


def code_mask(
    raster: NDArray[Any], codes: Sequence[str], predicate: Any
) -> NDArray[Any]:
    hits = [i + 1 for i, c in enumerate(codes) if predicate(c)]
    return np.isin(raster, hits)


def agreement_matrix(
    flags: NDArray[Any],
    reference: Mapping[str, NDArray[Any]],
    valid: NDArray[Any],
    pixel_area_m2: float,
) -> list[dict[str, Any]]:
    """Share of each reference category flagged as increase (1) / decrease (2) / none (0)."""
    rows = []
    n_valid = int(valid.sum())
    inc_total = int(((flags == 1) & valid).sum())
    dec_total = int(((flags == 2) & valid).sum())
    for name, ref in reference.items():
        m = ref & valid
        n = int(m.sum())
        rows.append(
            {
                "reference_category": name,
                "pixels": n,
                "area_ha": n * pixel_area_m2 / 10_000,
                "share_of_aoi": n / n_valid if n_valid else None,
                "share_of_all_increase_flags_in_category": (
                    int(((flags == 1) & m).sum()) / inc_total if inc_total else None
                ),
                "share_of_all_decrease_flags_in_category": (
                    int(((flags == 2) & m).sum()) / dec_total if dec_total else None
                ),
                "share_flagged_increase": float((flags[m] == 1).mean()) if n else None,
                "share_flagged_decrease": float((flags[m] == 2).mean()) if n else None,
                "share_not_flagged": float((flags[m] == 0).mean()) if n else None,
            }
        )
    return rows


def binary_agreement(pred: NDArray[Any], ref: NDArray[Any]) -> dict[str, Any]:
    tp = int((pred & ref).sum())
    fp = int((pred & ~ref).sum())
    fn = int((~pred & ref).sum())
    tn = int((~pred & ~ref).sum())
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision and recall else None
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def polygon_units(
    features_2025: Sequence[Mapping[str, Any]], prefix: str, grid: Any
) -> NDArray[Any]:
    """Raster of 2025 COS polygon ids (1..n) used as the evaluation unit."""
    from pyproj import Transformer
    from rasterio import features as rfeatures
    from shapely.geometry import mapping, shape
    from shapely.ops import transform as shp_transform

    to_grid = Transformer.from_crs("EPSG:4326", grid.crs, always_xy=True).transform
    shapes = [
        (mapping(shp_transform(to_grid, shape(f["geometry"]))), i + 1)
        for i, f in enumerate(features_2025)
    ]
    units = rfeatures.rasterize(
        shapes,
        out_shape=(grid.height, grid.width),
        transform=grid.transform,
        fill=0,
        dtype="int32",
    )
    return np.asarray(units)


def polygon_agreement(
    units: NDArray[Any],
    pred_pixels: NDArray[Any],
    ref_pixels: NDArray[Any],
    valid: NDArray[Any],
    min_pixels: int,
    share: float = 0.5,
) -> dict[str, Any]:
    """Unit = 2025 COS polygon clipped to the AOI (>= min_pixels valid pixels).

    A unit is reference-positive if >= ``share`` of its pixels are in the
    reference category, and detected if >= ``share`` of its pixels are flagged.
    Polygon units reduce the pixel-level spatial autocorrelation problem but do
    not remove it (neighbouring polygons are not independent).
    """
    ids = units[valid & (units > 0)]
    n_ids = int(units.max()) + 1
    count = np.bincount(ids, minlength=n_ids)
    pred_c = np.bincount(units[valid & (units > 0) & pred_pixels], minlength=n_ids)
    ref_c = np.bincount(units[valid & (units > 0) & ref_pixels], minlength=n_ids)
    keep = count >= min_pixels
    keep[0] = False
    pred = (pred_c[keep] / count[keep]) >= share
    ref = (ref_c[keep] / count[keep]) >= share
    out = binary_agreement(pred, ref)
    out.update(
        {
            "units_evaluated": int(keep.sum()),
            "min_unit_pixels": min_pixels,
            "majority_share": share,
        }
    )
    return out
