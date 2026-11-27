"""Offline tests for the soil-lab <-> Sentinel-2 link. All data here is synthetic."""

from __future__ import annotations

import math
from datetime import date
from types import SimpleNamespace

import numpy as np
import pytest

from pipeline.src import soil_link as sl


def bands(ndvi_like: float, nbr2_like: float, n: int = 9) -> dict[str, np.ndarray]:
    """Reflectances that give roughly the requested NDVI and NBR2."""
    red = 0.20
    nir = red * (1 + ndvi_like) / (1 - ndvi_like)
    sw2 = 0.25
    sw1 = sw2 * (1 + nbr2_like) / (1 - nbr2_like)
    b = {k: np.full(n, 0.2, "float32") for k in sl.SOIL_BANDS}
    b.update(
        red=np.full(n, red, "float32"),
        nir=np.full(n, nir, "float32"),
        swir16=np.full(n, sw1, "float32"),
        swir22=np.full(n, sw2, "float32"),
        blue=np.full(n, 0.1, "float32"),
    )
    return b


def test_bare_soil_mask_keeps_bare_and_rejects_vegetation_and_straw():
    scl = np.full(9, 5, np.uint8)
    assert sl.bare_soil_mask(bands(0.15, 0.05), scl).all()
    assert not sl.bare_soil_mask(bands(0.55, 0.05), scl).any()  # green crop
    # Real case seen near Castro Verde: NDVI 0.2 but NBR2 0.22-0.27 = straw
    assert not sl.bare_soil_mask(bands(0.20, 0.24), scl).any()


def test_bare_soil_mask_rejects_cloud_and_nan():
    b = bands(0.15, 0.05)
    scl = np.array([5, 5, 8, 9, 3, 5, 5, 5, 5], np.uint8)
    b["red"][0] = np.nan
    m = sl.bare_soil_mask(b, scl)
    assert m.tolist() == [False, True, False, False, False, True, True, True, True]


def test_composite_is_nan_not_zero_when_no_bare_pixels():
    feats, n, used = sl.composite_features([(bands(0.6, 0.3), np.full(9, 4, np.uint8))])
    assert n == 0 and used == 0
    assert all(math.isnan(v) for v in feats.values())


def test_composite_median_over_scenes():
    s1 = bands(0.10, 0.05)
    s2 = bands(0.10, 0.05)
    s2["green"] = np.full(9, 0.4, "float32")
    feats, n, used = sl.composite_features(
        [(s1, np.full(9, 5, np.uint8)), (s2, np.full(9, 5, np.uint8))]
    )
    assert used == 2 and n == 18
    assert feats["green"] == pytest.approx(0.3)
    assert -1 <= feats["ndvi"] <= 1


def test_read_samples_validates_and_keeps_missing_as_nan(tmp_path):
    p = tmp_path / "s.csv"
    p.write_text(
        "sample_id,lat,lon,date,soc_g_kg,ph\nA,38.1,-7.9,2025-10-01,12.5,\nB,38.2,-7.8,2025-10-02,x,6.1\n",
        encoding="utf-8",
    )
    s = sl.read_samples(p)
    assert s[0].values["soc_g_kg"] == 12.5 and math.isnan(s[0].values["ph"])
    assert math.isnan(s[1].values["soc_g_kg"]) and s[1].when == date(2025, 10, 2)
    bad = tmp_path / "b.csv"
    bad.write_text("sample_id,lat,lon\nA,1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required"):
        sl.read_samples(bad)
    bad.write_text("sample_id,lat,lon,date\nA,95,2,2025-01-01\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid lat"):
        sl.read_samples(bad)


def test_spread_by_month_caps_scenes_per_month_and_prefers_close_dates():
    def it(d):
        return SimpleNamespace(properties={"datetime": d + "T11:00:00Z"}, id=d)

    items = [it(f"2025-08-{d:02d}") for d in range(1, 29, 3)] + [
        it("2025-10-20"),
        it("2025-11-03"),
    ]
    chosen = sl.spread_by_month(items, date(2025, 8, 15), max_items=5)
    months = [c.id[:7] for c in chosen]
    assert months.count("2025-08") == 2
    assert "2025-10" in months and "2025-11" in months
    assert chosen[0].id in ("2025-08-13", "2025-08-16")


def test_extract_features_never_raises_and_keeps_order():
    samples = [sl.Sample(f"S{i}", 38.0, -8.0, date(2025, 10, 1)) for i in range(4)]

    def search(s):
        if s.sample_id == "S1":
            raise RuntimeError("catalogue down")
        return ["scene-a", "scene-b"]

    def reader(item, s):
        if item == "scene-b":
            raise OSError("short read")
        return bands(0.1, 0.05), np.full(9, 5, np.uint8)

    rows = sl.extract_features(
        samples, search, reader, terrain=None, workers=3, log=lambda m: None
    )
    assert [r["sample_id"] for r in rows] == ["S0", "S1", "S2", "S3"]
    assert "catalogue down" in rows[1]["errors"] and math.isnan(rows[1]["red"])
    assert rows[0]["n_scenes_used"] == 1 and "short read" not in rows[0]["errors"]
    assert "OSError" in rows[0]["errors"]


def test_spatial_blocks_group_nearby_points():
    g = sl.spatial_blocks([38.0, 38.001, 38.5], [-8.0, -8.001, -7.5], block_km=5)
    assert g[0] == g[1] != g[2]


def test_fdr_bh_matches_hand_calculation():
    q = sl.fdr_bh([0.01, 0.04, 0.03, 0.5])
    assert q.tolist() == pytest.approx([0.04, 0.0533333, 0.0533333, 0.5], rel=1e-4)
    assert len(sl.fdr_bh([])) == 0


def test_method_finds_planted_signal():
    X, t, lat, lon = sl.synthetic_dataset(n=200, signal=1.0, seed=1)
    res = sl.evaluate_property(
        X,
        t["soc_g_kg"],
        sl.spatial_blocks(lat, lon, 5),
        sl.FEATURE_NAMES,
        n_permutations=19,
        seed=1,
    )
    assert res["verdict"] == "signal_above_chance"
    assert res["models"][res["best_model"]]["r2"] > 0.5
    assert "swir16" in {r["feature"] for r in res["screen"] if r.get("q_fdr", 1) < 0.05}


@pytest.mark.parametrize("seed", [2, 3, 4])
def test_method_does_not_invent_signal_from_spatial_noise(seed):
    X, t, lat, lon = sl.synthetic_dataset(n=200, signal=0.0, seed=seed)
    res = sl.evaluate_property(
        X,
        t["soc_g_kg"],
        sl.spatial_blocks(lat, lon, 5),
        sl.FEATURE_NAMES,
        n_permutations=19,
        seed=seed,
    )
    assert res["verdict"] == "no_evidence_of_signal"


def test_too_few_samples_is_reported_not_scored():
    X, t, lat, lon = sl.synthetic_dataset(n=12, seed=0)
    res = sl.evaluate_property(
        X, t["soc_g_kg"], sl.spatial_blocks(lat, lon, 5), sl.FEATURE_NAMES
    )
    assert res["status"] == "too_few_samples"


def test_area_of_applicability_flags_unfamiliar_places():
    rng = np.random.default_rng(0)
    train = rng.normal(0, 1, (100, 4))
    new = np.vstack([rng.normal(0, 1, (5, 4)), np.full((2, 4), 12.0)])
    aoa = sl.area_of_applicability(train, new)
    assert aoa["inside"][:5].sum() >= 4
    assert not aoa["inside"][5:].any()


def test_prediction_interval_covers_requested_share():
    rng = np.random.default_rng(0)
    y = rng.normal(0, 1, 1000)
    pred = y + rng.normal(0, 1, 1000)
    hw = sl.prediction_interval_halfwidth(y, pred, 0.8)
    assert np.mean(np.abs(y - pred) <= hw) == pytest.approx(0.8, abs=0.01)


def test_samples_needed_matches_standard_table():
    # Standard values for alpha 0.05, power 0.8: r=0.3 -> 85, r=0.5 -> 30.
    assert sl.samples_needed(0.3) == 85
    assert sl.samples_needed(0.5) == 30
    with pytest.raises(ValueError):
        sl.samples_needed(1.0)
