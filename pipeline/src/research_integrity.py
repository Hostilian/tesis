"""Conservative scientific-status policy for public thesis exports.

A deterministic software result is not a scientifically verified observation.
The policy never auto-promotes satellite or company observations to Verified.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

MOCK_TERMS = ("mock", "synthetic", "simulat", "illustrativ", "fixture", "seeded")


def source_mode(record: dict[str, Any]) -> str:
    """Identify mock lineage before trusting any self-declared source mode."""
    lineage = record.get("data_lineage") or {}
    provider_text = " ".join(str(x or "") for x in (
        lineage.get("satellite_source"), record.get("provider"),
        record.get("source_system"), record.get("source_mode"),
    )).lower()
    if any(term in provider_text for term in MOCK_TERMS):
        return "synthetic"
    if record.get("source_mode") in ("real", "authentic", "observed"):
        return "authentic_unverified"
    return "unverified"


def prepare_public_record(record: dict[str, Any]) -> dict[str, Any]:
    """Downgrade unverifiable claims without destroying the original source file."""
    if not isinstance(record, dict) or not record.get("id"):
        raise ValueError("Public anomaly must be an object with a non-empty id")
    item = copy.deepcopy(record)
    mode = source_mode(item)
    original = item.get("verification") or {}
    if not isinstance(original, dict):
        original = {"status": str(original)}
    prior_status = original.get("status")
    if prior_status and "historical_status_claim" not in original:
        original["historical_status_claim"] = prior_status
    original["status"] = "Demonstration — not scientifically verified" if mode == "synthetic" else "Unverified — independent validation required"
    original["independent_ground_truth_checked"] = False
    item["verification"] = original
    item["source_mode"] = mode
    item["verification_status"] = "demonstration" if mode == "synthetic" else "unverified"
    item["scientific_use_notice"] = (
        "Mock/synthetic input; illustrative model output, not an observed or "
        "independently validated event." if mode == "synthetic" else
        "Observation and/or independent ground truth not established for this export."
    )
    if item.get("cross_reference_validated") is True:
        item["historical_cross_reference_claim"] = True
        item["cross_reference_validated"] = False
    item["confidence_interpretation"] = "illustrative_model_score_not_calibrated_probability"
    return item


def prepare_public_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(records, list):
        raise ValueError("Expected a list of anomaly records")
    result = [prepare_public_record(record) for record in records]
    ids = [record["id"] for record in result]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate anomaly IDs")
    return result


def assert_public_records_safe(records: list[dict[str, Any]]) -> None:
    """Fail closed when an export labels unverified or mock data as verified."""
    if not isinstance(records, list):
        raise ValueError("Expected list")
    for record in records:
        mode = source_mode(record)
        status = str((record.get("verification") or {}).get("status", "")).lower()
        if record.get("verification_status") == "verified" or "verified" in status and "not" not in status and "unverified" not in status:
            raise ValueError(f"Unsupported scientific verification in {record.get('id')}")
        if mode == "synthetic" and record.get("verification_status") != "demonstration":
            raise ValueError(f"Synthetic record lacks demonstration label: {record.get('id')}")
        if record.get("cross_reference_validated") is True:
            raise ValueError(f"Unreviewed cross-reference assertion: {record.get('id')}")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("Usage: python -m pipeline.src.research_integrity PATH_TO_ANOMALIES_JSON", file=sys.stderr)
        return 2
    data = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    try:
        assert_public_records_safe(data)
    except ValueError as exc:
        print(f"FAIL publication policy: {exc}", file=sys.stderr)
        return 1
    print(f"PASS publication policy: {len(data)} records; no independent verification asserted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
