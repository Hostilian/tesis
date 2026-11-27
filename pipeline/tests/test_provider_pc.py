"""Offline tests for the Planetary Computer provider helpers.

All inputs are synthetic (data_status: synthetic_demonstration): hand-written
IDs, a trimmed MTD_MSIL2A.xml fragment and small arrays. No network access.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from pipeline.src import case_study as cs
from pipeline.src import provider_pc as pp

REPO = Path(__file__).resolve().parents[2]
INTEROP = (
    REPO
    / "docs"
    / "case-study"
    / "data"
    / "alqueva_olive"
    / "interop_planetary_computer.json"
)

ES_URI_N0500 = "S2A_MSIL2A_20180818T112111_N0500_R037_T29SNC_20230810T181646.SAFE"
PC_URI_N0212 = "S2A_MSIL2A_20180818T112111_N0212_R037_T29SNC_20201011T032718.SAFE"
PC_ID_N0212 = "S2A_MSIL2A_20180818T112111_R037_T29SNC_20201011T032718"


def _mtd(baseline: str, offsets: dict[int, int] | None) -> str:
    """Minimal synthetic MTD_MSIL2A.xml fragment with the tags the parser reads."""
    bands = "".join(
        f'<Spectral_Information bandId="{i}" physicalBand="{b}"><x/></Spectral_Information>'
        for i, b in enumerate(
            [
                "B1",
                "B2",
                "B3",
                "B4",
                "B5",
                "B6",
                "B7",
                "B8",
                "B8A",
                "B9",
                "B10",
                "B11",
                "B12",
            ]
        )
    )
    off = ""
    if offsets is not None:
        off = (
            "<BOA_ADD_OFFSET_VALUES_LIST>"
            + "".join(
                f'<BOA_ADD_OFFSET band_id="{i}">{v}</BOA_ADD_OFFSET>'
                for i, v in offsets.items()
            )
            + "</BOA_ADD_OFFSET_VALUES_LIST>"
        )
    return (
        f"<root><PROCESSING_BASELINE>{baseline}</PROCESSING_BASELINE>"
        "<Special_Values><SPECIAL_VALUE_TEXT>NODATA</SPECIAL_VALUE_TEXT>"
        "<SPECIAL_VALUE_INDEX>0</SPECIAL_VALUE_INDEX></Special_Values>"
        "<Special_Values><SPECIAL_VALUE_TEXT>SATURATED</SPECIAL_VALUE_TEXT>"
        "<SPECIAL_VALUE_INDEX>65535</SPECIAL_VALUE_INDEX></Special_Values>"
        f"{bands}"
        '<QUANTIFICATION_VALUES_LIST><BOA_QUANTIFICATION_VALUE unit="none">10000</BOA_QUANTIFICATION_VALUE>'
        "</QUANTIFICATION_VALUES_LIST>"
        f"{off}</root>"
    )


# --- identifiers and matching -----------------------------------------------------


def test_parse_earth_search_id():
    p = pp.parse_earth_search_id("S2A_29SNC_20180818_1_L2A")
    assert p == {
        "platform": "S2A",
        "tile": "29SNC",
        "date": "2018-08-18",
        "sequence": 1,
        "level": "L2A",
    }
    with pytest.raises(ValueError):
        pp.parse_earth_search_id(PC_ID_N0212)


def test_parse_product_uri_and_pc_id_share_acquisition_key():
    es = pp.parse_product_uri(ES_URI_N0500)
    pc = pp.parse_product_uri(PC_URI_N0212)
    pid = pp.parse_pc_item_id(PC_ID_N0212)
    assert es["processing_baseline"] == "05.00" and pc["processing_baseline"] == "02.12"
    assert pp.acquisition_key(es) == pp.acquisition_key(pc) == pp.acquisition_key(pid)
    assert pp.acquisition_key(es) == ("S2A", "20180818T112111", "037", "29SNC")
    with pytest.raises(ValueError):
        pp.parse_product_uri("S2A_29SNC_20180818_1_L2A")


def test_select_match_prefers_same_baseline_then_highest():
    other_orbit = {"id": "x", "product_uri": ES_URI_N0500.replace("_R037_", "_R080_")}
    old = {"id": PC_ID_N0212, "product_uri": PC_URI_N0212}
    newer = {"id": "n", "product_uri": PC_URI_N0212.replace("N0212", "N0400")}
    same = {"id": "s", "product_uri": ES_URI_N0500}

    chosen, matches, rule = pp.select_match(ES_URI_N0500, [other_orbit, old, newer])
    assert chosen["id"] == "n" and {m["id"] for m in matches} == {PC_ID_N0212, "n"}
    assert "highest" in rule

    chosen, _, rule = pp.select_match(ES_URI_N0500, [old, same, newer])
    assert chosen["id"] == "s" and "same processing baseline" in rule

    with pytest.raises(LookupError):
        pp.select_match(ES_URI_N0500, [other_orbit])


def test_baseline_rules():
    assert pp.baseline_tuple("05.00") == (5, 0)
    assert pp.baseline_has_boa_offset("04.00")
    assert pp.baseline_has_boa_offset("05.11")
    assert not pp.baseline_has_boa_offset("02.12")
    assert not pp.baseline_has_boa_offset("03.01")
    with pytest.raises(ValueError):
        pp.baseline_tuple("N0500")


# --- calibration ------------------------------------------------------------------


def test_parse_product_metadata_with_offset():
    cal = pp.parse_product_metadata(_mtd("05.11", {i: -1000 for i in range(13)}))
    assert cal.processing_baseline == "05.11"
    assert cal.quantification_value == 10000
    assert cal.add_offsets["B4"] == -1000 and cal.add_offsets["B8"] == -1000
    assert cal.nodata == 0 and cal.saturated == 65535
    scale, offset = pp.band_calibration(cal, "red")
    assert scale == pytest.approx(1e-4) and offset == pytest.approx(-0.1)


def test_offset_maps_band_id_to_physical_band():
    # Only band_id 7 (B8) carries an offset: red (B4) must not pick it up.
    cal = pp.parse_product_metadata(_mtd("02.12", {7: -1000}))
    assert cal.add_offsets == {"B8": -1000}
    assert pp.band_calibration(cal, "red") == (pytest.approx(1e-4), 0.0)
    with pytest.raises(ValueError, match="< 04.00"):
        pp.band_calibration(cal, "nir")


def test_calibration_without_offset_and_inconsistent_products():
    old = pp.parse_product_metadata(_mtd("02.12", None))
    assert old.add_offsets == {}
    assert pp.band_calibration(old, "nir") == (pytest.approx(1e-4), 0.0)
    new_missing = pp.parse_product_metadata(_mtd("04.00", None))
    with pytest.raises(ValueError, match="refusing to guess"):
        pp.band_calibration(new_missing, "red")
    with pytest.raises(ValueError, match="PROCESSING_BASELINE"):
        pp.parse_product_metadata("<root/>")


def test_pc_calibration_reproduces_earth_search_reflectance():
    """Same surface, two encodings: PC keeps +1000 DN, Earth Search has removed it."""
    es_dn = np.array([[0, 500, 1638, 3000]], dtype="uint16")
    pc_dn = np.where(es_dn == 0, 0, es_dn + 1000).astype("uint16")
    cal = pp.parse_product_metadata(_mtd("05.00", {3: -1000, 7: -1000}))
    scale, offset = pp.band_calibration(cal, "red")
    es = cs.to_reflectance(es_dn, 1e-4, cs.effective_offset(-0.1, True), nodata=0)
    pc = cs.to_reflectance(pc_dn, scale, offset, nodata=cal.nodata)
    assert np.isnan(es[0, 0]) and np.isnan(pc[0, 0])
    np.testing.assert_allclose(pc[0, 1:], es[0, 1:], atol=1e-6)
    # Ignoring the offset would shift reflectance by +0.1.
    wrong = cs.to_reflectance(pc_dn, scale, 0.0, nodata=0)
    np.testing.assert_allclose(wrong[0, 1:] - es[0, 1:], 0.1, atol=1e-6)


# --- comparison statistics --------------------------------------------------------


def test_difference_stats():
    a = np.array([0.5, 0.5, 0.5, np.nan, 0.9], dtype="float32")
    b = np.array([0.5, 0.48, 0.505, 0.5, 0.0], dtype="float32")
    mask = np.array([True, True, True, True, False])
    s = pp.difference_stats(a, b, mask, tolerance=0.01)
    assert s["n"] == 3
    assert s["share_abs_diff_gt_tolerance"] == pytest.approx(1 / 3)
    assert s["share_exactly_equal"] == pytest.approx(1 / 3)
    assert s["max_abs_diff"] == pytest.approx(0.02, abs=1e-6)
    assert pp.difference_stats(a, b, np.zeros(5, dtype=bool)) == {"n": 0}


def test_flag_agreement_counts_and_kappa():
    a = np.array([1, 1, 0, 0, 1, 0], dtype=bool)
    b = np.array([1, 0, 0, 1, 1, 0], dtype=bool)
    mask = np.array([1, 1, 1, 1, 1, 0], dtype=bool)
    r = pp.flag_agreement(a, b, mask)
    assert (r["both_flagged"], r["only_first"], r["only_second"], r["neither"]) == (
        2,
        1,
        1,
        1,
    )
    assert r["agreement_share"] == pytest.approx(3 / 5)
    po, pe = 3 / 5, (3 / 5) * (3 / 5) + (2 / 5) * (2 / 5)
    assert r["cohen_kappa"] == pytest.approx((po - pe) / (1 - pe))
    assert r["jaccard_of_flagged"] == pytest.approx(2 / 4)
    same = pp.flag_agreement(a, a, np.ones(6, dtype=bool))
    assert same["agreement_share"] == 1.0 and same["cohen_kappa"] == pytest.approx(1.0)


# --- URL handling -----------------------------------------------------------------


def test_sign_and_redact():
    href = "https://example.blob.core.windows.net/c/B04.tif"
    signed = pp.sign_href(href, "?st=1&se=2&sig=abc")
    assert signed == href + "?st=1&se=2&sig=abc"
    assert pp.sign_href(href + "?a=1", "sig=abc") == href + "?a=1&sig=abc"
    assert pp.strip_query(signed) == href
    msg = f"'{signed}': not recognized; also {signed} again"
    red = pp.redact_url(msg)
    assert "sig=" not in red and "se=2" not in red and href in red


def test_pc_asset_keys_cover_index_bands():
    for band in cs.INDEX_BANDS["ndvi"]:
        assert band in pp.PC_ASSET_KEYS and band in pp.MTD_PHYSICAL_BAND
    assert pp.PC_ASSET_KEYS["scl"] == "SCL"


# --- published output (only if it exists) ----------------------------------------


@pytest.mark.skipif(not INTEROP.exists(), reason="interop check not run yet")
def test_published_interop_output_is_consistent():
    text = INTEROP.read_text(encoding="utf-8")
    for marker in ("sig=", "se=", "sv=", "token=", "X-Amz-Signature", "Authorization"):
        assert marker not in text
    raw = INTEROP.read_bytes()
    assert b"\r\n" not in raw
    d = json.loads(text)
    fig = REPO / d["figure"]["path"]
    assert hashlib.sha256(fig.read_bytes()).hexdigest() == d["figure"]["sha256"]
    assert d["steps_required"] and all(isinstance(s, str) for s in d["steps_required"])
    for s in d["scenes"]:
        assert s["grid_alignment"]["aligned"] is True
        es_key = pp.acquisition_key(
            pp.parse_product_uri(s["earth_search"]["product_uri"])
        )
        pc_key = pp.acquisition_key(
            pp.parse_product_uri(s["planetary_computer"]["product_uri"])
        )
        assert es_key == pc_key
        assert s["joint_valid_pixels"] <= min(
            s["valid_pixels_earth_search"], s["valid_pixels_planetary_computer"]
        )
    pf = d["change_agreement"]["pixel_flag"]
    assert (
        pf["both_flagged"] + pf["only_first"] + pf["only_second"] + pf["neither"]
        == pf["n"]
    )
