"""Run the explicit synthetic orchard example without network or company assets.

Run from the repository root: python -m pipeline.run_agriculture_pilot
"""
from __future__ import annotations

import json
from pipeline.src.agriculture_pilot import ndvi, robust_deviation, stac_search_request


def demonstration():
    sample_area = {
        "type": "Feature", "properties": {"id": "PUBLIC_SYNTHETIC_EXAMPLE"},
        "geometry": {"type": "Polygon", "coordinates": [[
            [-1.000, 40.000], [-1.000, 40.010],
            [-0.990, 40.010], [-0.990, 40.000], [-1.000, 40.000],
        ]]},
    }
    # Made-up reflectance examples, deliberately not location-linked observations.
    history = [ndvi(nir, red) for nir, red in [
        (0.50, 0.12), (0.48, 0.12), (0.53, 0.13),
        (0.51, 0.13), (0.49, 0.12), (0.52, 0.14),
    ]]
    current = ndvi(0.35, 0.17)
    return {
        "source_mode": "synthetic",
        "verification_status": "demonstration",
        "notice": "Invented band reflectances; no acquisitions downloaded; not crop-health evidence",
        "stac_query_template": stac_search_request(sample_area, "2025-04-01", "2025-10-01"),
        "mock_ndvi": current,
        "synthetic_robust_deviation": robust_deviation(current, history),
    }


if __name__ == "__main__":
    print(json.dumps(demonstration(), indent=2))
