"""Offline regression checks; these assert policy behavior, not scientific validity."""
import unittest
from pipeline.src.research_integrity import (
    source_mode, prepare_public_record, prepare_public_records, assert_public_records_safe,
)
from pipeline.src.agriculture_pilot import validate_study_area, stac_search_request, ndvi, robust_deviation


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.mock = {"id": "illustration_1", "source_mode": "authentic",
                     "data_lineage": {"satellite_source": "Mock Sentinel-2 L2A"},
                     "verification": {"status": "Verified", "ground_truth": "unconfirmed report"},
                     "cross_reference_validated": True, "confidence": 0.9}

    def test_mock_lineage_overrides_claimed_authenticity(self):
        self.assertEqual(source_mode(self.mock), "synthetic")

    def test_previous_verified_claim_is_downgraded_and_preserved(self):
        out = prepare_public_record(self.mock)
        self.assertEqual(out["verification_status"], "demonstration")
        self.assertEqual(out["verification"]["historical_status_claim"], "Verified")
        self.assertFalse(out["cross_reference_validated"])
        assert_public_records_safe([out])
        self.assertEqual(self.mock["verification"]["status"], "Verified")

    def test_rejects_unreviewed_verified(self):
        with self.assertRaises(ValueError):
            assert_public_records_safe([self.mock])

    def test_no_automatic_promotion_of_real_source(self):
        out = prepare_public_record({"id": "x", "source_mode": "authentic", "verification": {"status": "Verified"}})
        self.assertEqual(out["verification_status"], "unverified")
        assert_public_records_safe([out])

    def test_duplicate_ids_blocked(self):
        with self.assertRaises(ValueError):
            prepare_public_records([self.mock, self.mock])


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.feature = {"type": "Feature", "properties": {"id": "PUBLIC_DEMO"},
                        "geometry": {"type": "Polygon", "coordinates": [[
                            [-1, 40], [-1, 40.01], [-0.99, 40.01], [-1, 40]
                        ]]}}

    def test_stac_query_is_only_request_description(self):
        q = stac_search_request(self.feature, "2025-01-01", "2025-06-01")
        self.assertEqual(q["method"], "POST")
        self.assertFalse(q["network_performed"])
        self.assertEqual(q["json"]["collections"], ["sentinel-2-l2a"])

    def test_rejects_invalid_crs(self):
        f = dict(self.feature, crs={"type": "name", "properties": {"name": "EPSG:3857"}})
        with self.assertRaises(ValueError):
            validate_study_area(f)

    def test_rejects_invalid_ring(self):
        f = {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[1, 2], [3, 4], [1, 2]]]}}
        with self.assertRaises(ValueError):
            validate_study_area(f)

    def test_ndvi_formula_and_nodata(self):
        self.assertAlmostEqual(ndvi(.8, .2), .6)
        self.assertIsNone(ndvi(0, 0))

    def test_robust_z_zero_mad_is_not_infinite(self):
        self.assertIsNone(robust_deviation(.5, [.3] * 6)["robust_z"])

    def test_robust_deviation_five_samples_required(self):
        with self.assertRaises(ValueError):
            robust_deviation(.5, [.4, .4])


if __name__ == "__main__":
    unittest.main()
