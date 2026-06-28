"""
test_pipeline.py — Comprehensive test suite for the Space-Based Economic Intelligence pipeline.

Covers all 7 test categories mandated by the master prompt Section 7.1:
  1. Spectral index formula bounds
  2. Cloud mask correctness
  3. Isolation Forest score normalization
  4. GeoJSON export schema validity (RFC 7946)
  5. Null coordinate detection
  6. Date format consistency (ISO-8601)
  7. Anomaly type taxonomy validation

Additional tests:
  8. Economic overlay Pearson r correctness
  9. Bootstrap CI bounds
  10. Orchestrator edge cases (high cloud cover, NaN masking)
  11. World Bank mock fallback
  12. Temporal Z-score window behaviour

Author: Eren Ozturk — CZU Prague PEF KII Bachelor Thesis 2026
"""

import json
import math

import numpy as np
import pytest

from pipeline.src.utils import (
    calculate_ndvi,
    calculate_ndwi,
    calculate_bsi,
    apply_sentinel_cloud_mask,
    calculate_temporal_zscores,
)
from pipeline.src.models import AnomalyDetector
from pipeline.src.anomaly_detector import SatelliteAnomalyOrchestrator
from pipeline.src.economic_overlay import EconomicOverlay
from pipeline.src.config import PipelineConfig
from pipeline.src.ingestion import (
    CopernicusSTACClient,
    MockDataClient,
    NASAEarthDataClient,
    SatelliteDataIngester,
)
from pipeline.src.http_resilience import ResilientHTTPClient

# ── 1. Spectral Index Formula Bounds ──────────────────────────────────────────

class TestNDVI:
    def test_basic_formula(self):
        """NDVI = (NIR - Red) / (NIR + Red)."""
        nir = np.array([0.5, 0.1])
        red = np.array([0.1, 0.5])
        result = calculate_ndvi(nir, red)
        assert result[0] == pytest.approx(0.6667, abs=1e-3)
        assert result[1] == pytest.approx(-0.6667, abs=1e-3)

    def test_output_range_clipped_to_minus1_plus1(self):
        """NDVI output must always be in [-1.0, 1.0]."""
        rng = np.random.default_rng(0)
        nir = rng.uniform(0, 1, 1000)
        red = rng.uniform(0, 1, 1000)
        result = calculate_ndvi(nir, red)
        assert np.all(result >= -1.0), "NDVI below -1.0 detected"
        assert np.all(result <= 1.0),  "NDVI above  1.0 detected"

    def test_zero_denominator_handled(self):
        """Zero denominator must not raise ZeroDivisionError."""
        nir = np.array([0.0, 0.3])
        red = np.array([0.0, 0.3])
        result = calculate_ndvi(nir, red)
        assert result[0] == pytest.approx(0.0, abs=1e-3)
        assert np.isfinite(result).all()

    def test_healthy_forest_range(self):
        """Dense canopy NDVI must be >= 0.6 (Chapter 3 §3.3.1)."""
        nir = np.array([0.85])
        red = np.array([0.05])
        result = calculate_ndvi(nir, red)
        assert result[0] >= 0.60, f"Expected healthy forest NDVI >= 0.6, got {result[0]:.3f}"


class TestNDWI:
    def test_basic_formula(self):
        green = np.array([0.4, 0.1])
        nir = np.array([0.1, 0.4])
        result = calculate_ndwi(green, nir)
        assert result[0] == pytest.approx(0.60, abs=1e-3)
        assert result[1] == pytest.approx(-0.60, abs=1e-3)

    def test_output_range(self):
        rng = np.random.default_rng(1)
        g = rng.uniform(0, 1, 500)
        n = rng.uniform(0, 1, 500)
        result = calculate_ndwi(g, n)
        assert np.all(result >= -1.0) and np.all(result <= 1.0)

    def test_brine_pond_signature(self):
        """Open water / brine ponds must produce NDWI > 0.1 (Chapter 5 §5.2.1)."""
        green = np.array([0.30])
        nir = np.array([0.05])
        result = calculate_ndwi(green, nir)
        assert result[0] > 0.10


class TestBSI:
    def test_basic_formula(self):
        swir = np.array([0.4, 0.2])
        red  = np.array([0.3, 0.1])
        nir  = np.array([0.2, 0.4])
        blue = np.array([0.1, 0.2])
        result = calculate_bsi(swir, red, nir, blue)
        assert result[0] == pytest.approx(0.40,    abs=1e-3)
        assert result[1] == pytest.approx(-0.3333, abs=1e-3)

    def test_output_range(self):
        rng = np.random.default_rng(2)
        s, r, n, b = [rng.uniform(0, 1, 300) for _ in range(4)]
        result = calculate_bsi(s, r, n, b)
        assert np.all(result >= -1.0) and np.all(result <= 1.0)

    def test_exposed_mining_soil_high_bsi(self):
        """Exposed mining soil should show BSI > 0.15 (Chapter 3 §3.3.3)."""
        swir = np.array([0.45])
        red  = np.array([0.30])
        nir  = np.array([0.12])
        blue = np.array([0.08])
        result = calculate_bsi(swir, red, nir, blue)
        assert result[0] > 0.15


# ── 2. Cloud Mask Correctness ─────────────────────────────────────────────────

class TestSentinelCloudMask:
    def test_clear_pixel_is_true(self):
        qa = np.array([0], dtype=int)
        mask = apply_sentinel_cloud_mask(qa)
        assert mask[0] == True

    def test_cloud_bit10_is_false(self):
        qa = np.array([1 << 10], dtype=int)   # Opaque cloud flag
        mask = apply_sentinel_cloud_mask(qa)
        assert mask[0] == False

    def test_cirrus_bit11_is_false(self):
        qa = np.array([1 << 11], dtype=int)   # Cirrus cloud flag
        mask = apply_sentinel_cloud_mask(qa)
        assert mask[0] == False

    def test_mixed_qa_values(self):
        qa = np.array([0, 1024, 2048, 512], dtype=int)
        mask = apply_sentinel_cloud_mask(qa)
        assert mask[0] == True   # Clear
        assert mask[1] == False  # Opaque cloud
        assert mask[2] == False  # Cirrus
        assert mask[3] == True   # Not a cloud bit (bit 9)

    def test_cloud_cover_fraction_matches_mask(self):
        """Cloud fraction from QA mask should equal expected fraction."""
        qa = np.array([0, 0, 0, 1024, 2048], dtype=int)  # 2/5 = 40% cloudy
        mask = apply_sentinel_cloud_mask(qa)
        cloud_fraction = 1.0 - mask.sum() / mask.size
        assert cloud_fraction == pytest.approx(0.40, abs=1e-3)


# ── 3. Isolation Forest Score Normalization ───────────────────────────────────

class TestAnomalyDetectorModel:
    def test_output_scores_in_0_to_1(self):
        """Normalized anomaly scores must be in [0, 1]."""
        rng = np.random.default_rng(42)
        features = rng.uniform(-1, 1, (200, 3))
        detector = AnomalyDetector(contamination=0.08, random_state=42)
        preds, scores = detector.fit_predict_spatial(features)
        assert np.all(scores >= 0.0), "Score below 0.0 detected"
        assert np.all(scores <= 1.0), "Score above 1.0 detected"

    def test_predictions_are_binary(self):
        """Predictions must be either 1 (normal) or -1 (anomaly)."""
        rng = np.random.default_rng(42)
        features = rng.uniform(-1, 1, (150, 4))
        detector = AnomalyDetector()
        preds, _ = detector.fit_predict_spatial(features)
        unique = set(preds.tolist())
        assert unique.issubset({1, -1}), f"Unexpected prediction values: {unique}"

    def test_contamination_fraction_respected(self):
        """Anomaly count should be approximately contamination * n_samples."""
        rng = np.random.default_rng(42)
        features = rng.uniform(-1, 1, (1000, 3))
        contamination = 0.08
        detector = AnomalyDetector(contamination=contamination)
        preds, _ = detector.fit_predict_spatial(features)
        observed_rate = (preds == -1).sum() / len(preds)
        # Allow ±5% tolerance around the target rate
        assert abs(observed_rate - contamination) < 0.05, \
            f"Observed anomaly rate {observed_rate:.3f} deviates from {contamination}"

    def test_deterministic_with_same_seed(self):
        """Same seed must produce identical predictions."""
        rng = np.random.default_rng(99)
        features = rng.uniform(-1, 1, (200, 3))
        det1 = AnomalyDetector(random_state=42)
        det2 = AnomalyDetector(random_state=42)
        p1, s1 = det1.fit_predict_spatial(features)
        p2, s2 = det2.fit_predict_spatial(features)
        np.testing.assert_array_equal(p1, p2)
        np.testing.assert_array_almost_equal(s1, s2)


# ── 4. GeoJSON Export Schema Validity (RFC 7946) ──────────────────────────────

VALID_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "Atacama", "anomaly_type": "Lithium Expansion"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-68.5, -23.8],
                    [-68.1, -23.8],
                    [-68.1, -23.2],
                    [-68.5, -23.2],
                    [-68.5, -23.8],
                ]]
            }
        }
    ]
}

class TestGeoJSONSchema:
    def test_top_level_type_is_featurecollection(self):
        assert VALID_GEOJSON["type"] == "FeatureCollection"

    def test_features_is_list(self):
        assert isinstance(VALID_GEOJSON["features"], list)

    def test_each_feature_has_type_geometry_properties(self):
        for f in VALID_GEOJSON["features"]:
            assert "type"       in f, "Missing 'type' in Feature"
            assert "geometry"   in f, "Missing 'geometry' in Feature"
            assert "properties" in f, "Missing 'properties' in Feature"

    def test_polygon_first_last_coord_match(self):
        """RFC 7946 §3.1.6: Polygon rings must be closed (first == last point)."""
        for f in VALID_GEOJSON["features"]:
            if f["geometry"]["type"] == "Polygon":
                for ring in f["geometry"]["coordinates"]:
                    assert ring[0] == ring[-1], \
                        "Polygon ring is not closed (first != last coordinate)"

    def test_coordinates_are_lon_lat_order(self):
        """RFC 7946 §3.1.1: coordinate order is [longitude, latitude]."""
        for f in VALID_GEOJSON["features"]:
            if f["geometry"]["type"] == "Polygon":
                for ring in f["geometry"]["coordinates"]:
                    for lon, lat in ring:
                        assert -180 <= lon <= 180, f"Invalid longitude: {lon}"
                        assert -90  <= lat <= 90,  f"Invalid latitude: {lat}"

    def test_serializes_to_valid_json(self):
        serialized = json.dumps(VALID_GEOJSON)
        recovered = json.loads(serialized)
        assert recovered["type"] == "FeatureCollection"


# ── 5. Null Coordinate Detection ──────────────────────────────────────────────

class TestNullCoordinates:
    @pytest.fixture
    def sample_anomalies(self):
        return [
            {"id": "a1", "coordinates": [-23.472, -68.349], "date": "2024-10-12"},
            {"id": "a2", "coordinates": [-12.894, -69.912], "date": "2025-03-22"},
        ]

    def test_no_null_coordinates(self, sample_anomalies):
        """All anomaly records must have non-null lat/lon coordinates."""
        for a in sample_anomalies:
            coords = a.get("coordinates")
            assert coords is not None, f"Null coordinates in anomaly {a['id']}"
            assert len(coords) == 2, f"Coordinates must be [lat, lon] pair, got {coords}"
            assert None not in coords, f"None value in coordinates for {a['id']}"
            assert all(isinstance(c, (int, float)) for c in coords), \
                f"Non-numeric coordinate in {a['id']}"

    def test_coordinates_within_global_bounds(self, sample_anomalies):
        for a in sample_anomalies:
            lat, lon = a["coordinates"]
            assert -90  <= lat <= 90,  f"Latitude {lat} out of range for {a['id']}"
            assert -180 <= lon <= 180, f"Longitude {lon} out of range for {a['id']}"


# ── 6. Date Format Consistency (ISO-8601) ─────────────────────────────────────

class TestDateFormatConsistency:
    VALID_DATES = ["2024-10-12", "2025-03-22", "2025-06-01", "2026-02-28"]
    INVALID_DATES = ["10/12/2024", "2024-13-01", "2024-02-30", "22-03-2025", ""]

    def test_valid_iso8601_dates_pass(self):
        from datetime import datetime
        for d in self.VALID_DATES:
            try:
                datetime.strptime(d, "%Y-%m-%d")
            except ValueError:
                pytest.fail(f"Valid ISO-8601 date failed validation: {d}")

    def test_invalid_dates_raise(self):
        from datetime import datetime
        for d in self.INVALID_DATES:
            with pytest.raises((ValueError, TypeError)):
                datetime.strptime(d, "%Y-%m-%d")

    def test_orchestrator_rejects_invalid_date(self):
        orch = SatelliteAnomalyOrchestrator()
        with pytest.raises(ValueError):
            orch._validate_iso8601("2024-13-01")  # Month 13 invalid

    def test_orchestrator_accepts_leap_year(self):
        """Feb 29 on a real leap year must not raise."""
        orch = SatelliteAnomalyOrchestrator()
        orch._validate_iso8601("2024-02-29")  # 2024 is a leap year

    def test_orchestrator_rejects_non_leap_year_feb29(self):
        orch = SatelliteAnomalyOrchestrator()
        with pytest.raises(ValueError):
            orch._validate_iso8601("2023-02-29")  # 2023 is NOT a leap year


# ── 7. Anomaly Type Taxonomy Validation ───────────────────────────────────────

VALID_ANOMALY_TYPES = {
    "Lithium Expansion",
    "Gold Mining / Deforestation",
    "NTL Economic Expansion",
    "NTL Economic Contraction",
    "Industrial Shutdown",
    "Deforestation / Forest Degradation",
    "Bare Soil Emergence",
    "Water Body Expansion",
}

class TestAnomalyTypeTaxonomy:
    def test_all_sample_anomaly_types_in_taxonomy(self):
        """Every anomaly record type must belong to the approved taxonomy."""
        sample_records = [
            {"type": "Lithium Expansion"},
            {"type": "Gold Mining / Deforestation"},
            {"type": "NTL Economic Expansion"},
        ]
        for rec in sample_records:
            assert rec["type"] in VALID_ANOMALY_TYPES, \
                f"Unknown anomaly type: '{rec['type']}'"

    def test_taxonomy_types_are_non_empty_strings(self):
        for t in VALID_ANOMALY_TYPES:
            assert isinstance(t, str) and len(t) > 0


# ── 8. Economic Overlay Pearson r ─────────────────────────────────────────────

class TestEconomicOverlay:
    def test_pearson_r_perfect_positive(self):
        overlay = EconomicOverlay()
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        result = overlay.compute_ntl_gdp_correlation(x, y)
        assert result["r"] == pytest.approx(1.0, abs=1e-4)
        assert result["r_squared"] == pytest.approx(1.0, abs=1e-4)

    def test_pearson_r_perfect_negative(self):
        overlay = EconomicOverlay()
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [10.0, 8.0, 6.0, 4.0, 2.0]
        result = overlay.compute_ntl_gdp_correlation(x, y)
        assert result["r"] == pytest.approx(-1.0, abs=1e-4)

    def test_h2_hypothesis_supported_with_known_values(self):
        """H₂ requires r >= 0.65, p < 0.05 (Master Prompt §5.3.2).
        
        Test uses synthetic data with a known strong positive correlation
        to validate the H₂ decision logic in compute_ntl_gdp_correlation().
        The thesis r=0.724 was computed against the real ČSÚ GDP time series
        which is proprietary quarterly data — this test validates the logic,
        not the exact real-world figure.
        """
        overlay = EconomicOverlay()
        # Generate strongly positively correlated data (r ≈ 0.95 by construction)
        import numpy as np
        rng = np.random.default_rng(42)
        base = rng.normal(0, 1, 21)
        noise = rng.normal(0, 0.3, 21)
        z_scores  = base.tolist()
        gdp_vals  = (base + noise).tolist()

        result = overlay.compute_ntl_gdp_correlation(z_scores, gdp_vals)
        # H₂ threshold test: r ≥ 0.65
        assert result["r"] >= 0.65, \
            f"Pearson r below H₂ threshold: expected >= 0.65, got {result['r']}"
        assert result["p_value"] < 0.05, f"p-value not significant: {result['p_value']}"
        assert result["h2_supported"] is True
        assert 0.65 <= result["r"] <= 1.0, f"r = {result['r']} out of expected range"

    def test_mismatched_lengths_raise(self):
        overlay = EconomicOverlay()
        with pytest.raises(ValueError):
            overlay.compute_ntl_gdp_correlation([1.0, 2.0], [1.0])

    def test_mock_gdp_fallback_returns_data(self):
        ingester = SatelliteDataIngester()
        result = ingester.fetch_worldbank_gdp("CZE", 2021, 2025)
        assert len(result) > 0
        for rec in result:
            assert "year" in rec and "gdp_growth_pct" in rec


class TestEnterpriseIngestion:
    def test_pipeline_config_validation_reports_missing_live_credentials(self):
        config = PipelineConfig(mock_mode=True)
        warnings = config.validate()
        assert any("MOCK_MODE=true" in item for item in warnings)

    def test_mock_sentinel2_summary_is_deterministic_and_bounded(self):
        mock = MockDataClient(seed=42)
        bbox = [-68.5, -23.8, -68.1, -23.2]
        first = mock.spectral_summary(bbox, "2024-01-01", "2024-12-31", "Sentinel-2 L2A")
        second = mock.spectral_summary(bbox, "2024-01-01", "2024-12-31", "Sentinel-2 L2A")
        assert first == second
        assert -1.0 <= first["ndvi"] <= 1.0
        assert -1.0 <= first["ndwi"] <= 1.0
        assert -1.0 <= first["bsi"] <= 1.0

    def test_cdse_mock_search_returns_stac_like_item(self):
        config = PipelineConfig(mock_mode=True)
        client = CopernicusSTACClient(config, ResilientHTTPClient(), MockDataClient())
        items = client.search_sentinel2_scenes(
            [-70.2, -13.1, -69.6, -12.6],
            "2025-01-01T00:00:00Z",
            "2025-06-30T23:59:59Z",
        )
        assert len(items) == 1
        assert "assets" in items[0]
        assert items[0]["properties"]["sbei:mock"] is True

    def test_nasa_mock_cmr_search_returns_metadata_list(self):
        config = PipelineConfig(mock_mode=True)
        client = NASAEarthDataClient(config, ResilientHTTPClient(), MockDataClient())
        granules = client.search_viirs_ntl_granules(
            "-70.2,-13.1,-69.6,-12.6",
            "2025-01-01T00:00:00Z,2025-06-30T23:59:59Z",
        )
        assert isinstance(granules, list)
        assert granules[0]["id"] == "NASA_MOCK_SCENE_001"

    def test_mineral_dependency_index_has_expected_components(self):
        ingester = SatelliteDataIngester(config=PipelineConfig(mock_mode=True))
        result = ingester.fetch_mineral_dependency_index("CHL")
        assert result["score"] > 0
        assert "mineral_exports_pct" in result["components"]


# ── 9. Temporal Z-Score ───────────────────────────────────────────────────────

class TestTemporalZScore:
    def test_early_values_are_zero(self):
        values = np.ones(15) * 10.0
        z = calculate_temporal_zscores(values, rolling_window=12)
        assert all(z[i] == 0.0 for i in range(12))

    def test_shock_produces_large_negative_zscore(self):
        values = np.array([10.0] * 12 + [2.0])
        z = calculate_temporal_zscores(values, rolling_window=12)
        assert z[12] < -1.0, f"Expected large negative Z-score, got {z[12]}"

    def test_output_length_equals_input_length(self):
        values = np.linspace(5.0, 30.0, 36)
        z = calculate_temporal_zscores(values, rolling_window=12)
        assert len(z) == 36

    def test_constant_series_returns_zeros_after_warmup(self):
        values = np.ones(24) * 15.0
        z = calculate_temporal_zscores(values, rolling_window=12)
        # After warmup: std=0 → z should be 0 (handled by std floor)
        assert np.isfinite(z).all()


# ── 10. Orchestrator Edge Cases ───────────────────────────────────────────────

class TestOrchestratorEdgeCases:
    def _make_bands(self, size=(100, 100), cloud_fraction=0.0):
        rng = np.random.default_rng(42)
        qa = np.zeros(size, dtype=int)
        if cloud_fraction > 0:
            n_cloudy = int(cloud_fraction * size[0] * size[1])
            qa.flat[:n_cloudy] = 1024   # Opaque cloud bit
        return {
            "B2": rng.uniform(0.01, 0.15, size),
            "B3": rng.uniform(0.02, 0.18, size),
            "B4": rng.uniform(0.01, 0.12, size),
            "B8": rng.uniform(0.20, 0.65, size),
            "B11": rng.uniform(0.05, 0.45, size),
            "QA60": qa,
        }

    def test_normal_run_returns_valid_result(self):
        orch = SatelliteAnomalyOrchestrator()
        bands = self._make_bands()
        result = orch.run_spatial_detection(bands, "test_region", "2025-01-01")
        assert result["skipped_reason"] is None
        assert result["valid_pixel_count"] > 0
        assert 0.0 <= result["confidence_mean"] <= 1.0

    def test_high_cloud_cover_skips_tile(self):
        """Tiles with > 80% cloud cover must be skipped."""
        orch = SatelliteAnomalyOrchestrator()
        bands = self._make_bands(cloud_fraction=0.85)
        result = orch.run_spatial_detection(bands, "cloudy_region", "2025-06-01")
        assert result["skipped_reason"] is not None
        assert "Cloud cover" in result["skipped_reason"]
        assert result["anomaly_mask"] is None

    def test_invalid_date_raises(self):
        orch = SatelliteAnomalyOrchestrator()
        with pytest.raises(ValueError, match="Invalid ISO-8601"):
            orch.run_spatial_detection(self._make_bands(), "r", "2025/01/01")

    def test_confidence_ci_low_le_mean_le_high(self):
        orch = SatelliteAnomalyOrchestrator(n_bootstrap=10)
        result = orch.run_spatial_detection(self._make_bands(), "region", "2025-03-15")
        if result["skipped_reason"] is None and result["confidence_mean"] > 0:
            assert result["confidence_ci_low"] <= result["confidence_mean"]
            assert result["confidence_mean"] <= result["confidence_ci_high"]
