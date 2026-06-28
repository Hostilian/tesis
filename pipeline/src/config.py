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
"""Typed runtime configuration for the SBEI pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path


def _optional_path(env_name: str) -> Path | None:
    value = os.environ.get(env_name, "").strip()
    return Path(value) if value else None


@dataclass(frozen=True)
class PipelineConfig:
    """Environment-backed configuration with mock mode as a valid operating state."""

    gcp_project: str = field(default_factory=lambda: os.environ.get("GCP_PROJECT", ""))
    gee_service_account: str = field(default_factory=lambda: os.environ.get("GEE_SERVICE_ACCOUNT", ""))
    gee_key_file: Path | None = field(default_factory=lambda: _optional_path("GEE_KEY_FILE"))
    google_application_credentials: Path | None = field(
        default_factory=lambda: _optional_path("GOOGLE_APPLICATION_CREDENTIALS")
    )
    cdse_client_id: str = field(default_factory=lambda: os.environ.get("CDSE_CLIENT_ID", ""))
    cdse_client_secret: str = field(default_factory=lambda: os.environ.get("CDSE_CLIENT_SECRET", ""))
    cdse_username: str = field(default_factory=lambda: os.environ.get("CDSE_USERNAME", ""))
    nasa_earthdata_username: str = field(default_factory=lambda: os.environ.get("NASA_EARTHDATA_USERNAME", ""))
    nasa_earthdata_password: str = field(default_factory=lambda: os.environ.get("NASA_EARTHDATA_PASSWORD", ""))
    nasa_earthdata_token: str = field(default_factory=lambda: os.environ.get("NASA_EARTHDATA_TOKEN", ""))
    sentinelhub_client_id: str = field(default_factory=lambda: os.environ.get("SENTINELHUB_CLIENT_ID", ""))
    sentinelhub_client_secret: str = field(default_factory=lambda: os.environ.get("SENTINELHUB_CLIENT_SECRET", ""))
    sentinelhub_instance_id: str = field(default_factory=lambda: os.environ.get("SENTINELHUB_INSTANCE_ID", ""))
    comtrade_api_key: str = field(default_factory=lambda: os.environ.get("COMTRADE_API_KEY", ""))
    fred_api_key: str = field(default_factory=lambda: os.environ.get("FRED_API_KEY", ""))
    slack_webhook_url: str = field(default_factory=lambda: os.environ.get("SLACK_WEBHOOK_URL", ""))
    zenodo_access_token: str = field(default_factory=lambda: os.environ.get("ZENODO_ACCESS_TOKEN", ""))
    worldbank_cache_ttl_hours: int = 24
    cloud_cover_max_pct: float = 20.0
    isolation_forest_contamination: float = 0.1
    bootstrap_iterations: int = 50
    bootstrap_ci_level: float = 0.95
    output_dir: Path = Path("docs/data")
    mock_mode: bool = field(default_factory=lambda: os.environ.get("MOCK_MODE", "").lower() == "true")

    def gee_credentials_file(self) -> Path | None:
        """Return the preferred Earth Engine credential file path, if configured."""
        return self.gee_key_file or self.google_application_credentials

    def validate(self) -> list[str]:
        """Return warnings for unavailable live integrations while preserving mock-mode operation."""
        warnings: list[str] = []
        if self.mock_mode:
            warnings.append("MOCK_MODE=true - external providers will use deterministic offline data.")
        if not self.gcp_project:
            warnings.append("GCP_PROJECT not set - Google Earth Engine will use mock mode.")
        if not self.cdse_client_id or not self.cdse_client_secret:
            warnings.append("CDSE OAuth credentials not set - Copernicus STAC will use mock mode.")
        if not self.nasa_earthdata_token and not (
            self.nasa_earthdata_username and self.nasa_earthdata_password
        ):
            warnings.append("NASA EarthData credentials not set - CMR requests will use mock mode.")
        if not self.sentinelhub_client_id or not self.sentinelhub_client_secret:
            warnings.append("Sentinel Hub credentials not set - evalscript rendering will use mock mode.")
        return warnings
