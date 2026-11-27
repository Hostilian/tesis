"""Offline tests for the soil-lab <-> Sentinel-2 link. All data here is synthetic."""

from __future__ import annotations

import math
from datetime import date
from types import SimpleNamespace

import numpy as np
import pytest

from pipeline.src import soil_link as sl


def bands(ndvi_like: float, nbr2_like: float, shape=(9,)) -> dict[str, np.ndarray]:
    """Reflectances that give roughly the requested NDVI and NBR2."""
    red = 0.20
    nir = red * (1 + ndvi_like) / (1 - ndvi_like)
    sw2 = 0.25
    sw1 = sw2 * (1 + nbr2_like) / (1 - nbr2_like)
    b = {k: np.full(shape, 0.2, "float32") for k in sl.SOIL_BANDS}
    b.update(
        red=np.full(shape, red, "float32"),
        nir=np.full(shape, nir, "float32"),
        swir16=np.full(shape, sw1, "float32"),
        swir22=np.full(shape, sw2, "float32"),
        blue=np.full(shape, 0.1, "float32"),
    )
    return b


def fast_models():
    m = sl.make_models(0, fast=True)
    return {k: m[k] for k in ("baseline_mean", "ridge", "pls")}


# ---- masking -------------------------------------------------------------


def test_bare_soil_mask_keeps_bare_and_rejects_vegetation_and_straw():
    scl = np.full(9, 5, np.uint8)
    assert sl.bare_soil_mask(bands(0.15, 0.05), scl).all()
    assert not sl.bare_soil_mask(bands(0.55, 0.05), scl).any()  # green crop
    # Real case seen near Castro Verde: NDVI 0.2 but NBR2 0.22-0.27 = straw
    assert not sl.bare_soil_mask(bands(0.20, 0.24), scl).any()


def test_bare_soil_mask_rejects_cloud_nan_and_negative_reflectance():
    b = bands(0.15, 0.05)
    scl = np.array([5, 5, 8, 9, 3, 5, 5, 5, 5], np.uint8)
    b["red"][0] = np.nan
    b["green"][6] = -0.01
    m = sl.bare_soil_mask(b, scl)
    assert m.tolist() == [False, True, False, False, False, True, False, True, True]


def test_cloud_edges_are_buffered_on_images():
    scl = np.full((9, 9), 5, np.uint8)
    scl[4, 4] = 9  # one cloudy pixel in the middle
    m = sl.bare_soil_mask(bands(0.15, 0.05, (9, 9)), scl)
    assert not m[2:7, 2:7].any()  # 2-pixel buffer around it
    assert m[0, 0] and m[8, 8]


def test_composite_is_nan_not_zero_when_no_bare_pixels():
    feats, n, used = sl.composite_features([(bands(0.6, 0.3), np.full(9, 4, np.uint8))])
    assert n == 0 and used == 0
    assert all(math.isnan(v) for v in feats.values())


def test_composite_needs_at_least_three_swir_pixels():
    one_scene = [(bands(0.1, 0.05, (9,)), np.full(9, 5, np.uint8))]
    assert math.isnan(sl.composite_features(one_scene)[0]["red"])  # 9 < 12 px
    two = one_scene * 2
    assert not math.isnan(sl.composite_features(two)[0]["red"])


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


# ---- input ---------------------------------------------------------------


def test_parse_lab_value():
    assert sl.parse_lab_value("12,5") == (12.5, False)
    assert sl.parse_lab_value(" 7.25 ") == (7.25, False)
    v, c = sl.parse_lab_value("<5")
    assert math.isnan(v) and c
    v, c = sl.parse_lab_value("")
    assert math.isnan(v) and not c
    with pytest.raises(ValueError):
        sl.parse_lab_value("abc")


def test_read_samples_metadata_censoring_and_errors(tmp_path):
    p = tmp_path / "s.csv"
    p.write_text(
        "sample_id,lat,lon,date,depth_cm,method,soc_g_kg,p_mg_kg\n"
        'A,38.1,-7.9,2025-10-01,20,Walkley-Black,"12,5",<5\n'
        "B,38.2,-7.8,2025-10-02,20,Walkley-Black,,30\n",
        encoding="utf-8",
    )
    s = sl.read_samples(p)
    assert s[0].values["soc_g_kg"] == 12.5
    assert math.isnan(s[0].values["p_mg_kg"]) and "p_mg_kg" in s[0].censored
    assert s[0].meta["depth_cm"] == "20" and "depth_cm" not in s[0].values
    assert sl.iter_targets(s) == ["soc_g_kg", "p_mg_kg"]
    bad = tmp_path / "b.csv"
    bad.write_text("sample_id,lat,lon\nA,1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required"):
        sl.read_samples(bad)
    bad.write_text("sample_id,lat,lon,date\nA,95,2,2025-01-01\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid lat"):
        sl.read_samples(bad)
    bad.write_text(
        "sample_id,lat,lon,date\nA,38,-8,2025-01-01\nA,38,-8,2025-01-02\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate"):
        sl.read_samples(bad)
    bad.write_text(
        "sample_id,lat,lon,date,soc\nA,38,-8,2025-01-01,high\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="soc"):
        sl.read_samples(bad)


# ---- scene selection and privacy ----------------------------------------


def _item(day, version="0", baseline="05.10", tile=("29", "S", "NB")):
    return SimpleNamespace(
        id=f"S2A_{''.join(tile)}_{day.replace('-', '')}_{version}_L2A",
        properties={
            "datetime": day + "T11:00:00Z",
            "s2:processing_baseline": baseline,
            "mgrs:utm_zone": tile[0],
            "mgrs:latitude_band": tile[1],
            "mgrs:grid_square": tile[2],
        },
    )


def test_spread_by_month_caps_scenes_per_month_and_prefers_close_dates():
    items = [_item(f"2025-08-{d:02d}") for d in range(1, 29, 3)] + [
        _item("2025-10-20"),
        _item("2025-11-03"),
    ]
    chosen = sl.spread_by_month(items, date(2025, 8, 15), max_items=5)
    months = [c.properties["datetime"][:7] for c in chosen]
    assert months.count("2025-08") == 2
    assert "2025-10" in months and "2025-11" in months


def test_dedupe_overpasses_keeps_the_reprocessed_copy():
    items = [
        _item("2018-08-18", "0", "02.08"),
        _item("2018-08-18", "1", "05.00"),
        _item("2018-08-23", "0", "02.08"),
    ]
    kept = sl.dedupe_overpasses(items)
    assert sorted(i.id for i in kept) == [
        "S2A_29SNB_20180818_1_L2A",
        "S2A_29SNB_20180823_0_L2A",
    ]


def test_catalogue_search_uses_coarse_cell_not_the_point():
    cell = sl.coarse_cell(37.9512, -7.9871)
    assert cell == [-8.0, 37.9, -7.9, 38.0]


def test_extract_features_never_raises_and_keeps_order():
    samples = [sl.Sample(f"S{i}", 38.0, -8.0, date(2025, 10, 1)) for i in range(4)]

    def search(s):
        if s.sample_id == "S1":
            raise RuntimeError("catalogue down")
        return ["scene-a", "scene-b", "scene-c"]

    def reader(item, s):
        if item == "scene-b":
            raise OSError("short read")
        return bands(0.1, 0.05), np.full(9, 5, np.uint8)

    rows = sl.extract_features(
        samples, search, reader, terrain=None, workers=3, log=lambda m: None
    )
    assert [r["sample_id"] for r in rows] == ["S0", "S1", "S2", "S3"]
    assert "catalogue down" in rows[1]["errors"] and math.isnan(rows[1]["red"])
    assert rows[0]["n_scenes_used"] == 2 and rows[0]["n_scenes_read"] == 2
    assert "OSError" in rows[0]["errors"]


def test_terrain_errors_are_recorded_not_silent():
    rows = sl.extract_features(
        [sl.Sample("S0", 38.0, -8.0, date(2025, 10, 1))],
        lambda s: [],
        lambda i, s: None,
        terrain=lambda la, lo: {
            "elevation_m": math.nan,
            "slope_deg": math.nan,
            "terrain_error": "Timeout",
        },
        log=lambda m: None,
    )
    assert "terrain: Timeout" in rows[0]["errors"]
    assert "terrain_error" not in rows[0]


# ---- statistics ----------------------------------------------------------


def test_spatial_blocks_group_nearby_points():
    g = sl.spatial_blocks([38.0, 38.001, 38.5], [-8.0, -8.001, -7.5], block_km=5)
    assert g[0] == g[1] != g[2]


def test_permutation_strata_have_something_to_shuffle():
    rng = np.random.default_rng(0)
    lat, lon = 38 + rng.uniform(0, 0.5, 200), -8 + rng.uniform(0, 0.6, 200)
    g, km = sl.permutation_strata(lat, lon, start_km=5)
    assert np.median(np.bincount(g)) >= 6 and km >= 5


def test_restricted_permutation_stays_inside_strata():
    y = np.arange(10.0)
    strata = np.array([0] * 5 + [1] * 5)
    out = sl._permute_within(y, strata, np.random.default_rng(1))
    assert sorted(out[:5]) == [0, 1, 2, 3, 4] and sorted(out[5:]) == [5, 6, 7, 8, 9]


def test_empirical_range_is_larger_for_smoother_fields():
    rng = np.random.default_rng(0)
    lat, lon = 38 + rng.uniform(0, 0.54, 400), -8.2 + rng.uniform(0, 0.68, 400)
    xy = sl.to_km(lat, lon)
    noise = sl.empirical_range_km(lat, lon, rng.normal(0, 1, 400))
    short = sl.empirical_range_km(
        lat, lon, sl.smooth_field(xy, np.random.default_rng(1), 3)
    )
    long_ = sl.empirical_range_km(
        lat, lon, sl.smooth_field(xy, np.random.default_rng(1), 30)
    )
    assert noise < short < long_
    assert math.isnan(sl.empirical_range_km(lat[:5], lon[:5], np.arange(5.0)))


def test_fdr_bh_matches_hand_calculation():
    q = sl.fdr_bh([0.01, 0.04, 0.03, 0.5])
    assert q.tolist() == pytest.approx([0.04, 0.0533333, 0.0533333, 0.5], rel=1e-4)
    assert len(sl.fdr_bh([])) == 0


def _evaluate(scenario, seed):
    X, t, lat, lon = sl.synthetic_dataset(n=200, seed=seed, scenario=scenario)
    return sl.evaluate_property(
        X,
        t["soc_g_kg"],
        sl.spatial_blocks(lat, lon, 5),
        sl.FEATURE_NAMES,
        lat=lat,
        lon=lon,
        n_permutations=19,
        seed=seed,
        models=fast_models(),
    )


@pytest.mark.parametrize(
    "scenario,seed",
    [
        ("planted_signal", 1),
        ("planted_signal_patchy_features", 2),
        ("iid_noise", 2),
        ("unrelated_smooth_fields", 0),  # the independent review's trap
        ("unrelated_smooth_fields", 1),
        ("shared_trend", 3),
    ],
)
def test_method_verdicts_on_synthetic_scenarios(scenario, seed):
    res = _evaluate(scenario, seed)
    assert res["verdict"] == sl.EXPECTED[scenario]


def test_never_a_false_signal_over_many_seeds():
    """The core safety property: no signal reported where none was planted."""
    for scenario in ("iid_noise", "unrelated_smooth_fields", "shared_trend"):
        for seed in range(10, 14):
            assert _evaluate(scenario, seed)["verdict"] != "signal_above_chance", (
                scenario,
                seed,
            )


def test_planted_signal_screen_points_at_the_right_band():
    res = _evaluate("planted_signal", 1)
    assert "swir16" in {r["feature"] for r in res["screen"] if r.get("q_fdr", 1) < 0.05}


def test_detrend_removes_a_quadratic_surface():
    rng = np.random.default_rng(0)
    xy = rng.uniform(0, 50, (300, 2))
    trend = 3 + 0.2 * xy[:, 0] - 0.01 * xy[:, 1] ** 2
    assert np.abs(sl.detrend(trend, xy)).max() < 1e-8
    X = np.column_stack([trend, 2 * trend])
    assert np.abs(sl.detrend(X, xy)).max() < 1e-8


def test_spectral_surrogates_keep_smoothness_but_break_alignment():
    rng = np.random.default_rng(0)
    lat, lon = 38 + rng.uniform(0, 0.54, 200), -8.2 + rng.uniform(0, 0.68, 200)
    xy = sl.to_km(lat, lon)
    y = sl.smooth_field(xy, np.random.default_rng(1), 10)
    sur = sl.SpectralSurrogates(xy)
    ys = [sur(y, rng) for _ in range(30)]
    assert all(np.isclose(np.var(z), np.var(y), rtol=1e-6) for z in ys)
    assert abs(np.mean([np.corrcoef(y, z)[0, 1] for z in ys])) < 0.15

    def nn_similarity(v):  # correlation of each value with its nearest neighbour
        from scipy.spatial import cKDTree

        _, idx = cKDTree(xy).query(xy, k=2)
        return np.corrcoef(v, v[idx[:, 1]])[0, 1]

    assert np.mean([nn_similarity(z) for z in ys]) == pytest.approx(
        nn_similarity(y), abs=0.15
    )


def test_too_few_samples_is_reported_not_scored():
    X, t, lat, lon = sl.synthetic_dataset(n=12, seed=0)
    res = sl.evaluate_property(
        X, t["soc_g_kg"], sl.spatial_blocks(lat, lon, 5), sl.FEATURE_NAMES
    )
    assert res["status"] == "too_few_samples"


def test_area_of_applicability_flags_unfamiliar_places_and_survives_nan():
    rng = np.random.default_rng(0)
    train = rng.normal(0, 1, (100, 4))
    train[3, 2] = np.nan
    new = np.vstack([rng.normal(0, 1, (5, 4)), np.full((2, 4), 12.0)])
    new[0, 1] = np.nan
    aoa = sl.area_of_applicability(train, new)
    assert np.isfinite(aoa["threshold"])
    assert aoa["inside"][:5].sum() >= 4
    assert not aoa["inside"][5:].any()


def test_area_of_applicability_handles_many_samples():
    rng = np.random.default_rng(0)
    aoa = sl.area_of_applicability(
        rng.normal(0, 1, (20000, 17)), rng.normal(0, 1, (10, 17))
    )
    assert aoa["di_train"].shape == (20000,)


def test_prediction_interval_covers_requested_share_on_new_data():
    rng = np.random.default_rng(0)
    y = rng.normal(0, 1, 4000)
    pred = y + rng.normal(0, 1, 4000)
    hw = sl.prediction_interval_halfwidth(y[:2000], pred[:2000], 0.8)  # calibrate
    cover = np.mean(np.abs(y[2000:] - pred[2000:]) <= hw)  # test on other half
    assert cover == pytest.approx(0.8, abs=0.03)


def test_samples_needed_matches_standard_table_and_inflates():
    # Standard values for alpha 0.05, power 0.8: r=0.3 -> 85, r=0.5 -> 30.
    assert sl.samples_needed(0.3) == 85
    assert sl.samples_needed(0.5) == 30
    assert sl.samples_needed(0.3, bare_share=1 / 3) >= 3 * 85 - 1
    assert sl.samples_needed(0.3, n_tests=3) > 85
    with pytest.raises(ValueError):
        sl.samples_needed(1.0)
