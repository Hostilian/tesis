"""Tests for functions that write published numbers and had no test before.

Found in the QA audit of 2026-11-27 (coverage per function plus a hand-run
mutation test). Every array here is a small synthetic fixture
(data_status: synthetic_demonstration); the tests check arithmetic and
bookkeeping, not scientific validity.

Covered here:
* results.json: ``case_study.summarize``, ``scl_class_counts``, ``flag_changes``
  and the boundary cases of ``resolve_threshold``, ``threshold_table`` and
  ``label_patches`` that the existing suite let through;
* reference_cos.json: ``reference_cos.class_codes``, ``code_mask``,
  ``agreement_matrix``;
* robustness.json: ``robustness.reference_definition``,
  ``run_robustness._grid_matches``;
* all three files: ``run_case_study._clean``, ``write_json``, ``_round_geom``;
* independent_check.json: ``verify_independent`` end to end on local GeoTIFFs.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from pipeline import run_case_study as rcs
from pipeline import run_robustness as rrb
from pipeline import verify_independent as vi
from pipeline.src import case_study as cs
from pipeline.src import reference_cos as rc
from pipeline.src import robustness as rb

# --- case_study: values that go into results.json ------------------------------


def test_summarize_known_values_ignores_nan():
    s = cs.summarize(np.array([1.0, 2.0, 3.0, 4.0, np.nan]))
    assert s["n"] == 4
    assert s["mean"] == pytest.approx(2.5)
    assert s["std"] == pytest.approx(math.sqrt(5 / 3))  # sample std, ddof=1
    assert s["median"] == pytest.approx(2.5)
    assert s["p01"] == pytest.approx(1.03)
    assert s["p99"] == pytest.approx(3.97)
    assert list(s) == [
        "n",
        "mean",
        "std",
        "p01",
        "p05",
        "p25",
        "median",
        "p75",
        "p95",
        "p99",
    ]


def test_summarize_edge_cases():
    assert cs.summarize(np.array([np.nan, np.nan])) == {"n": 0}
    one = cs.summarize(np.array([0.3]))
    assert one["n"] == 1 and one["std"] == 0.0 and one["median"] == pytest.approx(0.3)


def test_scl_class_counts_labels_and_unknown_class():
    scl = np.array([[4, 4], [6, 99]], dtype="uint8")
    assert cs.scl_class_counts(scl) == {
        cs.SCL_LABELS[4]: 2,
        cs.SCL_LABELS[6]: 1,
        "class_99": 1,
    }


def test_flag_changes_is_strict_and_never_flags_nan():
    delta = np.array([0.3, 0.2, 0.1, -0.2, -0.3, np.nan], dtype="float32")
    inc, dec = cs.flag_changes(delta, 0.2)
    assert inc.tolist() == [True, False, False, False, False, False]
    assert dec.tolist() == [False, False, False, False, True, False]


def test_change_mask_uses_flag_changes():
    rng = np.random.default_rng(3)
    delta = rng.normal(0, 0.2, (30, 30)).astype("float32")
    delta[0, :5] = 0.2  # exactly at the threshold: never flagged
    delta[5:8, 5:8] = np.nan
    inc, dec = cs.flag_changes(delta, 0.2)
    np.testing.assert_array_equal(rb.change_mask(delta, 0.2, 1, None, "increase"), inc)
    np.testing.assert_array_equal(rb.change_mask(delta, 0.2, 1, None, "decrease"), dec)
    assert not inc[0, :5].any()


def test_resolve_threshold_accepts_grid_value_equal_to_p99():
    # p99 of a constant float64 array is exactly that value; the rule is ">=".
    control = np.full(1000, 0.1)
    t, _ = cs.resolve_threshold("control_p99", [0.05, 0.1, 0.15], control)
    assert t == 0.1


def test_threshold_table_value_at_threshold_is_not_flagged():
    main = np.array([0.2, -0.2, 0.3, -0.3])
    control = np.array([0.2, -0.2, 0.1, 0.25])
    (row,) = cs.threshold_table(main, control, [0.2])
    assert row["main_increase_pixels"] == 1
    assert row["main_decrease_pixels"] == 1
    assert row["control_flagged_pixels"] == 1
    assert row["control_flagged_share"] == pytest.approx(0.25)


def test_patches_are_eight_connected():
    mask = np.zeros((5, 5), dtype=bool)
    mask[1, 1] = mask[2, 2] = mask[3, 3] = True  # diagonal chain = one patch
    _, n = cs.label_patches(mask)
    assert n == 1
    np.testing.assert_array_equal(cs.keep_patches_ge(mask, 3), mask)
    assert cs.patch_statistics(mask, 100.0, 0.03)["patches_ge_min"] == 1


def test_keep_patches_ge_never_keeps_background():
    mask = np.zeros((4, 4), dtype=bool)
    mask[0, 0] = True
    np.testing.assert_array_equal(cs.keep_patches_ge(mask, 1), mask)


# --- reference_cos: values that go into reference_cos.json ----------------------


def test_class_codes_sorted_unique_strings():
    feats = [
        {"properties": {"cos18v4_n4_c": "2.2.3.1"}},
        {"properties": {"cos18v4_n4_c": "1.6.1.1"}},
        {"properties": {"cos18v4_n4_c": "2.2.3.1"}},
    ]
    assert rc.class_codes(feats, "cos18v4") == ["1.6.1.1", "2.2.3.1"]


def test_code_mask_uses_one_based_raster_ids():
    raster = np.array([[0, 1], [2, 3]], dtype="uint16")
    codes = ["1.6.1.1", "2.2.1.1", "2.2.3.1"]  # raster ids 1, 2, 3; 0 = no polygon
    m = rc.code_mask(raster, codes, lambda c: c.startswith(rc.PERMANENT_CROP_PREFIX))
    assert m.tolist() == [[False, False], [True, True]]


def test_agreement_matrix_hand_computed():
    flags = np.array([[1, 0], [2, 0]], dtype="uint8")
    valid = np.ones((2, 2), dtype=bool)
    ref = {
        "top": np.array([[True, True], [False, False]]),
        "bottom": np.array([[False, False], [True, True]]),
        "empty": np.zeros((2, 2), dtype=bool),
    }
    top, bottom, empty = rc.agreement_matrix(flags, ref, valid, 100.0)
    assert top == {
        "reference_category": "top",
        "pixels": 2,
        "area_ha": 0.02,
        "share_of_aoi": 0.5,
        "share_of_all_increase_flags_in_category": 1.0,
        "share_of_all_decrease_flags_in_category": 0.0,
        "share_flagged_increase": 0.5,
        "share_flagged_decrease": 0.0,
        "share_not_flagged": 0.5,
    }
    assert bottom["share_of_all_decrease_flags_in_category"] == 1.0
    assert bottom["share_flagged_decrease"] == 0.5
    assert empty["pixels"] == 0
    assert empty["share_flagged_increase"] is None


def test_agreement_matrix_ignores_invalid_pixels():
    flags = np.array([1, 1, 0], dtype="uint8")
    valid = np.array([True, False, True])
    (row,) = rc.agreement_matrix(flags, {"all": np.ones(3, dtype=bool)}, valid, 1.0)
    assert row["pixels"] == 2
    assert row["share_flagged_increase"] == 0.5


# --- robustness: values that go into robustness.json ----------------------------


def _cos(**arrays: Any) -> Any:
    return SimpleNamespace(**arrays)


def test_reference_definition_ndvi_and_bsi():
    perm18 = np.array([True, False, False, False])
    perm25 = np.array([True, True, False, False])
    mining25 = np.array([False, False, True, False])
    covered = np.array([True, True, True, False])
    valid = np.array([True, True, True, True])
    cos = _cos(perm18=perm18, perm25=perm25, mining25=mining25, covered=covered)
    ref, dom, desc = rb.reference_definition("ndvi", cos, valid)
    assert ref.tolist() == [False, True, False, False]
    assert dom.tolist() == [False, True, True, False]
    assert "2.2.x" in desc["reference_positive"]
    ref, dom, _ = rb.reference_definition("bsi", cos, valid)
    assert ref.tolist() == mining25.tolist()
    assert dom.tolist() == covered.tolist()
    with pytest.raises(ValueError):
        rb.reference_definition("evi", cos, valid)


def test_grid_matches():
    from affine import Affine
    from rasterio.crs import CRS

    tr = Affine(10, 0, 500000, 0, -10, 4200000)
    g = cs.Grid(CRS.from_epsg(32629), tr, 20, 20, (500000, 4199800, 500200, 4200000))
    assert rrb._grid_matches(g, g)
    moved = cs.Grid(
        g.crs, Affine(10, 0, 500010, 0, -10, 4200000), 20, 20, g.window_bounds
    )
    assert not rrb._grid_matches(g, moved)
    other_crs = cs.Grid(CRS.from_epsg(32630), tr, 20, 20, g.window_bounds)
    assert not rrb._grid_matches(g, other_crs)


# --- run_case_study: JSON writing used for every published file ---------------


def test_clean_replaces_non_finite_and_numpy_scalars():
    out = rcs._clean(
        {
            "a": float("nan"),
            "b": np.int64(3),
            "c": [np.float32(0.5), (1, float("inf"))],
            "d": np.bool_(True),
        }
    )
    assert out == {"a": None, "b": 3, "c": [0.5, [1, None]], "d": True}
    assert type(out["b"]) is int


def test_write_json_lf_utf8_and_trailing_newline(tmp_path: Path):
    p = tmp_path / "sub" / "x.json"
    rcs.write_json(p, {"name": "Direção-Geral do Território", "v": np.float64("nan")})
    raw = p.read_bytes()
    assert raw.endswith(b"}\n") and b"\r\n" not in raw
    assert "Direção".encode("utf-8") in raw
    assert json.loads(raw) == {"name": "Direção-Geral do Território", "v": None}


def test_round_geom_rounds_every_coordinate():
    geom = {
        "type": "Polygon",
        "coordinates": [
            [[1.123456789, 2.987654321], [3.0, 4.000004999], [1.123456789, 2.987654321]]
        ],
    }
    assert rcs._round_geom(geom) == {
        "type": "Polygon",
        "coordinates": [[[1.12346, 2.98765], [3.0, 4.0], [1.12346, 2.98765]]],
    }


# --- verify_independent: offline end-to-end on local GeoTIFFs --------------------

_BOUNDS = (500000.0, 4199800.0, 500200.0, 4200000.0)  # 20 x 20 px at 10 m


def _write_tif(path: Path, arr: np.ndarray) -> str:
    import rasterio
    from rasterio.transform import from_origin

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=arr.shape[1],
        height=arr.shape[0],
        count=1,
        dtype="uint16",
        crs="EPSG:32629",
        transform=from_origin(_BOUNDS[0], _BOUNDS[3], 10, 10),
    ) as ds:
        ds.write(arr.astype("uint16"), 1)
    return str(path)


def _fake_item(
    tmp: Path,
    name: str,
    nir: np.ndarray,
    red: np.ndarray,
    applied: bool,
    offset: float,
    scale: float,
) -> dict[str, Any]:
    rb_meta = [{"scale": scale, "offset": offset}]
    return {
        "properties": {"earthsearch:boa_offset_applied": applied},
        "assets": {
            "nir": {
                "href": _write_tif(tmp / f"{name}_nir.tif", nir),
                "raster:bands": rb_meta,
            },
            "red": {
                "href": _write_tif(tmp / f"{name}_red.tif", red),
                "raster:bands": rb_meta,
            },
            "scl": {"href": _write_tif(tmp / f"{name}_scl.tif", np.full(nir.shape, 4))},
        },
    }


def test_verify_independent_band_offset_follows_earth_search_flag(tmp_path: Path):
    dn = np.full((20, 20), 1000)
    shape = (20, 20)
    applied = _fake_item(tmp_path, "a", dn, dn, True, -0.1, 1e-4)
    not_applied = _fake_item(tmp_path, "n", dn, dn, False, -0.1, 1e-4)
    assert np.allclose(vi.band(applied, "nir", _BOUNDS, shape), 0.1)
    assert np.allclose(vi.band(not_applied, "nir", _BOUNDS, shape), 0.0)


def test_verify_independent_area_in_patches_is_eight_connected():
    mask = np.zeros((5, 5), dtype=bool)
    mask[1, 1] = mask[2, 2] = mask[3, 3] = True
    assert vi.area_in_patches(mask, 3) == 3
    assert vi.area_in_patches(np.zeros((3, 3), dtype=bool), 1) == 0


def test_verify_independent_main_on_synthetic_scenes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Integer reflectances give exact NDVI (0.25, 0.5, 0.75, -0.5), so some deltas
    sit exactly on the threshold and must not be flagged."""
    shape = (20, 20)
    nir_b, red_b = np.full(shape, 5), np.full(shape, 3)  # NDVI 0.25
    nir_a, red_a = nir_b.copy(), red_b.copy()
    nir_a[2:6, 2:6], red_a[2:6, 2:6] = (
        3,
        1,
    )  # NDVI 0.5: delta 0.25 = threshold, not flagged
    nir_a[10:15, 10:15], red_a[10:15, 10:15] = (
        7,
        1,
    )  # NDVI 0.75: delta 0.5, 25 px flagged
    nir_a[2:5, 14:18], red_a[2:5, 14:18] = 1, 3  # NDVI -0.5: delta -0.75, 12 px flagged
    nir_a[18, 1], red_a[18, 1] = 7, 1  # 1 px increase, below the 4 px minimum patch
    nir_ca, red_ca = nir_b.copy(), red_b.copy()
    nir_ca[0, 0:4], red_ca[0, 0:4] = 3, 1  # control delta 0.25 (= threshold)
    nir_ca[19, 18:20], red_ca[19, 18:20] = 7, 1  # control delta 0.5 (flagged)

    # Offsets: Earth Search says the BOA offset is already in the pixels, so -0.1 must be ignored.
    items = {
        "B": _fake_item(tmp_path, "b", nir_b, red_b, True, -0.1, 1.0),
        "A": _fake_item(tmp_path, "a", nir_a, red_a, True, -0.1, 1.0),
        "CB": _fake_item(tmp_path, "cb", nir_b, red_b, True, -0.1, 1.0),
        "CA": _fake_item(tmp_path, "ca", nir_ca, red_ca, True, -0.1, 1.0),
    }
    cfg = {
        "case_id": "synthetic_vi",
        "index": "ndvi",
        "before_item": "B",
        "after_item": "A",
        "control_before_item": "CB",
        "control_after_item": "CA",
        "thresholds": [0.1, 0.25, 0.5],
        "primary_threshold": "control_p99",  # p99 of |control delta| is exactly 0.25
        "min_patch_ha": 0.04,  # 4 px
        "valid_scl": [4, 5, 6],
    }
    pub = tmp_path / "docs" / "case-study" / "data" / "synthetic_vi"
    pub.mkdir(parents=True)
    results = {
        "run_id": "synthetic_vi-test",
        "aoi": {
            "grid": {
                "bounds": list(_BOUNDS),
                "height": 20,
                "width": 20,
                "pixel_size_m": 10.0,
            }
        },
        "coverage": {"joint_valid_pixels_main": 400, "joint_valid_pixels_control": 400},
        "threshold": {"value": 0.25},
        "change": {
            "increase_area_ha": 0.25,
            "decrease_area_ha": 0.12,
            "control_flagged_share_at_threshold": 2 / 400,
        },
    }
    (pub / "results.json").write_text(json.dumps(results), encoding="utf-8")
    cfg_path = tmp_path / "synthetic_vi.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    monkeypatch.setattr(vi, "REPO", tmp_path)
    monkeypatch.setattr(vi, "item", lambda iid: items[iid])
    rc_ = vi.main(str(cfg_path))
    report = json.loads((pub / "independent_check.json").read_text(encoding="utf-8"))
    mismatches = [r for r in report["comparisons"] if not r["match"]]
    assert rc_ == 0 and report["all_match"], mismatches
