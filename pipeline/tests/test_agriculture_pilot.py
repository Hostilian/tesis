"""Scientific-integrity tests, including no-network defaults for orchard pilot."""

from __future__ import annotations

from typing import Any

import pytest

from pipeline.run_agriculture_pilot import demonstration
from pipeline.src.agriculture_pilot import (
    CDSE_STAC_SEARCH_URL,
    execute_stac_discovery,
    ndmi,
    ndvi,
    robust_deviation,
    stac_search_request,
    validate_study_area,
)


def _public_polygon() -> dict[str, Any]:
    return {
        "type": "Feature",
        "properties": {"id": "PUBLIC_SYNTHETIC_TEST"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-1, 40],
                    [-1, 40.01],
                    [-0.99, 40.01],
                    [-0.99, 40],
                    [-1, 40],
                ]
            ],
        },
    }


def test_stac_search_does_not_send_data() -> None:
    query = stac_search_request(_public_polygon(), "2025-04-01", "2025-10-01")
    assert query["network_performed"] is False
    assert query["url"] == CDSE_STAC_SEARCH_URL
    assert query["json"]["collections"] == ["sentinel-2-l2a"]
    assert execute_stac_discovery.__name__ == "execute_stac_discovery"


def test_requires_explicit_authorisation_before_external_query() -> None:
    query = stac_search_request(_public_polygon(), "2025-04-01", "2025-10-01")

    class BlockNetwork:
        def post(self, *args: Any, **kwargs: Any) -> None:
            raise AssertionError("The network should not be called")

    with pytest.raises(PermissionError):
        execute_stac_discovery(query, session=BlockNetwork())  # type: ignore[arg-type]


def test_authorised_stac_only_returns_sanitised_metadata() -> None:
    class Response:
        @staticmethod
        def raise_for_status() -> None:
            return None

        @staticmethod
        def json() -> dict[str, Any]:
            return {
                "type": "FeatureCollection",
                "features": [
                    {
                        "id": "S2A_TEST_NOT_A_REAL_ACQUISITION",
                        "collection": "sentinel-2-l2a",
                        "geometry": {"sensitive": "never-return"},
                        "properties": {
                            "datetime": "2025-01-01T00:00:00Z",
                            "eo:cloud_cover": 7.4,
                        },
                        "assets": {
                            "B04": {
                                "href": "https://example.invalid/private?secret=do-not-show"
                            }
                        },
                    }
                ],
            }

    class Session:
        def post(self, url: str, **kwargs: Any) -> Response:
            assert url == CDSE_STAC_SEARCH_URL
            assert kwargs["timeout"] == 30
            return Response()

    items = execute_stac_discovery(
        stac_search_request(_public_polygon(), "2025-01-01", "2025-02-01"),
        approved_public_geometry=True,
        session=Session(),  # type: ignore[arg-type]
    )
    assert len(items) == 1
    assert items[0]["product_id"] == "S2A_TEST_NOT_A_REAL_ACQUISITION"
    assert items[0]["asset_keys"] == ["B04"]
    assert items[0]["pixel_assets_read"] is False
    assert "secret" not in str(items)
    assert "geometry" not in items[0]


def test_geometry_and_dates_require_validity() -> None:
    g = _public_polygon()
    assert validate_study_area(g) == g["geometry"]
    with pytest.raises(ValueError):
        stac_search_request(g, "2026-07-01", "2026-06-01")
    with pytest.raises(ValueError):
        stac_search_request(g, "2026-01-01", "2026-02-01", limit=0)
    with pytest.raises(ValueError):
        validate_study_area({**g, "crs": "EPSG:3857"})
    with pytest.raises(ValueError):
        validate_study_area({"type": "Feature", "geometry": {"type": "Point"}})
    with pytest.raises(ValueError):
        validate_study_area(
            {
                **g,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0]]],
                },
            }
        )


def test_ndvi_and_ndmi_are_different_concepts() -> None:
    assert ndvi(0.8, 0.2) == pytest.approx(0.6)
    assert ndmi(0.8, 0.4) == pytest.approx(1 / 3)
    assert ndvi(0, 0) is None
    assert ndmi(0, 0) is None
    with pytest.raises(ValueError):
        ndvi(float("nan"), 0.5)


def test_mad_never_invents_infinite_certainty() -> None:
    result = robust_deviation(0.4, [0.3] * 5)
    assert result["robust_z"] is None
    with pytest.raises(ValueError):
        robust_deviation(0.4, [0.2, 0.3])


def test_demo_cannot_claim_real_observation() -> None:
    data = demonstration()
    assert data["source_mode"] == "synthetic_demo"
    assert data["verification_status"] == "unverified"
    assert "mock_ndvi" in data
    assert "satellite_scene_ids" not in data
