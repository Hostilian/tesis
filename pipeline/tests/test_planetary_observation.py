"""Offline checks for credential-free *observed* COG preview processing.

Fabricated arrays are used only inside tests; no live scene is asserted here.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from pipeline.planetary_observation import (
    mask_real_pixels,
    _boa_offset_dn,
    save_private_sample,
    PC_ASSET_KEY,
    select_scene_metadata,
)

BANDS = ("B2", "B3", "B4", "B8", "B11")


def _scene(id_: str, cloud: float, bands: tuple[str, ...] = tuple(PC_ASSET_KEY.values())) -> SimpleNamespace:
    return SimpleNamespace(
        id=id_,
        assets={k: SimpleNamespace(href="not-requested-in-test") for k in (*bands, "SCL")},
        properties={"eo:cloud_cover": cloud, "datetime": "2024-10-09T12:00:00Z"},
    )


def test_scene_selection_prefers_low_cloud_with_full_bands() -> None:
    items = [_scene("hi", 50), _scene("lo", 15), _scene("missing", 2, ("B02",))]
    assert select_scene_metadata(items).id == "lo"


def test_empty_or_invalid_assets_fail_closed() -> None:
    with pytest.raises(ValueError):
        select_scene_metadata([])
    with pytest.raises(ValueError):
        select_scene_metadata([_scene("wrong", 5, ("B02",))])


def test_scl_masks_cloud_and_invalid_pixels() -> None:
    source = {key: np.full((6, 6), 1000.0) for key in BANDS}
    source["B8"][:] = 3000.0
    scl = np.full((6, 6), 4.0)
    scl[0, 0] = 9.0
    bands = mask_real_pixels(source, scl)
    assert np.isnan(bands["B2"][0, 0])
    assert "B02" not in bands
    assert bands["B2"][1, 1] == pytest.approx(0.1)
    assert bands["B8"][1, 1] == pytest.approx(0.3)


def test_cloudy_entire_window_is_rejected() -> None:
    source = {key: np.full((6, 6), 1000.0) for key in BANDS}
    with pytest.raises(ValueError, match="Insufficient"):
        mask_real_pixels(source, np.full((6, 6), 9.0))


def test_private_manifest_does_not_claim_validation(tmp_path: Path) -> None:
    source = {key: np.full((6, 6), 1000.0) for key in BANDS}
    source["B8"][:] = 3000.0
    bands = mask_real_pixels(source, np.full((6, 6), 4.0))
    pixels, manifest = save_private_sample(
        bands,
        {"scene_id": "TEST_ONLY", "evidence_state": "real_pixel_inputs_unvalidated"},
        tmp_path,
    )
    info = json.loads(manifest.read_text())
    assert pixels.exists()
    assert info["scientific_validation"] == "not_performed"
    assert info["model_performance"] == "not_evaluated"
    assert info["independent_ground_truth"] == "not_available"
    assert len(info["checksum_sha256"]) == 64


def test_official_baseline_offset_for_post_2022_products() -> None:
    """ESA PB 04.00+ BOA SR=(DN-1000)/10000; never DN/10000."""
    source = {key: np.full((6, 6), 3000.0) for key in BANDS}
    source["B4"][:] = 2000.0
    source["B8"][:] = 4000.0
    assert _boa_offset_dn("05.11") == -1000
    adjusted = mask_real_pixels(
        source, np.full((6, 6), 4.0), boa_add_offset_dn=_boa_offset_dn("05.11")
    )
    assert adjusted["B4"][1, 1] == pytest.approx(0.1)
    assert adjusted["B8"][1, 1] == pytest.approx(0.3)
    assert _boa_offset_dn("03.01") == 0


@pytest.mark.parametrize("baseline", [None, "", "unknown", "0.00", "999"])
def test_unknown_radiometry_fails_closed(baseline: str | None) -> None:
    with pytest.raises(ValueError, match="baseline"):
        _boa_offset_dn(baseline)
