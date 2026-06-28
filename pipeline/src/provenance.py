"""
provenance.py — Canonical evidence hashing for anomaly exports.

Builds immutable SHA-256 fingerprints from raw satellite inputs and processing
parameters so each exported anomaly can be tied back to a reproducible evidence
set without changing the public anomalies.json contract.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
from typing import Any, Mapping

import numpy as np

from pipeline.src.http_resilience import stable_json_hash


@dataclass(frozen=True)
class ProvenanceRecord:
    anomaly_id: str
    source_system: str
    raw_tile_hash: str
    processing_parameters_hash: str
    combined_hash: str
    created_at: str
    metadata: dict[str, Any]


def hash_numpy_array(array: Any) -> str:
    if not isinstance(array, np.ndarray):
        array = np.asarray(array)

    contiguous = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(str(contiguous.dtype).encode("utf-8"))
    digest.update(str(contiguous.shape).encode("utf-8"))
    digest.update(contiguous.tobytes())
    return digest.hexdigest()


def build_provenance_record(
    anomaly_id: str,
    *,
    source_system: str,
    raw_tile_inputs: Mapping[str, Any],
    processing_parameters: Mapping[str, Any],
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    raw_tile_hash = stable_json_hash(_normalize_payload(raw_tile_inputs))
    processing_parameters_hash = stable_json_hash(_normalize_payload(processing_parameters))
    combined_hash = hashlib.sha256(
        f"{raw_tile_hash}:{processing_parameters_hash}".encode("utf-8")
    ).hexdigest()

    record = ProvenanceRecord(
        anomaly_id=anomaly_id,
        source_system=source_system,
        raw_tile_hash=raw_tile_hash,
        processing_parameters_hash=processing_parameters_hash,
        combined_hash=combined_hash,
        created_at=datetime.now(timezone.utc).isoformat(),
        metadata=dict(metadata or {}),
    )
    return asdict(record)


def build_dataset_provenance(records: list[dict[str, Any]]) -> dict[str, Any]:
    normalized_records = sorted(records, key=lambda item: item.get("anomaly_id", ""))
    dataset_hash = stable_json_hash(normalized_records)
    return {
        "schema": "space-based-economic-intelligence.provenance.v1",
        "dataset_hash": dataset_hash,
        "record_count": len(normalized_records),
        "records": normalized_records,
    }


def _normalize_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, np.ndarray):
            normalized[key] = {
                "shape": list(value.shape),
                "dtype": str(value.dtype),
                "sha256": hash_numpy_array(value),
            }
        elif isinstance(value, (list, tuple)) and value and hasattr(value[0], "shape"):
            normalized[key] = [hash_numpy_array(item) for item in value]
        else:
            normalized[key] = value
    return normalized