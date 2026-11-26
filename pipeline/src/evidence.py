"""Evidence classifications for the public thesis demonstrator.

Authentication is not proof of real raster processing: the current Sentinel-2
feature arrays and monthly VIIRS time series are deterministic mock data.
Keep source provenance, ground-truth validation and confidence separate.
"""

from __future__ import annotations

from typing import Any

DEMO_STATUS = "Demo - unverified"
DEMO_NOTICE = (
    "Synthetic demonstration. No independently linked satellite scene or "
    "ground-truth validation is available for this anomaly."
)


def disclose_demonstration(records: list[dict[str, Any]]) -> None:
    """Mark synthetic anomalies in-place before any JSON/API export.

    This function never upgrades the status of a record to "verified".
    Scientific validation must be implemented and evidenced separately.
    """
    for anomaly in records:
        anomaly["data_origin"] = "synthetic_demo"
        anomaly["verification_status"] = "unverified"
        anomaly["confidence_interpretation"] = (
            "Illustrative normalized anomaly score; not a calibrated probability"
        )
        anomaly["evidence_notice"] = DEMO_NOTICE

        verification = anomaly.get("verification")
        if not isinstance(verification, dict):
            verification = {}
            anomaly["verification"] = verification
        verification["status"] = DEMO_STATUS
        verification["validation_state"] = "not_independently_validated"
        verification["evidence_note"] = DEMO_NOTICE
        verification["ground_truth_note"] = (
            "Listed reference is a candidate for future validation, not a verified match"
        )

        lineage = anomaly.get("data_lineage")
        if isinstance(lineage, dict):
            lineage["satellite_source"] = (
                "Synthetic pixel arrays / deterministic mock time series"
            )
            lineage["satellite_scene_ids"] = []
            lineage["data_origin"] = "synthetic_demo"
            lineage["economic_source_validation"] = "not_independently_verified"

        # These values were illustrative heuristics, not measured spatial overlap
        # or independent economic cross-validation.
        anomaly["osm_overlap_pct"] = None
        if "cross_reference_validated" in anomaly:
            anomaly["cross_reference_validated"] = False
