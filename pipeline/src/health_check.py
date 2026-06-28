"""
API Connection Health Check Module
====================================
Verifies connectivity and authentication status for satellite and economic data
providers. Outputs a structured JSON health report used by CI/CD workflows.

Usage:
    python pipeline/src/health_check.py --provider all
    python pipeline/src/health_check.py --provider gee
    python pipeline/src/health_check.py --provider cdse

Exit codes:
    0 - all checked providers healthy or intentionally skipped
    1 - one or more providers degraded or unavailable
    2 - authentication failure (secret missing or expired)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import requests

try:
    import ee  # type: ignore
    EE_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    EE_AVAILABLE = False
    ee = None  # type: ignore[assignment]


@dataclass
class HealthResult:
    provider: str
    status: str
    latency_ms: float
    http_status: Optional[int]
    error: Optional[str]
    checked_at: str
    endpoint: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _result(provider: str, status: str, latency_ms: float, http_status: Optional[int], error: Optional[str], endpoint: str) -> HealthResult:
    return HealthResult(
        provider=provider,
        status=status,
        latency_ms=round(latency_ms, 2),
        http_status=http_status,
        error=error,
        checked_at=_now_iso(),
        endpoint=endpoint,
    )


def check_worldbank() -> HealthResult:
    endpoint = "https://api.worldbank.org/v2/country/CZE/indicator/NY.GDP.MKTP.KD.ZG?format=json&per_page=1"
    start = time.perf_counter()
    try:
        response = requests.get(endpoint, timeout=20)
        latency_ms = (time.perf_counter() - start) * 1000
        if response.ok:
            return _result("worldbank", "ok", latency_ms, response.status_code, None, endpoint)
        return _result("worldbank", "unavailable", latency_ms, response.status_code, response.text[:200], endpoint)
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return _result("worldbank", "unavailable", latency_ms, None, str(exc), endpoint)


def check_gee() -> HealthResult:
    endpoint = "earthengine.googleapis.com"
    start = time.perf_counter()
    if not EE_AVAILABLE:
        latency_ms = (time.perf_counter() - start) * 1000
        return _result("gee", "unavailable", latency_ms, None, "earthengine-api not installed", endpoint)

    project = os.getenv("GCP_PROJECT")
    key_file = os.getenv("GEE_KEY_FILE") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    try:
        if key_file and Path(key_file).exists():
            ee.Initialize(project=project)
        else:
            ee.Initialize(project=project)
        collection_size = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").limit(1).size().getInfo()
        latency_ms = (time.perf_counter() - start) * 1000
        if collection_size >= 0:
            return _result("gee", "ok", latency_ms, 200, None, endpoint)
        return _result("gee", "unavailable", latency_ms, None, "Empty response from Earth Engine", endpoint)
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return _result("gee", "auth_failed", latency_ms, None, str(exc), endpoint)


def check_cdse() -> HealthResult:
    endpoint = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    start = time.perf_counter()
    client_id = os.getenv("CDSE_CLIENT_ID")
    client_secret = os.getenv("CDSE_CLIENT_SECRET")
    if not client_id or not client_secret:
        latency_ms = (time.perf_counter() - start) * 1000
        return _result("cdse", "auth_failed", latency_ms, None, "CDSE_CLIENT_ID or CDSE_CLIENT_SECRET missing", endpoint)

    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    try:
        response = requests.post(endpoint, data=payload, timeout=20)
        latency_ms = (time.perf_counter() - start) * 1000
        if response.ok and response.json().get("access_token"):
            return _result("cdse", "ok", latency_ms, response.status_code, None, endpoint)
        return _result("cdse", "auth_failed", latency_ms, response.status_code, response.text[:200], endpoint)
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return _result("cdse", "unavailable", latency_ms, None, str(exc), endpoint)


def check_nasa_earthdata() -> HealthResult:
    endpoint = "https://cmr.earthdata.nasa.gov/search/granules.json?short_name=VNP46A3&page_size=1"
    start = time.perf_counter()
    token = os.getenv("NASA_EARTHDATA_TOKEN")
    username = os.getenv("NASA_EARTHDATA_USERNAME")
    password = os.getenv("NASA_EARTHDATA_PASSWORD")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    auth = None if token else (username, password) if username and password else None
    if not headers and auth is None:
        latency_ms = (time.perf_counter() - start) * 1000
        return _result("nasa", "auth_failed", latency_ms, None, "NASA_EARTHDATA_TOKEN or username/password missing", endpoint)

    try:
        response = requests.get(endpoint, headers=headers, auth=auth, timeout=20)
        latency_ms = (time.perf_counter() - start) * 1000
        if response.ok:
            return _result("nasa", "ok", latency_ms, response.status_code, None, endpoint)
        return _result("nasa", "unavailable", latency_ms, response.status_code, response.text[:200], endpoint)
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return _result("nasa", "unavailable", latency_ms, None, str(exc), endpoint)


def check_imf() -> HealthResult:
    endpoint = "https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH/CZ/2024"
    start = time.perf_counter()
    try:
        response = requests.get(endpoint, timeout=20)
        latency_ms = (time.perf_counter() - start) * 1000
        if response.ok:
            return _result("imf", "ok", latency_ms, response.status_code, None, endpoint)
        return _result("imf", "unavailable", latency_ms, response.status_code, response.text[:200], endpoint)
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return _result("imf", "unavailable", latency_ms, None, str(exc), endpoint)


def check_comtrade() -> HealthResult:
    endpoint = "https://comtradeapi.un.org/data/v1/get/C/A/2526"
    start = time.perf_counter()
    api_key = os.getenv("COMTRADE_API_KEY")
    if not api_key:
        latency_ms = (time.perf_counter() - start) * 1000
        return _result("comtrade", "auth_failed", latency_ms, None, "COMTRADE_API_KEY missing", endpoint)

    try:
        response = requests.get(endpoint, headers={"Ocp-Apim-Subscription-Key": api_key}, timeout=20)
        latency_ms = (time.perf_counter() - start) * 1000
        if response.ok:
            return _result("comtrade", "ok", latency_ms, response.status_code, None, endpoint)
        return _result("comtrade", "unavailable", latency_ms, response.status_code, response.text[:200], endpoint)
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return _result("comtrade", "unavailable", latency_ms, None, str(exc), endpoint)


def check_fred() -> HealthResult:
    endpoint = "https://fred.stlouisfed.org/graph/fredgraph.json?id=GOLDAMGBD228NLBM"
    start = time.perf_counter()
    try:
        response = requests.get(endpoint, timeout=20)
        latency_ms = (time.perf_counter() - start) * 1000
        if response.ok:
            return _result("fred", "ok", latency_ms, response.status_code, None, endpoint)
        return _result("fred", "unavailable", latency_ms, response.status_code, response.text[:200], endpoint)
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return _result("fred", "unavailable", latency_ms, None, str(exc), endpoint)


def _providers() -> dict[str, Callable[[], HealthResult]]:
    return {
        "gee": check_gee,
        "cdse": check_cdse,
        "nasa": check_nasa_earthdata,
        "worldbank": check_worldbank,
        "imf": check_imf,
        "comtrade": check_comtrade,
        "fred": check_fred,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="API health checker")
    parser.add_argument("--provider", default="all", choices=["all", "gee", "cdse", "nasa", "worldbank", "imf", "comtrade", "fred"])
    parser.add_argument("--output", default="health_report.json")
    args = parser.parse_args()

    providers = _providers()
    selected = list(providers.keys()) if args.provider == "all" else [args.provider]
    results = [providers[name]() for name in selected]

    report = {
        "checked_at": _now_iso(),
        "results": [asdict(result) for result in results],
    }
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    if any(result.status == "auth_failed" for result in results):
        return 2
    if any(result.status not in {"ok", "skipped"} for result in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
