"""Second Sentinel-2 L2A provider: Microsoft Planetary Computer (PC).

Purpose
-------
Read the same acquisition that the case study takes from Earth Search
(``case_study.EARTH_SEARCH_URL``) from a second, independent public
catalogue, on the identical 10 m grid, so that the two providers can be
compared pixel by pixel (``pipeline/run_interop_check.py``).

What differs from Earth Search (each point is handled below)
-----------------------------------------------------------
* Item IDs. Earth Search: ``S2A_29SNC_20180818_1_L2A`` (platform, tile, date,
  sequence). PC: ``S2A_MSIL2A_20180818T112111_R037_T29SNC_20201011T032718``
  (the ESA product name without the ``_Nxxxx`` baseline and ``.SAFE``). The
  two are matched on the ESA product URI fields that do not depend on the
  processing run: platform, sensing start, relative orbit and MGRS tile
  (:func:`acquisition_key`).
* Asset keys. Earth Search uses common names (``red``, ``nir``, ``scl``); PC
  uses band names (``B04``, ``B08``, ``SCL``) (:data:`PC_ASSET_KEYS`).
* Access. PC assets live in Azure Blob Storage and need a short-lived,
  anonymous SAS token appended to each URL (:func:`fetch_sas_token`,
  :func:`sign_href`). Tokens and signed URLs are kept in memory only; use
  :func:`redact_url` before logging any text that might contain one.
* Calibration. PC assets carry no ``raster:bands`` scale/offset. The values
  come from the product metadata file ``MTD_MSIL2A.xml`` (asset
  ``product-metadata``): ``BOA_QUANTIFICATION_VALUE`` (10000) and, for
  processing baseline >= 04.00, a per-band ``BOA_ADD_OFFSET`` (-1000). PC
  serves the original ESA encoding, so the offset is applied here:
  ``reflectance = (DN + BOA_ADD_OFFSET) / BOA_QUANTIFICATION_VALUE``
  (:func:`parse_product_metadata`, :func:`band_calibration`). If a baseline
  >= 04.00 product lacks the offset, or a pre-04.00 product has one, the
  code raises instead of guessing.

Pure helpers are unit-tested offline in ``pipeline/tests/test_provider_pc.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping, Sequence

import numpy as np

from pipeline.src import case_study as cs

PC_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
PC_COLLECTION = "sentinel-2-l2a"
PC_SAS_TOKEN_URL = (
    "https://planetarycomputer.microsoft.com/api/sas/v1/token/{collection}"
)

# Earth Search common name -> PC asset key.
PC_ASSET_KEYS: dict[str, str] = {
    "blue": "B02",
    "green": "B03",
    "red": "B04",
    "nir": "B08",
    "swir16": "B11",
    "scl": "SCL",
}
# Earth Search common name -> ``physicalBand`` label used in MTD_MSIL2A.xml.
MTD_PHYSICAL_BAND: dict[str, str] = {
    "blue": "B2",
    "green": "B3",
    "red": "B4",
    "nir": "B8",
    "swir16": "B11",
}
# First processing baseline whose L2A pixels carry BOA_ADD_OFFSET (ESA, Jan 2022).
OFFSET_FROM_BASELINE: tuple[int, int] = (4, 0)

_PRODUCT_URI_RE = re.compile(
    r"^(?P<platform>S2[A-D])_MSI(?P<level>L[12][AC])_(?P<sensing>\d{8}T\d{6})"
    r"_N(?P<baseline>\d{4})_R(?P<orbit>\d{3})_T(?P<tile>\d{2}[A-Z]{3})"
    r"_(?P<generation>\d{8}T\d{6})(?:\.SAFE)?$"
)
_PC_ID_RE = re.compile(
    r"^(?P<platform>S2[A-D])_MSI(?P<level>L[12][AC])_(?P<sensing>\d{8}T\d{6})"
    r"_R(?P<orbit>\d{3})_T(?P<tile>\d{2}[A-Z]{3})_(?P<generation>\d{8}T\d{6})$"
)
_ES_ID_RE = re.compile(
    r"^(?P<platform>S2[A-D])_(?P<tile>\d{2}[A-Z]{3})_(?P<date>\d{8})"
    r"_(?P<sequence>\d+)_(?P<level>L[12][AC])$"
)
_URL_QUERY_RE = re.compile(r"(https?://[^\s?'\"]+)\?[^\s'\"]*")


# ---------------------------------------------------------------------------
# Pure helpers: identifiers
# ---------------------------------------------------------------------------


def parse_earth_search_id(item_id: str) -> dict[str, Any]:
    """Split an Earth Search v1 item ID (``S2A_29SNC_20180818_1_L2A``)."""
    m = _ES_ID_RE.match(item_id)
    if not m:
        raise ValueError(f"Not an Earth Search Sentinel-2 item ID: {item_id!r}")
    d = m.group("date")
    return {
        "platform": m.group("platform"),
        "tile": m.group("tile"),
        "date": f"{d[:4]}-{d[4:6]}-{d[6:]}",
        "sequence": int(m.group("sequence")),
        "level": m.group("level"),
    }


def parse_product_uri(uri: str) -> dict[str, str]:
    """Split an ESA product name (``S2A_MSIL2A_<sensing>_N<baseline>_R<orbit>_T<tile>_<gen>.SAFE``)."""
    m = _PRODUCT_URI_RE.match(uri)
    if not m:
        raise ValueError(f"Not a Sentinel-2 product URI: {uri!r}")
    b = m.group("baseline")
    return {
        "platform": m.group("platform"),
        "level": m.group("level"),
        "sensing_start": m.group("sensing"),
        "processing_baseline": f"{b[:2]}.{b[2:]}",
        "relative_orbit": m.group("orbit"),
        "tile": m.group("tile"),
        "generation_time": m.group("generation"),
    }


def parse_pc_item_id(item_id: str) -> dict[str, str]:
    """Split a PC item ID (product name without baseline and ``.SAFE``)."""
    m = _PC_ID_RE.match(item_id)
    if not m:
        raise ValueError(f"Not a Planetary Computer Sentinel-2 item ID: {item_id!r}")
    return {
        "platform": m.group("platform"),
        "level": m.group("level"),
        "sensing_start": m.group("sensing"),
        "relative_orbit": m.group("orbit"),
        "tile": m.group("tile"),
        "generation_time": m.group("generation"),
    }


def acquisition_key(parsed: Mapping[str, str]) -> tuple[str, str, str, str]:
    """Fields that identify one acquisition independently of the processing run."""
    return (
        parsed["platform"],
        parsed["sensing_start"],
        parsed["relative_orbit"],
        parsed["tile"],
    )


def baseline_tuple(baseline: str) -> tuple[int, int]:
    """``"05.00"`` -> ``(5, 0)``. Rejects anything that is not ``NN.NN``."""
    m = re.fullmatch(r"(\d{1,2})\.(\d{2})", baseline.strip())
    if not m:
        raise ValueError(f"Unrecognised processing baseline {baseline!r}")
    return int(m.group(1)), int(m.group(2))


def baseline_has_boa_offset(baseline: str) -> bool:
    return baseline_tuple(baseline) >= OFFSET_FROM_BASELINE


def select_match(
    es_product_uri: str, candidates: Sequence[Mapping[str, Any]]
) -> tuple[Mapping[str, Any], list[Mapping[str, Any]], str]:
    """Pick the PC candidate that shows the same acquisition as the Earth Search item.

    ``candidates`` are mappings with at least ``id`` and ``product_uri``.
    Returns ``(chosen, all_matches, rule)``. Several matches can exist when a
    provider keeps more than one processing run; the one with the Earth Search
    baseline is preferred, otherwise the most recent baseline.
    """
    target = parse_product_uri(es_product_uri)
    key = acquisition_key(target)
    matches = [
        c
        for c in candidates
        if acquisition_key(parse_product_uri(c["product_uri"])) == key
    ]
    if not matches:
        raise LookupError(
            f"No Planetary Computer item with platform/sensing/orbit/tile {key}"
        )
    same = [
        c
        for c in matches
        if parse_product_uri(c["product_uri"])["processing_baseline"]
        == target["processing_baseline"]
    ]
    if same:
        return same[0], list(matches), "same acquisition, same processing baseline"
    best = max(
        matches,
        key=lambda c: baseline_tuple(
            parse_product_uri(c["product_uri"])["processing_baseline"]
        ),
    )
    return (
        best,
        list(matches),
        "same acquisition; Earth Search baseline not available on PC, highest PC baseline taken",
    )


# ---------------------------------------------------------------------------
# Pure helpers: calibration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProductCalibration:
    """Radiometric encoding read from MTD_MSIL2A.xml."""

    processing_baseline: str
    quantification_value: float
    add_offsets: dict[str, int] = field(default_factory=dict)  # physicalBand -> DN
    nodata: int = 0
    saturated: int | None = 65535


def parse_product_metadata(xml_text: str) -> ProductCalibration:
    """Extract baseline, BOA quantification value and per-band BOA_ADD_OFFSET.

    Uses fixed tag patterns of the ESA L2A user product format (PSD 14.x and
    later) instead of a full XML parser. Raises if a required tag is missing.
    """
    pb = re.search(
        r"<PROCESSING_BASELINE>\s*([^<\s]+)\s*</PROCESSING_BASELINE>", xml_text
    )
    if not pb:
        raise ValueError("PROCESSING_BASELINE missing from product metadata")
    qv = re.search(
        r"<BOA_QUANTIFICATION_VALUE[^>]*>\s*([0-9.]+)\s*</BOA_QUANTIFICATION_VALUE>",
        xml_text,
    )
    if not qv:
        raise ValueError("BOA_QUANTIFICATION_VALUE missing from product metadata")
    band_names = {
        int(i): name
        for i, name in re.findall(
            r'<Spectral_Information\s+bandId="(\d+)"\s+physicalBand="([^"]+)"', xml_text
        )
    }
    offsets: dict[str, int] = {}
    for band_id, value in re.findall(
        r'<BOA_ADD_OFFSET\s+band_id="(\d+)"\s*>\s*(-?\d+)\s*</BOA_ADD_OFFSET>', xml_text
    ):
        bid = int(band_id)
        if bid not in band_names:
            raise ValueError(
                f"BOA_ADD_OFFSET for band_id {bid} but no Spectral_Information entry"
            )
        offsets[band_names[bid]] = int(value)
    special = dict(
        (text, int(idx))
        for text, idx in re.findall(
            r"<SPECIAL_VALUE_TEXT>\s*([A-Z_]+)\s*</SPECIAL_VALUE_TEXT>\s*"
            r"<SPECIAL_VALUE_INDEX>\s*(\d+)\s*</SPECIAL_VALUE_INDEX>",
            xml_text,
        )
    )
    return ProductCalibration(
        processing_baseline=pb.group(1),
        quantification_value=float(qv.group(1)),
        add_offsets=offsets,
        nodata=special.get("NODATA", 0),
        saturated=special.get("SATURATED"),
    )


def band_calibration(cal: ProductCalibration, band: str) -> tuple[float, float]:
    """Return ``(scale, offset)`` so that ``reflectance = DN * scale + offset``.

    ``band`` is an Earth Search common name (``red``, ``nir`` ...). The offset
    must be present exactly when the baseline is >= 04.00; anything else is an
    inconsistent product and raises rather than guessing.
    """
    if cal.quantification_value <= 0:
        raise ValueError("BOA_QUANTIFICATION_VALUE must be positive")
    physical = MTD_PHYSICAL_BAND[band]
    expects_offset = baseline_has_boa_offset(cal.processing_baseline)
    if expects_offset and physical not in cal.add_offsets:
        raise ValueError(
            f"Baseline {cal.processing_baseline} >= 04.00 but no BOA_ADD_OFFSET for {physical}; refusing to guess"
        )
    if not expects_offset and cal.add_offsets.get(physical, 0) != 0:
        raise ValueError(
            f"Baseline {cal.processing_baseline} < 04.00 but BOA_ADD_OFFSET present for {physical}"
        )
    add = cal.add_offsets.get(physical, 0)
    return 1.0 / cal.quantification_value, add / cal.quantification_value


# ---------------------------------------------------------------------------
# Pure helpers: provider comparison
# ---------------------------------------------------------------------------


def difference_stats(
    a: np.ndarray, b: np.ndarray, mask: np.ndarray, tolerance: float = 0.01
) -> dict[str, float | int]:
    """Statistics of ``a - b`` over ``mask`` (and finite values only)."""
    m = mask & np.isfinite(a) & np.isfinite(b)
    d = a[m].astype("float64") - b[m].astype("float64")
    if d.size == 0:
        return {"n": 0}
    ad = np.abs(d)
    return {
        "n": int(d.size),
        "mean_diff": float(d.mean()),
        "median_diff": float(np.median(d)),
        "median_abs_diff": float(np.median(ad)),
        "p95_abs_diff": float(np.percentile(ad, 95)),
        "p99_abs_diff": float(np.percentile(ad, 99)),
        "max_abs_diff": float(ad.max()),
        "tolerance": float(tolerance),
        "share_abs_diff_gt_tolerance": float((ad > tolerance).mean()),
        "share_exactly_equal": float((d == 0).mean()),
    }


def flag_agreement(
    flag_a: np.ndarray, flag_b: np.ndarray, mask: np.ndarray
) -> dict[str, float | int]:
    """Agreement of two boolean change flags over ``mask``, with Cohen's kappa."""
    a = flag_a[mask].astype(bool)
    b = flag_b[mask].astype(bool)
    n = int(a.size)
    if n == 0:
        return {"n": 0}
    both = int((a & b).sum())
    a_only = int((a & ~b).sum())
    b_only = int((~a & b).sum())
    neither = n - both - a_only - b_only
    po = (both + neither) / n
    pa, pb = (both + a_only) / n, (both + b_only) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    union = both + a_only + b_only
    return {
        "n": n,
        "both_flagged": both,
        "only_first": a_only,
        "only_second": b_only,
        "neither": neither,
        "agreement_share": float(po),
        "cohen_kappa": float(kappa),
        "jaccard_of_flagged": float(both / union) if union else float("nan"),
    }


# ---------------------------------------------------------------------------
# Pure helpers: URLs
# ---------------------------------------------------------------------------


def sign_href(href: str, token: str) -> str:
    """Append a SAS token (query string) to an Azure Blob URL."""
    token = token.lstrip("?")
    return f"{href}{'&' if '?' in href else '?'}{token}"


def strip_query(href: str) -> str:
    return href.split("?", 1)[0]


def redact_url(text: str) -> str:
    """Remove query strings (SAS tokens) from every URL inside ``text``."""
    return _URL_QUERY_RE.sub(r"\1?<redacted>", text)


# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------


def fetch_sas_token(collection: str = PC_COLLECTION, timeout: float = 60) -> str:
    """Anonymous, short-lived read token for one PC collection. Keep in memory only."""
    import requests

    r = requests.get(PC_SAS_TOKEN_URL.format(collection=collection), timeout=timeout)
    r.raise_for_status()
    return str(r.json()["token"])


def open_pc_catalog(url: str = PC_STAC_URL) -> Any:
    from pystac_client import Client

    return Client.open(url)


def pc_candidates(tile: str, date: str, url: str = PC_STAC_URL) -> list[Any]:
    """All PC L2A items for one MGRS tile on one UTC day."""
    search = open_pc_catalog(url).search(
        collections=[PC_COLLECTION],
        datetime=date,
        query={"s2:mgrs_tile": {"eq": tile}},
        max_items=50,
    )
    return list(search.items())


def find_pc_match(es_meta: Mapping[str, Any]) -> tuple[Any, dict[str, Any]]:
    """Find the PC item for an Earth Search item (metadata from ``cs.item_metadata``)."""
    parsed = parse_earth_search_id(es_meta["id"])
    items = pc_candidates(parsed["tile"], parsed["date"])
    rows = [
        {
            "id": it.id,
            "product_uri": it.properties["s2:product_uri"],
            "processing_baseline": it.properties.get("s2:processing_baseline"),
        }
        for it in items
    ]
    chosen, matches, rule = select_match(es_meta["product_uri"], rows)
    item = next(it for it in items if it.id == chosen["id"])
    report = {
        "search": {
            "collection": PC_COLLECTION,
            "datetime": parsed["date"],
            "query": {"s2:mgrs_tile": parsed["tile"]},
        },
        "candidates_same_day_and_tile": rows,
        "matching_items": [m["id"] for m in matches],
        "match_rule": rule,
        "match_key": dict(
            zip(
                ("platform", "sensing_start", "relative_orbit", "tile"),
                acquisition_key(parse_product_uri(es_meta["product_uri"])),
            )
        ),
    }
    return item, report


def fetch_text(href: str, token: str, timeout: float = 60) -> str:
    import requests

    r = requests.get(sign_href(href, token), timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code} for {strip_query(href)}")
    return r.text


def pc_item_metadata(item: Any, token: str) -> dict[str, Any]:
    """Unsigned metadata for one PC item plus calibration from MTD_MSIL2A.xml."""
    p = item.properties
    mtd_href = item.assets["product-metadata"].href
    cal = parse_product_metadata(fetch_text(mtd_href, token))
    if cal.processing_baseline != p.get("s2:processing_baseline"):
        raise ValueError(
            f"{item.id}: STAC baseline {p.get('s2:processing_baseline')} != product metadata {cal.processing_baseline}"
        )
    assets: dict[str, dict[str, Any]] = {}
    for key in ("red", "nir", "scl"):
        a = item.assets[PC_ASSET_KEYS[key]]
        if key == "scl":
            scale, offset = 1.0, 0.0
        else:
            scale, offset = band_calibration(cal, key)
        assets[key] = {
            "pc_asset_key": PC_ASSET_KEYS[key],
            "href": strip_query(a.href),
            "scale": scale,
            "offset": offset,
            "nodata": cal.nodata,
            "gsd_m": a.extra_fields.get("gsd"),
            "raster_bands_in_stac": "raster:bands" in a.extra_fields,
        }
    return {
        "id": item.id,
        "datetime": p.get("datetime"),
        "platform": p.get("platform"),
        "mgrs_tile": p.get("s2:mgrs_tile"),
        "processing_baseline": p.get("s2:processing_baseline"),
        "product_uri": p.get("s2:product_uri"),
        "granule_id": p.get("s2:granule_id"),
        "generation_time": p.get("s2:generation_time"),
        "eo_cloud_cover": p.get("eo:cloud_cover"),
        "epsg": p.get("proj:epsg") or p.get("proj:code"),
        "calibration": {
            "source": "product-metadata asset (MTD_MSIL2A.xml)",
            "product_metadata_href": strip_query(mtd_href),
            "processing_baseline": cal.processing_baseline,
            "boa_quantification_value": cal.quantification_value,
            "boa_add_offset_dn": {
                k: cal.add_offsets.get(MTD_PHYSICAL_BAND[k]) for k in ("red", "nir")
            },
            "nodata_dn": cal.nodata,
            "saturated_dn": cal.saturated,
            "rule": "reflectance = (DN + BOA_ADD_OFFSET) / BOA_QUANTIFICATION_VALUE; offset required iff baseline >= 04.00",
        },
        "assets": assets,
        "stac_item_url": f"{PC_STAC_URL}/collections/{PC_COLLECTION}/items/{item.id}",
        "license": cs.SENTINEL_LICENSE_URL,
        "data_status": "public_observation",
    }


def _signed_asset(asset: Mapping[str, Any], token: str) -> dict[str, Any]:
    out = dict(asset)
    out["href"] = sign_href(asset["href"], token)
    return out


def grid_alignment(
    es_href: str, pc_href: str, grid: cs.Grid, token: str
) -> dict[str, Any]:
    """Compare the 10 m tile grids of the two providers and locate the AOI window."""
    import rasterio
    from rasterio.windows import from_bounds

    with cs._gdal_env():
        with rasterio.open(es_href) as es_ds, rasterio.open(
            sign_href(pc_href, token)
        ) as pc_ds:
            es_tr, pc_tr = es_ds.transform, pc_ds.transform
            win = from_bounds(*grid.window_bounds, transform=pc_ds.transform)
            same_crs = es_ds.crs == pc_ds.crs
            info = {
                "crs_earth_search": str(es_ds.crs),
                "crs_planetary_computer": str(pc_ds.crs),
                "same_crs": bool(same_crs),
                "transform_earth_search": list(es_tr)[:6],
                "transform_planetary_computer": list(pc_tr)[:6],
                "tile_shape_earth_search": [es_ds.height, es_ds.width],
                "tile_shape_planetary_computer": [pc_ds.height, pc_ds.width],
                "origin_shift_m": [pc_tr.c - es_tr.c, pc_tr.f - es_tr.f],
                "pc_window_col_row_off": [float(win.col_off), float(win.row_off)],
            }
    integer_window = (
        abs(win.col_off - round(win.col_off)) < 1e-6
        and abs(win.row_off - round(win.row_off)) < 1e-6
    )
    info["identical_transform"] = bool(list(es_tr)[:6] == list(pc_tr)[:6])
    info["aoi_window_on_whole_pixels"] = bool(integer_window)
    info["aligned"] = bool(
        same_crs and integer_window and es_tr.a == pc_tr.a and es_tr.e == pc_tr.e
    )
    return info


@dataclass
class PCObservation:
    observation: cs.Observation
    dn: dict[str, np.ndarray]


def load_pc_ndvi(
    pc_meta: Mapping[str, Any],
    grid: cs.Grid,
    valid_scl: Sequence[int],
    token: str,
) -> PCObservation:
    """Read red, NIR and SCL from PC on ``grid`` and compute NDVI with PC calibration."""
    bands: dict[str, np.ndarray] = {}
    dn: dict[str, np.ndarray] = {}
    for key in ("nir", "red"):
        a = pc_meta["assets"][key]
        raw = cs.read_band(_signed_asset(a, token), grid)
        dn[key] = raw
        bands[key] = cs.to_reflectance(raw, a["scale"], a["offset"], a["nodata"])
    scl = cs.read_band(_signed_asset(pc_meta["assets"]["scl"], token), grid)
    valid = cs.scl_valid_mask(scl, valid_scl)
    for arr in bands.values():
        valid &= np.isfinite(arr)
    idx = cs.compute_index("ndvi", bands)
    return PCObservation(cs.Observation(dict(pc_meta), bands, scl, valid, idx), dn)
