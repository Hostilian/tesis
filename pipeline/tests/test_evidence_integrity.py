"""Evidence-integrity regression tests for the public static demonstrator.

These tests check data provenance disclosures, not scientific accuracy.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.src.evidence import DEMO_STATUS, disclose_demonstration

ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_published_anomalies_match_api_records() -> None:
    published = _read("docs/data/anomalies.json")
    index = _read("docs/api/v1/anomalies/index.json")
    assert isinstance(published, list)
    assert len(published) == 10
    assert published == index

    for record in published:
        assert _read(
            f"docs/api/v1/anomalies/{record['id']}/index.json"
        ) == record


def test_demo_data_cannot_claim_ground_truth_verification() -> None:
    runs = _read("docs/api/v1/status/index.json")["recent_runs"]
    assert runs
    assert runs[0]["mock_mode"] is True

    for record in _read("docs/data/anomalies.json"):
        assert record["data_origin"] == "synthetic_demo"
        assert record["verification_status"] == "unverified"
        assert record["verification"]["status"] == DEMO_STATUS
        assert record["verification"]["validation_state"] == (
            "not_independently_validated"
        )
        assert record["data_lineage"]["satellite_scene_ids"] == []
        assert record["osm_overlap_pct"] is None
        assert "not a calibrated probability" in record[
            "confidence_interpretation"
        ]


def test_static_status_discloses_snapshot_mode() -> None:
    status = _read("docs/api/v1/status/index.json")
    assert status["data_mode"] == "synthetic_demo"
    assert status["verified_satellite_observations"] == 0
    assert "static" in status["status_note"].lower()


def test_disclosure_clears_spurious_scene_ids_and_heuristics() -> None:
    records: list[dict[str, Any]] = [
        {
            "id": "example",
            "confidence": 0.9,
            "verification": {"status": "Verified"},
            "osm_overlap_pct": 88.4,
            "cross_reference_validated": True,
            "data_lineage": {
                "satellite_scene_ids": ["not-a-real-verified-scene"],
                "satellite_source": "Unverified",
            },
        }
    ]
    disclose_demonstration(records)
    record = records[0]
    assert record["verification"]["status"] == DEMO_STATUS
    assert record["data_lineage"]["satellite_scene_ids"] == []
    assert record["osm_overlap_pct"] is None
    assert record["cross_reference_validated"] is False
    assert record["confidence"] == 0.9


def test_every_public_dashboard_contains_evidence_notice() -> None:
    for name in ("index.html", "index3.html", "index4.html"):
        html = (ROOT / "docs" / name).read_text(encoding="utf-8")
        assert "Research demonstrator" in html
        assert 'href="evidence.html"' in html
    assert (ROOT / "docs/evidence.html").is_file()


def test_v4_does_not_confuse_opaque_fetch_with_api_health() -> None:
    source = (ROOT / "docs/app4.js").read_text(encoding="utf-8")
    assert 'mode: "no-cors"' not in source
    assert "not verified from browser" in source


def test_scheduled_rehearsal_is_read_only() -> None:
    workflow = (ROOT / ".github/workflows/data-refresh.yml").read_text(
        encoding="utf-8"
    )
    assert "contents: read" in workflow
    assert "MOCK_MODE: 'true'" in workflow
    assert "git push" not in workflow.replace("# No automatic git push.", "")
    assert "actions/upload-artifact@" in workflow


def test_public_satellite_evidence_layers_remain_separate() -> None:
    """Metadata, pixel sampling and independently validated events differ."""
    catalogue = _read("docs/data/public_stac_scene_inventory.json")
    sample = _read("docs/data/observed_three_region_proof_20261119.json")
    demo = _read("docs/data/anomalies.json")

    assert catalogue["evidence_state"] == "catalogue_metadata_only"
    assert catalogue["product_count"] == 9
    assert sample["status"] == "real_pixel_inputs_unvalidated"
    assert sample["scientific_validation"] == "not_performed"
    assert sample["independent_event_ground_truth"] is False
    assert sample["model_accuracy_measured"] is False
    assert len(sample["studies"]) == 3
    assert sum(region["valid_pixels"] for region in sample["studies"]) == 21253
    assert sample["raw_rasters_or_pixel_npzs_published"] is False
    assert all(len(region["derived_pixel_npz_sha256"]) == 64 for region in sample["studies"])
    assert all(anomaly["data_origin"] == "synthetic_demo" for anomaly in demo)


def test_satellite_remains_default_map_layer_on_all_three_versions() -> None:
    """Protect the previously restored V2/V3/V4 satellite-first UX."""
    for filename in ("app.js", "app3.js", "app4.js"):
        script = (ROOT / "docs" / filename).read_text(encoding="utf-8")
        assert "server.arcgisonline.com/ArcGIS/rest/services/World_Imagery" in script
        assert "satelliteBasemapLayer" in script
        if filename != "app4.js":
            assert "satelliteBasemapLayer.addTo(map)" in script
        else:
            assert "}).addTo(map)" in script
