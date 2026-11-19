"""Synthetic orchard evidence rehearsal; never sends private farm data.

Usage: python -m pipeline.run_agriculture_pilot
Or explicitly authorised catalogue metadata search:
    python -m pipeline.run_agriculture_pilot --public-feature path/to/public.geojson \
       --approve-external-disclosure
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pipeline.src.agriculture_pilot import (
    execute_stac_discovery,
    ndvi,
    robust_deviation,
    stac_search_request,
)


def demonstration() -> dict[str, Any]:
    """Produce invented signals, never mistaken for actual orchard telemetry."""
    history = [
        ndvi(nir, red)
        for nir, red in [
            (0.50, 0.12),
            (0.48, 0.12),
            (0.53, 0.13),
            (0.51, 0.13),
            (0.49, 0.12),
            (0.52, 0.14),
        ]
    ]
    if any(v is None for v in history):
        raise ValueError("Unexpected invalid demonstration reflectance")
    historical = [float(value) for value in history if value is not None]
    current = ndvi(0.35, 0.17)
    assert current is not None
    return {
        "source_mode": "synthetic_demo",
        "verification_status": "unverified",
        "notice": (
            "Invented band reflectances; no satellite acquisition or "
            "independent orchard ground truth was used"
        ),
        "mock_ndvi": current,
        "synthetic_robust_deviation": robust_deviation(current, historical),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--public-feature",
        type=Path,
        help="Public or authorised WGS84 GeoJSON study Feature; optional",
    )
    parser.add_argument(
        "--approve-external-disclosure",
        action="store_true",
        help="Required before sending this geometry to a public STAC provider",
    )
    parser.add_argument("--start", default="2025-04-01")
    parser.add_argument("--end", default="2025-10-01")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    if args.public_feature is None:
        print(json.dumps(demonstration(), indent=2))
        return
    if not args.approve_external_disclosure:
        parser.error(
            "--approve-external-disclosure is mandatory for external STAC searches"
        )
    feature = json.loads(args.public_feature.read_text(encoding="utf-8"))
    request = stac_search_request(feature, args.start, args.end, args.limit)
    scenes = execute_stac_discovery(
        request, approved_public_geometry=args.approve_external_disclosure
    )
    print(
        json.dumps(
            {
                "source_mode": "public_stac_metadata",
                "pixel_assets_read": False,
                "verification_status": "unverified",
                "scenes": scenes,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
