"""Tests for fail-closed experimental Earth Engine pixel acquisition."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from pipeline.real_observation import (
    decode_sample,
    fetch_observed_sample,
    save_observation,
    validate_request,
    _ensure_private_path,
)

BBOX = [-68.25, -23.48, -68.24, -23.47]


def test_small_request_passes() -> None:
    first, last = validate_request(BBOX, "2024-10-01", "2024-10-15")
    assert first.isoformat() == "2024-10-01"
    assert last.isoformat() == "2024-10-15"


@pytest.mark.parametrize(
    "bbox",
    [
        [-68.5, -23.8, -68.1, -23.2],  # huge study region
        [-68.2, -23.3, -68.2, -23.1],
        [float("nan"), -23.3, -68.1, -23.1],
        [1000, -23.4, 1001, -23.3],
    ],
)
def test_reject_bad_region(bbox: list[float]) -> None:
    with pytest.raises(ValueError):
        validate_request(bbox, "2024-10-01", "2024-10-15")


def test_bad_dates_rejected() -> None:
    with pytest.raises(ValueError):
        validate_request(BBOX, "2024-10-15", "2024-10-01")
    with pytest.raises(ValueError):
        validate_request(BBOX, "2024-01-01", "2024-12-01")


def test_observed_raster_decoder_rejects_incomplete_data() -> None:
    with pytest.raises(ValueError):
        decode_sample({"B2": [[1000.0]]})
    with pytest.raises(ValueError):
        decode_sample({name: [[-9999.0] * 6] * 6 for name in ("B2", "B3", "B4", "B8", "B11")})


def test_decoder_rejects_misaligned_bands() -> None:
    pixels = {name: np.full((5, 6), 1000.0) for name in ("B2", "B3", "B4", "B8", "B11")}
    pixels["B11"] = np.full((6, 5), 1000.0)
    with pytest.raises(ValueError, match="same grid"):
        decode_sample(pixels)


def test_mock_mode_refused_before_gee(monkeypatch: Any) -> None:
    monkeypatch.setenv("MOCK_MODE", "true")
    with pytest.raises(RuntimeError, match="rejects MOCK_MODE"):
        fetch_observed_sample(BBOX, "2024-10-01", "2024-10-15")


def test_public_docs_path_refused(tmp_path: Path) -> None:
    project = Path(__file__).resolve().parents[2]
    with pytest.raises(ValueError, match="docs"):
        _ensure_private_path(project / "docs" / "secret_observation")


def test_saved_observation_manifest_is_unvalidated(tmp_path: Path) -> None:
    # Test-only fabricated values deliberately must NOT become public output.
    sample = {name: [[1000.0] * 6 for _ in range(6)] for name in ("B2", "B3", "B4", "B8", "B11")}
    sample["B8"] = [[3000.0] * 6 for _ in range(6)]
    bands = decode_sample(sample)
    npz, metadata = save_observation(
        bands,
        ["TEST_ONLY_NOT_A_REAL_SCENE"],
        BBOX,
        "2024-10-01",
        "2024-10-15",
        tmp_path,
    )
    info = json.loads(metadata.read_text(encoding="utf-8"))
    assert npz.exists()
    assert info["status"] == "real_pixel_inputs_unvalidated"
    assert info["scientific_validation"] == "not_performed"
    assert info["checksum_sha256"]
    assert info["scene_identifiers"] == ["TEST_ONLY_NOT_A_REAL_SCENE"]
    with np.load(npz) as arrays:
        assert "ndvi" in arrays
        assert arrays["ndvi"].shape == (6, 6)
