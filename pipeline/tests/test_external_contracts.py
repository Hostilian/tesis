"""Offline contract regressions for external catalogue and economic adapters."""

from __future__ import annotations

from typing import Any

from pipeline.src.config import PipelineConfig
from pipeline.src.ingestion import SatelliteDataIngester


def test_cdse_stac_points_to_current_catalogue() -> None:
    client = SatelliteDataIngester(config=PipelineConfig(mock_mode=True))
    assert client.cdse.base_url == "https://stac.dataspace.copernicus.eu/v1"


def test_mock_imf_is_missing_not_zero_growth() -> None:
    client = SatelliteDataIngester(config=PipelineConfig(mock_mode=True))
    data = client.fetch_imf_weo_data("NGDP_RPCH", ["CZE"], 2023, 2024)
    assert data == {"CZE": [None, None]}


def test_missing_imf_does_not_generate_false_gdp_discrepancy(monkeypatch: Any) -> None:
    client = SatelliteDataIngester(config=PipelineConfig(mock_mode=True))
    monkeypatch.setattr(
        client,
        "fetch_worldbank_gdp",
        lambda *args: [{"year": 2024, "gdp_growth_pct": 1.8}],
    )
    assert client.flag_wb_imf_discrepancies("CZ", "CZE", 2024, 2024) == []


def test_imf_period_query_preserves_missing_years(monkeypatch: Any) -> None:
    client = SatelliteDataIngester(config=PipelineConfig(mock_mode=False))
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_request(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        assert method == "GET"
        calls.append((url, kwargs["params"]))
        return {
            "structure": {
                "dimensions": {
                    "observation": [
                        {"values": [{"id": "2023"}, {"id": "2024"}]}
                    ]
                }
            },
            "dataSets": [
                {
                    "series": {
                        "0:0:0": {"observations": {"1": ["1.8"]}}
                    }
                }
            ],
        }

    monkeypatch.setattr(client.http, "request_json", fake_request)
    data = client.fetch_imf_weo_data("NGDP_RPCH", ["CZE"], 2023, 2024)
    assert data == {"CZE": [None, 1.8]}
    assert calls == [
        (
            "https://api.imf.org/external/sdmx/2.1/data/"
            "IMF.RES,WEO,9.0.0/CZE.NGDP_RPCH",
            {"startPeriod": "2023", "endPeriod": "2024"},
        )
    ]
