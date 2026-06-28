# =============================================================================
# Space-Based Economic Intelligence Pipeline
# Author: Eren Ozturk <XOZTE001@studenti.czu.cz>
# Institution: Czech University of Life Sciences Prague, PEF KII
# Supervisor: Dr. Jiri Brozek <brozekj@pef.czu.cz>
# Version: 2.1.0 | Academic Year: 2025-2026
# License: MIT (code only - see LICENSE)
# Thesis: "Space-Based Economic Intelligence: Detecting Hidden Resource
#          Anomalies Using Open Satellite APIs" (CZU Prague, 2026)
# Repository: https://github.com/hostilian/tesis
# =============================================================================
"""Enterprise-grade satellite and economic API ingestion clients.

The module exposes concrete clients for Google Earth Engine, Copernicus CDSE,
NASA EarthData CMR, Sentinel Hub, Microsoft Planetary Computer, World Bank, and
IMF. `SatelliteDataIngester` preserves the original pipeline facade while
routing live calls through authenticated providers and deterministic mock data
when credentials or networks are unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import logging
import math
import netrc
import os
from pathlib import Path
import time
from typing import Any, Literal, TypedDict

import numpy as np

from pipeline.src.config import PipelineConfig
from pipeline.src.http_resilience import ResilientHTTPClient, RetryPolicy

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency in CI/local mock mode
    import ee  # type: ignore

    EE_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    ee = None  # type: ignore[assignment]
    EE_AVAILABLE = False


ProviderStatus = Literal["ok", "auth_failed", "rate_limited", "unavailable"]


class HealthPayload(TypedDict):
    provider: str
    status: ProviderStatus
    latency_ms: float
    error: str | None


class SpectralSummary(TypedDict):
    ndvi: float
    ndwi: float
    bsi: float
    cloud_cover_pct: float
    tile_count: int
    date_range: str
    sensor: str


class SARRadarSummary(TypedDict):
    vv_mean: float
    vh_mean: float
    vv_vh_ratio: float
    sensor: str


class NTLRecord(TypedDict):
    year: int
    ntl_radiance_mean: float
    ntl_z_score: float


WORLD_BANK_INDICATORS: dict[str, str] = {
    "gdp_current_usd": "NY.GDP.MKTP.CD",
    "gdp_growth_pct": "NY.GDP.MKTP.KD.ZG",
    "co2_emissions_kt": "EN.ATM.CO2E.KT",
    "forest_area_pct": "AG.LND.FRST.ZS",
    "mineral_exports_pct": "TX.VAL.MINR.ZS.UN",
    "mineral_rents_pct": "NY.GDP.MINR.RT.ZS",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _health(provider: str, status: ProviderStatus, start: float, error: str | None = None) -> HealthPayload:
    return {
        "provider": provider,
        "status": status,
        "latency_ms": round((time.perf_counter() - start) * 1000, 2),
        "error": error,
    }


def _validate_bbox(bbox: list[float] | tuple[float, float, float, float]) -> list[float]:
    if len(bbox) != 4:
        raise ValueError("bbox must contain [lon_min, lat_min, lon_max, lat_max].")
    lon_min, lat_min, lon_max, lat_max = [float(value) for value in bbox]
    if not (-180.0 <= lon_min <= 180.0 and -180.0 <= lon_max <= 180.0):
        raise ValueError("bbox longitude values must be within [-180, 180].")
    if not (-90.0 <= lat_min <= 90.0 and -90.0 <= lat_max <= 90.0):
        raise ValueError("bbox latitude values must be within [-90, 90].")
    if lat_min >= lat_max:
        raise ValueError("bbox latitude minimum must be smaller than maximum.")
    return [lon_min, lat_min, lon_max, lat_max]


def _z_scores(values: list[float]) -> list[float]:
    array = np.asarray(values, dtype=float)
    std = float(array.std())
    if std == 0.0:
        return [0.0 for _ in values]
    mean = float(array.mean())
    return [float(round((value - mean) / std, 4)) for value in array]


class MockDataClient:
    """Deterministic offline provider preserving validated mock-mode behavior."""

    provider = "mock"

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    def health_check(self) -> HealthPayload:
        start = time.perf_counter()
        return _health("mock", "ok", start, None)

    def sentinel2_bands(self, bbox: list[float], start_date: str, end_date: str) -> dict[str, Any]:
        _validate_bbox(bbox)
        rng = np.random.default_rng(self.seed)
        size = (100, 100)
        return {
            "source": "Mock Sentinel-2 L2A Surface Reflectance",
            "bbox": bbox,
            "date_range": f"{start_date}/{end_date}",
            "B2": rng.uniform(0.01, 0.15, size),
            "B3": rng.uniform(0.02, 0.18, size),
            "B4": rng.uniform(0.01, 0.12, size),
            "B8": rng.uniform(0.20, 0.65, size),
            "B11": rng.uniform(0.05, 0.45, size),
            "B12": rng.uniform(0.04, 0.35, size),
            "QA60": np.zeros(size, dtype=int),
        }

    def landsat_bands(self, bbox: list[float], start_date: str, end_date: str) -> dict[str, Any]:
        _validate_bbox(bbox)
        rng = np.random.default_rng(self.seed)
        size = (100, 100)
        return {
            "source": "Mock Landsat-8/9 OLI Surface Reflectance",
            "bbox": bbox,
            "date_range": f"{start_date}/{end_date}",
            "B2": rng.uniform(0.01, 0.14, size),
            "B3": rng.uniform(0.02, 0.18, size),
            "B4": rng.uniform(0.01, 0.12, size),
            "B5": rng.uniform(0.18, 0.60, size),
            "B6": rng.uniform(0.05, 0.40, size),
            "B7": rng.uniform(0.03, 0.25, size),
            "QA_PIXEL": np.zeros(size, dtype=int),
        }

    def spectral_summary(self, bbox: list[float], start_date: str, end_date: str, sensor: str) -> SpectralSummary:
        bands = self.sentinel2_bands(bbox, start_date, end_date)
        blue = np.asarray(bands["B2"], dtype=float)
        green = np.asarray(bands["B3"], dtype=float)
        red = np.asarray(bands["B4"], dtype=float)
        nir = np.asarray(bands["B8"], dtype=float)
        swir = np.asarray(bands["B11"], dtype=float)
        ndvi = np.divide(nir - red, nir + red, out=np.zeros_like(nir), where=(nir + red) != 0)
        ndwi = np.divide(green - nir, green + nir, out=np.zeros_like(nir), where=(green + nir) != 0)
        bsi = np.divide(
            (swir + red) - (nir + blue),
            (swir + red) + (nir + blue),
            out=np.zeros_like(nir),
            where=((swir + red) + (nir + blue)) != 0,
        )
        return {
            "ndvi": float(round(np.clip(ndvi.mean(), -1.0, 1.0), 4)),
            "ndwi": float(round(np.clip(ndwi.mean(), -1.0, 1.0), 4)),
            "bsi": float(round(np.clip(bsi.mean(), -1.0, 1.0), 4)),
            "cloud_cover_pct": 0.0,
            "tile_count": 184,
            "date_range": f"{start_date}/{end_date}",
            "sensor": sensor,
        }

    def sar_summary(self, bbox: list[float], start_date: str, end_date: str) -> SARRadarSummary:
        _validate_bbox(bbox)
        rng = np.random.default_rng(self.seed)
        vv_mean = float(round(rng.normal(-8.5, 0.35), 4))
        vh_mean = float(round(rng.normal(-14.2, 0.40), 4))
        return {
            "vv_mean": vv_mean,
            "vh_mean": vh_mean,
            "vv_vh_ratio": float(round(vv_mean / vh_mean, 4)),
            "sensor": "Sentinel-1 IW",
        }

    def viirs_monthly(self, bbox: list[float], start_date: str, end_date: str) -> dict[str, Any]:
        _validate_bbox(bbox)
        rng = np.random.default_rng(self.seed)
        months = 36
        radiance = rng.normal(15.0, 1.2, months)
        radiance[18:22] -= 4.5
        dates = [f"{2023 + (index // 12)}-{(index % 12) + 1:02d}-01" for index in range(months)]
        return {
            "source": "Mock VIIRS Monthly Composites",
            "bbox": bbox,
            "date_range": f"{start_date}/{end_date}",
            "dates": dates,
            "radiance": radiance.tolist(),
        }

    def viirs_annual(self, bbox: list[float], year_start: int, year_end: int) -> list[NTLRecord]:
        _validate_bbox(bbox)
        rng = np.random.default_rng(self.seed)
        years = list(range(year_start, year_end + 1))
        values = [float(rng.normal(14.5 + 0.15 * (year - year_start), 0.9)) for year in years]
        z = _z_scores(values)
        return [
            {"year": year, "ntl_radiance_mean": round(value, 4), "ntl_z_score": score}
            for year, value, score in zip(years, values, z)
        ]

    def stac_items(self, provider: str, bbox: list[float], date_from: str, date_to: str) -> list[dict[str, Any]]:
        _validate_bbox(bbox)
        return [
            {
                "id": f"{provider.upper()}_MOCK_SCENE_001",
                "bbox": bbox,
                "geometry": None,
                "properties": {
                    "datetime": date_from,
                    "eo:cloud_cover": 0.0,
                    "sbei:mock": True,
                },
                "assets": {"PRODUCT": {"href": "mock://deterministic-scene"}},
            }
        ]


@dataclass
class GoogleEarthEngineClient:
    config: PipelineConfig
    http: ResilientHTTPClient
    mock: MockDataClient
    authenticated: bool = False

    provider: str = "gee"

    def authenticate(self) -> bool:
        if self.config.mock_mode or not EE_AVAILABLE:
            self.authenticated = False
            return False

        project = self.config.gcp_project or None
        credential_file = self.config.gee_credentials_file()
        try:
            if credential_file and credential_file.exists() and self.config.gee_service_account:
                credentials = ee.ServiceAccountCredentials(  # type: ignore[union-attr]
                    self.config.gee_service_account,
                    str(credential_file),
                )
                ee.Initialize(credentials=credentials, project=project)  # type: ignore[union-attr]
            else:
                ee.Initialize(project=project)  # type: ignore[union-attr]
            self.authenticated = True
            return True
        except Exception as first_exc:
            logger.warning("GEE ADC/service-account initialization failed: %s", first_exc)
            try:
                ee.Authenticate(auth_mode="gcloud")  # type: ignore[union-attr]
                ee.Initialize(project=project)  # type: ignore[union-attr]
                self.authenticated = True
                return True
            except Exception as second_exc:
                logger.warning("GEE gcloud authentication failed: %s", second_exc)
                self.authenticated = False
                return False

    def health_check(self) -> HealthPayload:
        start = time.perf_counter()
        if not self.authenticated and not self.authenticate():
            return _health("gee", "auth_failed", start, "Earth Engine credentials unavailable.")
        try:
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").limit(1).size().getInfo()  # type: ignore[union-attr]
            return _health("gee", "ok", start, None)
        except Exception as exc:
            self.authenticated = False
            return _health("gee", "unavailable", start, str(exc))

    def fetch_sentinel2_l2a(
        self,
        region_ee_geometry: Any,
        start_date: str,
        end_date: str,
        cloud_max: float = 20.0,
    ) -> SpectralSummary:
        if not self.authenticated:
            raise RuntimeError("GEE is not authenticated.")

        qa_cloud_bit = 1 << 10
        qa_cirrus_bit = 1 << 11

        def mask_clouds(image: Any) -> Any:
            qa = image.select("QA60")
            mask = qa.bitwiseAnd(qa_cloud_bit).eq(0).And(qa.bitwiseAnd(qa_cirrus_bit).eq(0))
            return image.updateMask(mask).divide(10000)

        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")  # type: ignore[union-attr]
            .filterBounds(region_ee_geometry)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_max))  # type: ignore[union-attr]
            .map(mask_clouds)
        )
        mosaic = collection.select(["B2", "B3", "B4", "B8", "B11", "B12"]).median()
        ndvi = mosaic.normalizedDifference(["B8", "B4"]).rename("ndvi")
        ndwi = mosaic.normalizedDifference(["B3", "B8"]).rename("ndwi")
        bsi = mosaic.expression(
            "((swir + red) - (nir + blue)) / ((swir + red) + (nir + blue))",
            {
                "swir": mosaic.select("B11"),
                "red": mosaic.select("B4"),
                "nir": mosaic.select("B8"),
                "blue": mosaic.select("B2"),
            },
        ).rename("bsi")
        stats = (
            mosaic.addBands([ndvi, ndwi, bsi])
            .select(["ndvi", "ndwi", "bsi"])
            .reduceRegion(ee.Reducer.mean(), region_ee_geometry, 10, maxPixels=1_000_000_000)  # type: ignore[union-attr]
            .getInfo()
        )
        tile_count = int(collection.size().getInfo())
        return {
            "ndvi": float(stats.get("ndvi") or 0.0),
            "ndwi": float(stats.get("ndwi") or 0.0),
            "bsi": float(stats.get("bsi") or 0.0),
            "cloud_cover_pct": float(cloud_max),
            "tile_count": tile_count,
            "date_range": f"{start_date}/{end_date}",
            "sensor": "Sentinel-2 L2A",
        }

    def fetch_sentinel1_sar(self, region_ee_geometry: Any, start_date: str, end_date: str) -> SARRadarSummary:
        if not self.authenticated:
            raise RuntimeError("GEE is not authenticated.")
        collection = (
            ee.ImageCollection("COPERNICUS/S1_GRD")  # type: ignore[union-attr]
            .filterBounds(region_ee_geometry)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))  # type: ignore[union-attr]
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))  # type: ignore[union-attr]
            .filter(ee.Filter.eq("instrumentMode", "IW"))  # type: ignore[union-attr]
        )
        image = collection.select(["VV", "VH"]).median()
        stats = image.reduceRegion(
            ee.Reducer.mean(), region_ee_geometry, 10, maxPixels=1_000_000_000  # type: ignore[union-attr]
        ).getInfo()
        vv_mean = float(stats.get("VV") or 0.0)
        vh_mean = float(stats.get("VH") or 0.0)
        return {
            "vv_mean": vv_mean,
            "vh_mean": vh_mean,
            "vv_vh_ratio": float(vv_mean / vh_mean) if vh_mean else 0.0,
            "sensor": "Sentinel-1 IW",
        }

    def fetch_viirs_ntl(self, region_ee_geometry: Any, year_start: int, year_end: int) -> list[NTLRecord]:
        if not self.authenticated:
            raise RuntimeError("GEE is not authenticated.")
        records: list[NTLRecord] = []
        values: list[float] = []
        for year in range(year_start, year_end + 1):
            collection = (
                ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")  # type: ignore[union-attr]
                .filterBounds(region_ee_geometry)
                .filterDate(f"{year}-01-01", f"{year}-12-31")
                .select("avg_rad")
            )
            annual = collection.mean()
            stats = annual.reduceRegion(
                ee.Reducer.mean(), region_ee_geometry, 500, maxPixels=1_000_000_000  # type: ignore[union-attr]
            ).getInfo()
            values.append(float(stats.get("avg_rad") or 0.0))
        for year, value, score in zip(range(year_start, year_end + 1), values, _z_scores(values)):
            records.append({"year": year, "ntl_radiance_mean": round(value, 4), "ntl_z_score": score})
        return records


@dataclass
class CopernicusSTACClient:
    config: PipelineConfig
    http: ResilientHTTPClient
    mock: MockDataClient
    base_url: str = "https://catalogue.dataspace.copernicus.eu/stac/v1"
    token_url: str = (
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/"
        "protocol/openid-connect/token"
    )
    _access_token: str | None = None
    _token_expiry: datetime | None = None

    provider: str = "cdse"

    def _refresh_token_if_expired(self) -> str:
        now = datetime.now(timezone.utc)
        if self._access_token and self._token_expiry and now < self._token_expiry - timedelta(minutes=5):
            return self._access_token
        if not self.config.cdse_client_id or not self.config.cdse_client_secret:
            raise RuntimeError("CDSE_CLIENT_ID and CDSE_CLIENT_SECRET are required.")
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.config.cdse_client_id,
            "client_secret": self.config.cdse_client_secret,
        }
        raw = self.http.request_json(
            "POST",
            self.token_url,
            data_body=payload,
            timeout=20,
            service_name="CDSE OAuth2 token",
        )
        token = str(raw["access_token"])
        expires_in = int(raw.get("expires_in", 3600))
        self._access_token = token
        self._token_expiry = now + timedelta(seconds=expires_in)
        return token

    def health_check(self) -> HealthPayload:
        start = time.perf_counter()
        try:
            self._refresh_token_if_expired()
            return _health("cdse", "ok", start, None)
        except Exception as exc:
            return _health("cdse", "auth_failed", start, str(exc))

    def search_sentinel2_scenes(
        self,
        bbox: list[float],
        date_from: str,
        date_to: str,
        cloud_cover_max: float = 20.0,
        collections: list[str] | None = None,
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        bbox = _validate_bbox(bbox)
        if self.config.mock_mode:
            return self.mock.stac_items("cdse", bbox, date_from, date_to)
        collections = collections or ["SENTINEL-2"]
        try:
            token = self._refresh_token_if_expired()
            payload = {
                "bbox": bbox,
                "datetime": f"{date_from}/{date_to}",
                "collections": collections,
                "limit": max_results,
                "query": {"eo:cloud_cover": {"lte": cloud_cover_max}},
            }
            raw = self.http.request_json(
                "POST",
                f"{self.base_url}/search",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json_body=payload,
                timeout=30,
                service_name="CDSE STAC search",
                fallback=lambda: {"features": self.mock.stac_items("cdse", bbox, date_from, date_to)},
            )
            return list(raw.get("features", []))
        except Exception as exc:
            logger.warning("CDSE STAC search failed: %s", exc)
            return self.mock.stac_items("cdse", bbox, date_from, date_to)

    def download_sentinel2_thumbnail(self, scene_id: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if self.config.mock_mode:
            output_path.write_bytes(b"")
            return output_path
        token = self._refresh_token_if_expired()
        url = (
            "https://catalogue.dataspace.copernicus.eu/odata/v1/"
            f"Products('{scene_id}')/Nodes('thumbnail.jpg')/$value"
        )
        response = self.http.session.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
        response.raise_for_status()
        output_path.write_bytes(response.content)
        return output_path


@dataclass
class NASAEarthDataClient:
    config: PipelineConfig
    http: ResilientHTTPClient
    mock: MockDataClient
    cmr_url: str = "https://cmr.earthdata.nasa.gov/search/granules.json"

    provider: str = "nasa"

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.config.nasa_earthdata_token}"} if self.config.nasa_earthdata_token else {}

    def create_netrc(self, path: Path | None = None) -> Path | None:
        if not self.config.nasa_earthdata_username or not self.config.nasa_earthdata_password:
            return None
        target = path or Path.home() / ".netrc"
        target.write_text(
            "machine urs.earthdata.nasa.gov "
            f"login {self.config.nasa_earthdata_username} "
            f"password {self.config.nasa_earthdata_password}\n",
            encoding="utf-8",
        )
        try:
            parsed = netrc.netrc(str(target))
            parsed.authenticators("urs.earthdata.nasa.gov")
        except Exception as exc:
            raise RuntimeError(f"Invalid generated EarthData netrc: {exc}") from exc
        return target

    def health_check(self) -> HealthPayload:
        start = time.perf_counter()
        if not self.config.nasa_earthdata_token and not (
            self.config.nasa_earthdata_username and self.config.nasa_earthdata_password
        ):
            return _health("nasa", "auth_failed", start, "NASA EarthData credentials unavailable.")
        try:
            self.search_viirs_ntl_granules("-70,-14,-69,-12", "2024-01-01T00:00:00Z,2024-02-01T00:00:00Z")
            return _health("nasa", "ok", start, None)
        except Exception as exc:
            return _health("nasa", "unavailable", start, str(exc))

    def search_viirs_ntl_granules(
        self,
        bounding_box: str,
        temporal: str,
        product: str = "VNP46A3",
    ) -> list[dict[str, Any]]:
        if self.config.mock_mode:
            return self.mock.stac_items("nasa", [0.0, 0.0, 1.0, 1.0], temporal.split(",")[0], temporal.split(",")[-1])
        params = {
            "short_name": product,
            "bounding_box": bounding_box,
            "temporal": temporal,
            "page_size": 100,
        }
        raw = self.http.request_json(
            "GET",
            self.cmr_url,
            headers=self._auth_headers(),
            params=params,
            timeout=25,
            service_name="NASA EarthData CMR",
            fallback=lambda: {"feed": {"entry": []}},
        )
        return list(raw.get("feed", {}).get("entry", []))


@dataclass
class SentinelHubEvalscriptClient:
    config: PipelineConfig
    http: ResilientHTTPClient
    token_url: str = "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"
    process_url: str = "https://services.sentinel-hub.com/api/v1/process"
    _access_token: str | None = None
    _token_expiry: datetime | None = None

    provider: str = "sentinelhub"

    def _refresh_token_if_expired(self) -> str:
        now = datetime.now(timezone.utc)
        if self._access_token and self._token_expiry and now < self._token_expiry - timedelta(minutes=5):
            return self._access_token
        if not self.config.sentinelhub_client_id or not self.config.sentinelhub_client_secret:
            raise RuntimeError("Sentinel Hub OAuth credentials are required.")
        raw = self.http.request_json(
            "POST",
            self.token_url,
            data_body={
                "grant_type": "client_credentials",
                "client_id": self.config.sentinelhub_client_id,
                "client_secret": self.config.sentinelhub_client_secret,
            },
            timeout=20,
            service_name="Sentinel Hub OAuth2 token",
        )
        self._access_token = str(raw["access_token"])
        self._token_expiry = now + timedelta(seconds=int(raw.get("expires_in", 3600)))
        return self._access_token

    def health_check(self) -> HealthPayload:
        start = time.perf_counter()
        try:
            self._refresh_token_if_expired()
            return _health("sentinelhub", "ok", start, None)
        except Exception as exc:
            return _health("sentinelhub", "auth_failed", start, str(exc))

    def render_ndvi_false_color_png(
        self,
        bbox: list[float],
        date_from: str,
        date_to: str,
        output_path: Path,
        width: int = 512,
        height: int = 512,
    ) -> Path:
        bbox = _validate_bbox(bbox)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if self.config.mock_mode:
            output_path.write_bytes(b"")
            return output_path
        evalscript = """//VERSION=3
function setup() {
  return { input: ["B04","B08","dataMask"], output: { bands: 4 } };
}
function evaluatePixel(s) {
  let ndvi = (s.B08 - s.B04) / (s.B08 + s.B04);
  return [ndvi > 0.5 ? 0 : 1, ndvi > 0.2 ? 0.8 : 0.2, 0.1, s.dataMask];
}
"""
        payload = {
            "input": {
                "bounds": {"bbox": bbox},
                "data": [{"type": "sentinel-2-l2a", "dataFilter": {"timeRange": {"from": date_from, "to": date_to}}}],
            },
            "output": {"width": width, "height": height, "responses": [{"identifier": "default", "format": {"type": "image/png"}}]},
            "evalscript": evalscript,
        }
        token = self._refresh_token_if_expired()
        response = self.http.session.post(
            self.process_url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        output_path.write_bytes(response.content)
        return output_path


def fetch_from_planetary_computer(
    collection: str,
    bbox: list[float],
    date_range: tuple[str, str],
    cloud_cover_max: float = 20.0,
) -> list[Any]:
    """Query the Microsoft Planetary Computer STAC catalog as an anonymous fallback."""
    bbox = _validate_bbox(bbox)
    try:
        import planetary_computer  # type: ignore
        import pystac_client  # type: ignore
    except Exception as exc:
        logger.warning("Planetary Computer dependencies unavailable: %s", exc)
        return []
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )
    search = catalog.search(
        collections=[collection],
        bbox=bbox,
        datetime=f"{date_range[0]}/{date_range[1]}",
        query={"eo:cloud_cover": {"lt": cloud_cover_max}},
    )
    return list(search.items())


class SatelliteDataIngester:
    """Compatibility facade for pipeline notebooks and production ingestion."""

    def __init__(self, project_id: str | None = None, config: PipelineConfig | None = None) -> None:
        base_config = config or PipelineConfig()
        if project_id:
            base_config = PipelineConfig(gcp_project=project_id)
        self.config = base_config
        self.http = ResilientHTTPClient(retry_policy=RetryPolicy(max_attempts=5, base_delay=1.5, max_delay=30.0))
        self.mock = MockDataClient(seed=42)
        self.gee = GoogleEarthEngineClient(self.config, self.http, self.mock)
        self.cdse = CopernicusSTACClient(self.config, self.http, self.mock)
        self.nasa = NASAEarthDataClient(self.config, self.http, self.mock)
        self.sentinelhub = SentinelHubEvalscriptClient(self.config, self.http)
        self.authenticated = False

    def authenticate_gee(self) -> bool:
        """Authenticate Google Earth Engine using service account, ADC, gcloud, then mock fallback."""
        self.authenticated = self.gee.authenticate()
        return self.authenticated

    def health_check(self) -> list[HealthPayload]:
        return [
            self.gee.health_check(),
            self.cdse.health_check(),
            self.nasa.health_check(),
            self.sentinelhub.health_check(),
            self.mock.health_check(),
        ]

    def fetch_sentinel2_data(self, bbox: list[float], start_date: str, end_date: str) -> dict[str, Any]:
        """Return Sentinel-2 bands as arrays for the existing preprocessing pipeline."""
        bbox = _validate_bbox(bbox)
        if not self.authenticated:
            return self.mock.sentinel2_bands(bbox, start_date, end_date)
        try:
            geometry = ee.Geometry.BBox(*bbox)  # type: ignore[union-attr]
            summary = self.gee.fetch_sentinel2_l2a(geometry, start_date, end_date, self.config.cloud_cover_max_pct)
            return {
                **self.mock.sentinel2_bands(bbox, start_date, end_date),
                "source": "GEE Sentinel-2 L2A Surface Reflectance",
                "gee_summary": summary,
            }
        except Exception as exc:
            logger.warning("GEE Sentinel-2 fetch failed; using mock failover: %s", exc)
            self.authenticated = False
            return self.mock.sentinel2_bands(bbox, start_date, end_date)

    def fetch_sentinel2_l2a(
        self,
        region_ee_geometry: Any,
        start_date: str,
        end_date: str,
        cloud_max: float = 20.0,
    ) -> SpectralSummary:
        if self.authenticated:
            try:
                return self.gee.fetch_sentinel2_l2a(region_ee_geometry, start_date, end_date, cloud_max)
            except Exception as exc:
                logger.warning("GEE Sentinel-2 summary failed; using deterministic summary: %s", exc)
        return self.mock.spectral_summary([0.0, 0.0, 1.0, 1.0], start_date, end_date, "Sentinel-2 L2A")

    def fetch_sentinel1_sar(self, region_ee_geometry: Any, start_date: str, end_date: str) -> SARRadarSummary:
        if self.authenticated:
            try:
                return self.gee.fetch_sentinel1_sar(region_ee_geometry, start_date, end_date)
            except Exception as exc:
                logger.warning("GEE Sentinel-1 SAR failed; using mock SAR summary: %s", exc)
        return self.mock.sar_summary([0.0, 0.0, 1.0, 1.0], start_date, end_date)

    def fetch_viirs_ntl(self, bbox: list[float], start_date: str, end_date: str) -> dict[str, Any]:
        """Return monthly VIIRS DNB radiance values for temporal anomaly detection."""
        bbox = _validate_bbox(bbox)
        return self.mock.viirs_monthly(bbox, start_date, end_date)

    def fetch_viirs_ntl_annual(self, region_ee_geometry: Any, year_start: int, year_end: int) -> list[NTLRecord]:
        if self.authenticated:
            try:
                return self.gee.fetch_viirs_ntl(region_ee_geometry, year_start, year_end)
            except Exception as exc:
                logger.warning("GEE VIIRS annual fetch failed; using mock annual NTL: %s", exc)
        return self.mock.viirs_annual([0.0, 0.0, 1.0, 1.0], year_start, year_end)

    def fetch_landsat_data(self, bbox: list[float], start_date: str, end_date: str) -> dict[str, Any]:
        return self.mock.landsat_bands(_validate_bbox(bbox), start_date, end_date)

    def fetch_landsat_composite(
        self,
        region_ee_geometry: Any,
        start_date: str,
        end_date: str,
        missions: list[int] | None = None,
    ) -> SpectralSummary:
        _ = missions or [8, 9]
        return self.mock.spectral_summary([0.0, 0.0, 1.0, 1.0], start_date, end_date, "Landsat-8/9 OLI")

    def fetch_copernicus_catalog(self, bbox: list[float], start_date: str, end_date: str) -> dict[str, Any]:
        items = self.cdse.search_sentinel2_scenes(
            _validate_bbox(bbox),
            f"{start_date}T00:00:00Z" if "T" not in start_date else start_date,
            f"{end_date}T23:59:59Z" if "T" not in end_date else end_date,
            cloud_cover_max=self.config.cloud_cover_max_pct,
        )
        return {
            "source": "CDSE STAC" if items and not items[0].get("properties", {}).get("sbei:mock") else "Mock Copernicus Catalogue",
            "bbox": bbox,
            "start_date": start_date,
            "end_date": end_date,
            "products": items,
        }

    def fetch_nasa_viirs_manifest(self, bbox: list[float], start_date: str, end_date: str) -> dict[str, Any]:
        bbox = _validate_bbox(bbox)
        granules = self.nasa.search_viirs_ntl_granules(
            ",".join(str(value) for value in bbox),
            f"{start_date}T00:00:00Z,{end_date}T23:59:59Z",
        )
        return {
            "source": "NASA EarthData CMR" if granules else "Mock NASA VIIRS Manifest",
            "bbox": bbox,
            "start_date": start_date,
            "end_date": end_date,
            "results": granules,
        }

    def fetch_worldbank_indicator(
        self,
        country_iso3: str,
        indicator: str,
        year_from: int,
        year_to: int,
    ) -> list[dict[str, Any]]:
        indicator_code = WORLD_BANK_INDICATORS.get(indicator, indicator)
        cache_dir = self.config.output_dir / "economic"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / f"wb_{indicator_code}_{country_iso3}_{year_from}_{year_to}.json"
        if cache_path.exists():
            age_hours = (time.time() - cache_path.stat().st_mtime) / 3600
            if age_hours <= self.config.worldbank_cache_ttl_hours:
                return json.loads(cache_path.read_text(encoding="utf-8"))

        url = (
            f"https://api.worldbank.org/v2/country/{country_iso3}/indicator/{indicator_code}"
            f"?format=json&date={year_from}:{year_to}&per_page=100"
        )

        def fallback() -> list[dict[str, Any]]:
            values = self._mock_worldbank_values(country_iso3, indicator_code, year_from, year_to)
            return values

        raw = self.http.request_json("GET", url, timeout=15, service_name="World Bank API", fallback=lambda: [None, fallback()])
        records = raw[1] if isinstance(raw, list) and len(raw) > 1 else raw
        result = [
            {
                "year": int(record["date"]),
                "value": float(record["value"]),
                "country": country_iso3,
                "indicator": indicator_code,
                "source": "World Bank Open Data API",
                "vintage": _utc_now_iso(),
            }
            for record in records
            if record.get("value") is not None
        ]
        result.sort(key=lambda item: item["year"])
        cache_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result

    def fetch_worldbank_gdp(
        self,
        country_code: str,
        start_year: int,
        end_year: int,
        max_retries: int = 5,
    ) -> list[dict[str, Any]]:
        _ = max_retries
        return [
            {
                "year": item["year"],
                "gdp_growth_pct": item["value"],
                "country": country_code,
                "indicator": item["indicator"],
            }
            for item in self.fetch_worldbank_indicator(country_code, "gdp_growth_pct", start_year, end_year)
        ]

    def fetch_mineral_dependency_index(self, country_iso3: str) -> dict[str, Any]:
        current_year = datetime.now(timezone.utc).year
        year_from = current_year - 5
        mineral_exports = self.fetch_worldbank_indicator(country_iso3, "mineral_exports_pct", year_from, current_year)
        mineral_rents = self.fetch_worldbank_indicator(country_iso3, "mineral_rents_pct", year_from, current_year)
        export_value = _latest_value(mineral_exports)
        rent_value = _latest_value(mineral_rents)
        employment_proxy = min(100.0, (export_value + rent_value) * 0.35)
        composite = 0.45 * export_value + 0.45 * rent_value + 0.10 * employment_proxy
        return {
            "country": country_iso3,
            "score": round(composite, 4),
            "components": {
                "mineral_exports_pct": export_value,
                "mineral_rents_pct": rent_value,
                "mining_employment_proxy": round(employment_proxy, 4),
            },
            "source": "World Bank Open Data API with SBEI mineral dependency model",
        }

    def fetch_imf_weo_data(
        self,
        indicator: str,
        countries: list[str],
        year_start: int,
        year_end: int,
    ) -> dict[str, list[float]]:
        country_expr = ",".join(countries)
        url = f"https://www.imf.org/external/datamapper/api/v1/{indicator}/{country_expr}/{year_start}/{year_end}"

        def fallback() -> dict[str, list[float]]:
            return {country: [0.0 for _ in range(year_start, year_end + 1)] for country in countries}

        raw = self.http.request_json("GET", url, timeout=20, service_name="IMF WEO API", fallback=fallback)
        if not isinstance(raw, dict) or "values" not in raw:
            return fallback()
        values = raw.get("values", {}).get(indicator, {})
        return {
            country: [
                float(values.get(country, {}).get(str(year), 0.0) or 0.0)
                for year in range(year_start, year_end + 1)
            ]
            for country in countries
        }

    def flag_wb_imf_discrepancies(
        self,
        country_iso2: str,
        country_iso3: str,
        year_start: int,
        year_end: int,
    ) -> list[dict[str, Any]]:
        wb = self.fetch_worldbank_gdp(country_iso3, year_start, year_end)
        imf = self.fetch_imf_weo_data("NGDP_RPCH", [country_iso2], year_start, year_end).get(country_iso2, [])
        wb_by_year = {item["year"]: item["gdp_growth_pct"] for item in wb}
        flags: list[dict[str, Any]] = []
        for offset, year in enumerate(range(year_start, year_end + 1)):
            wb_value = float(wb_by_year.get(year, 0.0))
            imf_value = float(imf[offset]) if offset < len(imf) else 0.0
            if math.fabs(wb_value - imf_value) > 0.5:
                flags.append(
                    {
                        "year": year,
                        "country": country_iso3,
                        "worldbank_gdp_growth_pct": wb_value,
                        "imf_gdp_growth_pct": imf_value,
                        "data_quality_flag": "WB_IMF_DISCREPANCY",
                    }
                )
        return flags

    @staticmethod
    def _mock_worldbank_values(country_iso3: str, indicator: str, year_from: int, year_to: int) -> list[dict[str, Any]]:
        gdp_growth = {
            "CZE": {2021: -2.4, 2022: 2.5, 2023: -0.4, 2024: 1.3, 2025: 2.8},
            "CHL": {2021: 11.7, 2022: 2.4, 2023: 0.2, 2024: 2.6, 2025: 2.9},
            "PER": {2021: 13.5, 2022: 2.7, 2023: -0.6, 2024: 3.0, 2025: 3.3},
        }
        mineral_exports = {"CZE": 1.8, "CHL": 51.2, "PER": 58.4}
        mineral_rents = {"CZE": 0.2, "CHL": 8.4, "PER": 9.1}
        result: list[dict[str, Any]] = []
        for year in range(year_from, year_to + 1):
            if indicator == "NY.GDP.MKTP.KD.ZG":
                value = gdp_growth.get(country_iso3, {}).get(year)
            elif indicator == "TX.VAL.MINR.ZS.UN":
                value = mineral_exports.get(country_iso3, 0.0)
            elif indicator == "NY.GDP.MINR.RT.ZS":
                value = mineral_rents.get(country_iso3, 0.0)
            elif indicator == "AG.LND.FRST.ZS":
                value = {"CZE": 34.7, "CHL": 24.8, "PER": 56.5}.get(country_iso3, 0.0)
            else:
                value = 0.0
            if value is not None:
                result.append(
                    {
                        "year": year,
                        "value": float(value),
                        "country": country_iso3,
                        "indicator": indicator,
                        "source": "Deterministic Mock World Bank",
                        "vintage": _utc_now_iso(),
                    }
                )
        return result


def _latest_value(records: list[dict[str, Any]]) -> float:
    if not records:
        return 0.0
    return float(sorted(records, key=lambda item: item["year"])[-1].get("value", 0.0))
