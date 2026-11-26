"""Guard the additive correction and joint land mask used in the Alentejo case."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


def test_product_offsets_are_applied_before_ndvi(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "research/prototypes"))
    import alentejo_change as case

    bands = {
        "SCL": np.array([[4, 5, 9, 4]]),
        "B04": np.array([[2000., 2000., 2000., 0.]]),
        "B08": np.array([[4000., 4000., 4000., 4000.]]),
    }
    xml = (b"<metadata><BOA_QUANTIFICATION_VALUE>10000</BOA_QUANTIFICATION_VALUE>"
           b'<BOA_ADD_OFFSET band_id="3">-1000</BOA_ADD_OFFSET>'
           b'<BOA_ADD_OFFSET band_id="7">-1000</BOA_ADD_OFFSET></metadata>')
    scene = SimpleNamespace(
        id="fixture", properties={"datetime": "fixture", "s2:processing_baseline": "fixture"},
        assets={"product-metadata": SimpleNamespace(href="fixture")},
    )
    monkeypatch.setattr(case.pilot, "read_real_bands", lambda _: bands)
    monkeypatch.setattr(case.requests, "get", lambda *args, **kwargs: SimpleNamespace(status_code=200, content=xml))
    values, metadata = case.calibrate(scene)
    assert values[0, :2] == pytest.approx([0.5, 0.5])
    assert np.isnan(values[0, 2:]).all()
    assert metadata["valid_cells"] == 2
