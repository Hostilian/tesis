"""Offline tests for the Sentinel-2 case-study method and its public artifacts.

All arrays below are small synthetic fixtures (data_status: synthetic_demonstration).
They check arithmetic and bookkeeping, not scientific validity.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest

from pipeline.src import case_study as cs
from pipeline.src import reference_cos as rc

REPO = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO / "pipeline" / "case_studies"
PUBLIC = REPO / "docs" / "case-study" / "data"


# --- reflectance and indices -------------------------------------------------


def test_effective_offset_respects_earth_search_flag():
    assert cs.effective_offset(-0.1, boa_offset_applied=True) == 0.0
    assert cs.effective_offset(-0.1, boa_offset_applied=False) == -0.1
    assert cs.effective_offset(0.0, boa_offset_applied=False) == 0.0


def test_to_reflectance_scale_offset_and_nodata():
    dn = np.array([[0, 1000, 2500]], dtype="uint16")
    out = cs.to_reflectance(dn, 0.0001, -0.1, nodata=0)
    assert np.isnan(out[0, 0])
    assert out[0, 1] == pytest.approx(0.0, abs=1e-7)
    assert out[0, 2] == pytest.approx(0.15, abs=1e-6)


def test_normalized_difference_bounds_and_zero_denominator():
    a = np.array([0.5, 0.0, 0.2, np.nan], dtype="float32")
    b = np.array([0.1, 0.0, 0.2, 0.1], dtype="float32")
    nd = cs.normalized_difference(a, b)
    assert nd[0] == pytest.approx(0.4 / 0.6, rel=1e-5)
    assert np.isnan(nd[1]) and np.isnan(nd[3])
    assert nd[2] == 0.0


def test_bsi_formula():
    bands = {k: np.array([v], dtype="float32") for k, v in {"blue": 0.05, "red": 0.10, "nir": 0.20, "swir16": 0.30}.items()}
    expected = ((0.30 + 0.10) - (0.20 + 0.05)) / ((0.30 + 0.10) + (0.20 + 0.05))
    assert cs.compute_index("bsi", bands)[0] == pytest.approx(expected, rel=1e-5)


def test_scl_mask_keeps_only_clear_land_and_water():
    scl = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], dtype="uint8")
    assert cs.scl_valid_mask(scl).tolist() == [False] * 4 + [True] * 3 + [False] * 5


def test_difference_uses_joint_valid_pixels_only():
    before = np.array([0.2, 0.2, np.nan, 0.2], dtype="float32")
    after = np.array([0.5, 0.1, 0.4, 0.6], dtype="float32")
    vb = np.array([True, True, True, False])
    va = np.array([True, True, True, True])
    delta, joint = cs.difference(before, after, vb, va)
    assert joint.tolist() == [True, True, False, False]
    assert delta[0] == pytest.approx(0.3) and delta[1] == pytest.approx(-0.1)
    assert np.isnan(delta[2]) and np.isnan(delta[3])


# --- thresholds, patches, resolution ------------------------------------------


def test_threshold_table_counts():
    main = np.array([0.5, -0.5, 0.05, np.nan], dtype="float32")
    control = np.array([0.0, 0.25, -0.01, 0.02], dtype="float32")
    rows = cs.threshold_table(main, control, [0.1, 0.3])
    assert rows[0]["main_valid_pixels"] == 3
    assert rows[0]["main_increase_pixels"] == 1 and rows[0]["main_decrease_pixels"] == 1
    assert rows[0]["control_flagged_pixels"] == 1
    assert rows[1]["control_flagged_pixels"] == 0


def test_resolve_threshold_control_p99_rule():
    rng = np.random.default_rng(0)  # synthetic noise
    control = rng.normal(0, 0.05, 10_000).astype("float32")
    t, why = cs.resolve_threshold("control_p99", [0.05, 0.1, 0.15, 0.2], control)
    p99 = np.percentile(np.abs(control), 99)
    assert t >= p99 and t == min(x for x in [0.05, 0.1, 0.15, 0.2] if x >= p99)
    assert "control_p99" in why
    assert cs.resolve_threshold(0.2, [0.2], control)[0] == 0.2
    with pytest.raises(ValueError, match="exceeds every threshold"):
        cs.resolve_threshold("control_p99", [0.01, 0.02], control)


class _FakeAsset:
    def __init__(self, bands):
        self.href = "https://example.invalid/x.tif"
        self.extra_fields = {"raster:bands": bands}


class _FakeItem:
    id = "FAKE_ITEM"
    properties = {"earthsearch:boa_offset_applied": True}

    def __init__(self, bands):
        self.assets = {"red": _FakeAsset(bands)}


def test_item_metadata_refuses_missing_calibration():
    with pytest.raises(ValueError, match="calibration"):
        cs.item_metadata(_FakeItem([{"nodata": 0}]))
    meta = cs.item_metadata(_FakeItem([{"nodata": 0, "scale": 0.0001, "offset": -0.1}]))
    assert meta["assets"]["red"]["offset"] == 0.0  # offset already applied in the pixels
    assert meta["assets"]["red"]["offset_in_stac_metadata"] == -0.1


def test_patch_statistics_and_filter():
    mask = np.zeros((20, 20), dtype=bool)
    mask[0:10, 0:10] = True  # 100 px patch = 1 ha at 10 m
    mask[15, 15] = True  # single pixel
    stats = cs.patch_statistics(mask, pixel_area_m2=100.0, min_patch_ha=1.0)
    assert stats["patches_total"] == 2 and stats["patches_ge_min"] == 1
    assert stats["area_ge_min_ha"] == pytest.approx(1.0)
    kept = cs.keep_patches_ge(mask, 100)
    assert kept.sum() == 100 and not kept[15, 15]


def test_resolution_table_one_hectare():
    rows = {r["resolution_m"]: r for r in cs.resolution_table(1.0)}
    assert rows[10.0]["pixels_total"] == pytest.approx(100.0)
    assert rows[10.0]["pixels_interior"] == pytest.approx(64.0)
    assert rows[60.0]["pixels_interior"] == 0.0


def test_seasonal_split():
    inc = np.array([True, True, True, False])
    summer = np.array([0.6, 0.7, 0.5, 0.5], dtype="float32")
    spring = np.array([0.55, 0.2, np.nan, 0.1], dtype="float32")
    valid = np.array([True, True, True, True])
    out = cs.seasonal_split(inc, summer, spring, valid, 0.15)
    assert out == {"increase_pixels": 3, "with_valid_second_date": 2, "stable_within_year": 1, "strongly_seasonal": 1}


# --- configuration ------------------------------------------------------------


@pytest.mark.parametrize("path", sorted(CONFIG_DIR.glob("*.json")), ids=lambda p: p.stem)
def test_shipped_configs_load(path):
    cfg = cs.CaseStudyConfig.from_file(path)
    assert cfg.case_id == path.stem
    assert len(set(cfg.item_ids())) >= 3
    tiles = {iid.split("_")[1] for iid in cfg.item_ids()}
    assert len(tiles) == 1, "all items of a case must share one MGRS tile"


def test_config_validation_errors():
    base = {
        "case_id": "x", "title": "x", "bbox": [-8.0, 38.0, -7.9, 38.1], "index": "ndvi",
        "before_item": "a", "after_item": "b", "control_before_item": "c", "control_after_item": "b",
        "primary_threshold": 0.2, "thresholds": [0.1, 0.2],
    }
    cs.CaseStudyConfig.from_mapping(base)
    with pytest.raises(ValueError):
        cs.CaseStudyConfig.from_mapping({**base, "bbox": [-7.9, 38.0, -8.0, 38.1]})
    with pytest.raises(ValueError):
        cs.CaseStudyConfig.from_mapping({**base, "primary_threshold": 0.15})
    with pytest.raises(ValueError):
        cs.CaseStudyConfig.from_mapping({**base, "primary_threshold": "median"})
    with pytest.raises(ValueError):
        cs.CaseStudyConfig.from_mapping({**base, "index": "evi"})


# --- reference comparison -----------------------------------------------------


def test_binary_agreement():
    pred = np.array([1, 1, 0, 0, 1], dtype=bool)
    ref = np.array([1, 0, 1, 0, 1], dtype=bool)
    out = rc.binary_agreement(pred, ref)
    assert (out["tp"], out["fp"], out["fn"], out["tn"]) == (2, 1, 1, 1)
    assert out["precision"] == pytest.approx(2 / 3) and out["recall"] == pytest.approx(2 / 3)


def test_polygon_agreement_majority_rule():
    units = np.array([[1, 1, 2, 2], [1, 1, 2, 2]])
    pred = np.array([[1, 1, 1, 0], [1, 0, 0, 0]], dtype=bool)
    ref = np.array([[1, 1, 0, 0], [1, 1, 1, 1]], dtype=bool)
    out = rc.polygon_agreement(units, pred, ref, np.ones_like(pred), min_pixels=4)
    assert out["units_evaluated"] == 2
    assert (out["tp"], out["fn"]) == (1, 1)


# --- public artifacts agree with their manifests ------------------------------


def _cases():
    idx = PUBLIC / "index.json"
    if not idx.exists():
        return []
    return sorted(json.loads(idx.read_text(encoding="utf-8"))["cases"])


@pytest.mark.parametrize("case_id", _cases())
def test_public_artifacts_are_consistent(case_id):
    pub = PUBLIC / case_id
    manifest = json.loads((pub / "manifest.json").read_text(encoding="utf-8"))
    results = json.loads((pub / "results.json").read_text(encoding="utf-8"))
    index = json.loads((PUBLIC / "index.json").read_text(encoding="utf-8"))["cases"][case_id]
    assert manifest["run_id"] == results["run_id"] == index["run_id"]
    assert manifest["status"] == "ok"
    for name, out in manifest["outputs"].items():
        data = (REPO / out["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == out["sha256"], f"{name} changed after the run (stale or edited artifact)"
    # no signed URLs or tokens in public metadata
    text = (pub / "manifest.json").read_text(encoding="utf-8")
    for marker in ("X-Amz-Signature", "token=", "sig=", "Authorization"):
        assert marker not in text
    # arithmetic in results is internally consistent
    px_area = results["aoi"]["grid"]["pixel_size_m"] ** 2
    ch = results["change"]
    assert ch["increase_area_ha"] == pytest.approx(ch["increase_pixels_in_patches"] * px_area / 10_000)
    assert 0.8 <= results["coverage"]["joint_valid_fraction_main"] <= 1.0
    with open(pub / "sensitivity.csv", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert [float(r["threshold"]) for r in rows] == [r["threshold"] for r in results["sensitivity"]]
    t = results["threshold"]["value"]
    assert any(math.isclose(r["threshold"], t) for r in results["sensitivity"])
    assert results["index_summary"]["abs_delta_control_p99"] <= t or "exceeds grid" in results["threshold"]["rule"]
